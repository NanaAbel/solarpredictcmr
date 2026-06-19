/**
 * Main layout shell with sidebar navigation.
 * Wraps all pages and renders the active route via <Outlet />.
 */
import { NavLink, Outlet } from "react-router-dom";

// Sidebar navigation items — path, label, and display icon
const navItems = [
  { to: "/", label: "Dashboard", icon: "◉" },
  { to: "/prediction", label: "Prediction", icon: "☀" },
  { to: "/history", label: "History", icon: "⌚" },
  { to: "/microgrid", label: "Microgrid", icon: "⚡" },
  { to: "/about", label: "About", icon: "ℹ" },
];

export default function Layout() {
  return (
    <div className="app-shell">
      {/* Left sidebar — branding, nav links, footer */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">SP</div>
          <div>
            <h1>SolarPredict</h1>
            <p>Forecasting & Microgrid</p>
          </div>
        </div>

        <nav className="sidebar-nav">
          {/* NavLink automatically exposes active state for styling. */}
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `nav-link${isActive ? " active" : ""}`
              }
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <p>Final Year Project</p>
          <span>Cameroon Solar Energy</span>
        </div>
      </aside>

      {/* Right content area — active page renders here */}
      <main className="main-content">
        {/* Outlet is replaced by Dashboard, Prediction, History, etc. */}
        <Outlet />
      </main>
    </div>
  );
}
