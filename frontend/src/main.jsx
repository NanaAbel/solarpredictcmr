/**
 * Application entry point.
 * Mounts the React app inside BrowserRouter for client-side routing.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles/index.css";

// Render the root component into the #root div from index.html
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {/* BrowserRouter enables clean client-side URLs for each page. */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
