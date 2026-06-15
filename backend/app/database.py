"""SQLite database layer — predictions storage."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime

from .config import DB_PATH

PREDICTIONS_COLUMNS = {
    "id",
    "city",
    "temperature",
    "humidity",
    "wind_speed",
    "precipitation",
    "prediction",
    "timestamp",
}


def init_db() -> None:
    """Create or migrate the predictions table to the required schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        _ensure_predictions_schema(conn)
        conn.commit()


def _ensure_predictions_schema(conn: sqlite3.Connection) -> None:
    """Create predictions table or migrate from legacy schema."""
    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'"
    ).fetchone()

    if not existing:
        conn.executescript(
            """
            CREATE TABLE predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                wind_speed REAL NOT NULL,
                precipitation REAL NOT NULL,
                prediction REAL NOT NULL,
                timestamp TEXT NOT NULL
            );
            """
        )
        return

    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(predictions)").fetchall()
    }
    if columns == PREDICTIONS_COLUMNS:
        return

    # Migrate legacy table to new column names
    conn.executescript(
        """
        ALTER TABLE predictions RENAME TO predictions_legacy;

        CREATE TABLE predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            wind_speed REAL NOT NULL,
            precipitation REAL NOT NULL,
            prediction REAL NOT NULL,
            timestamp TEXT NOT NULL
        );
        """
    )

    legacy_cols = {
        row[1]
        for row in conn.execute("PRAGMA table_info(predictions_legacy)").fetchall()
    }

    if "temperature" in legacy_cols:
        conn.execute(
            """
            INSERT INTO predictions (
                city, temperature, humidity, wind_speed,
                precipitation, prediction, timestamp
            )
            SELECT city, temperature, humidity, wind_speed,
                   precipitation, prediction, timestamp
            FROM predictions_legacy
            """
        )
    elif "t2m" in legacy_cols:
        conn.execute(
            """
            INSERT INTO predictions (
                city, temperature, humidity, wind_speed,
                precipitation, prediction, timestamp
            )
            SELECT city, t2m, rh2m, ws10m, prectotcorr,
                   predicted_irradiance, prediction_time
            FROM predictions_legacy
            """
        )

    conn.execute("DROP TABLE IF EXISTS predictions_legacy")


@contextmanager
def get_connection():
    """Context manager for SQLite connections with dict-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_predictions(city: str, records: list[dict]) -> int:
    """Insert prediction records. Returns number of rows saved."""
    rows = [
        (
            city.lower(),
            record["temperature"],
            record["humidity"],
            record["wind_speed"],
            record["precipitation"],
            record["prediction"],
            record["timestamp"],
        )
        for record in records
    ]

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO predictions (
                city, temperature, humidity, wind_speed,
                precipitation, prediction, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        return len(rows)


def get_prediction_history(city: str | None = None, limit: int = 100) -> list[dict]:
    """Retrieve prediction history, optionally filtered by city."""
    query = """
        SELECT id, city, temperature, humidity, wind_speed,
               precipitation, prediction, timestamp
        FROM predictions
    """
    params: list = []

    if city:
        query += " WHERE city = ?"
        params.append(city.lower())

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_latest_prediction(city: str | None = None) -> dict | None:
    """Return the most recent prediction row."""
    query = """
        SELECT id, city, temperature, humidity, wind_speed,
               precipitation, prediction, timestamp
        FROM predictions
    """
    params: list = []

    if city:
        query += " WHERE city = ?"
        params.append(city.lower())

    query += " ORDER BY timestamp DESC LIMIT 1"

    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def get_dashboard_stats(city: str | None = None) -> dict:
    """Aggregate stats for analytics sections on the dashboard."""
    params: list = []
    city_filter = ""
    if city:
        city_filter = " WHERE city = ?"
        params.append(city.lower())

    with get_connection() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM predictions{city_filter}", params
        ).fetchone()[0]

        city_counts = conn.execute(
            "SELECT city, COUNT(*) AS count FROM predictions GROUP BY city"
        ).fetchall()

        latest_rows = conn.execute(
            f"""
            SELECT city, timestamp, prediction, temperature, humidity
            FROM predictions{city_filter}
            ORDER BY timestamp DESC
            LIMIT 5
            """,
            params,
        ).fetchall()

        avg_by_city = conn.execute(
            """
            SELECT city, AVG(prediction) AS avg_prediction
            FROM predictions
            GROUP BY city
            """
        ).fetchall()

    return {
        "total_predictions": total,
        "predictions_by_city": {row["city"]: row["count"] for row in city_counts},
        "latest_predictions": [dict(row) for row in latest_rows],
        "average_prediction_by_city": {
            row["city"]: round(row["avg_prediction"], 2) for row in avg_by_city
        },
    }
