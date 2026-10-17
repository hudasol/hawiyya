import "@fontsource/space-grotesk/500.css";
import "@fontsource/space-grotesk/700.css";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans-arabic/400.css";
import "@fontsource/ibm-plex-sans-arabic/600.css";
import "@fontsource/ibm-plex-mono/400.css";
import "./theme/global.css";
import "./i18n";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { PrefsProvider } from "./prefs";
import { applyTheme } from "./theme/tokens";

applyTheme("light");
const client = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 60_000 } } });

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <QueryClientProvider client={client}>
        <PrefsProvider>
          <App />
        </PrefsProvider>
      </QueryClientProvider>
    </StrictMode>,
  );
}
