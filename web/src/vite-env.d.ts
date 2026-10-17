/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_HAWIYYA_MODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
