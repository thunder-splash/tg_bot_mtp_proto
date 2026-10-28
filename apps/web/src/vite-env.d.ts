/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BOT_USERNAME: string;
  readonly VITE_PRICE_1M: string;
  readonly VITE_PRICE_3M: string;
  readonly VITE_PRICE_12M: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
