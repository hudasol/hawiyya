import { HashRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./Layout";
import { Check } from "./pages/Check";
import { NameLab } from "./pages/NameLab";
import { Overview } from "./pages/Overview";

// Screens present in this build. The remaining screens arrive in later phases.
const AVAILABLE = new Set(["overview", "check", "names"]);

export function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<Layout available={AVAILABLE} />}>
          <Route index element={<Overview />} />
          <Route path="check" element={<Check />} />
          <Route path="names" element={<NameLab />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}
