/**
 * Root application component.
 * Defines all page routes wrapped in the shared Layout (sidebar + content area).
 */
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Prediction from "./pages/Prediction";
import History from "./pages/History";
import Microgrid from "./pages/Microgrid";
import About from "./pages/About";

export default function App() {
  return (
    <Routes>
      {/* Layout provides sidebar navigation; child routes render in <Outlet /> */}
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="prediction" element={<Prediction />} />
        <Route path="history" element={<History />} />
        <Route path="microgrid" element={<Microgrid />} />
        <Route path="about" element={<About />} />
      </Route>
    </Routes>
  );
}
