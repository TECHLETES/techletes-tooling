/// <reference types="vite/client" />

interface Window {
  __APP_CONFIG__?: {
    apiUrl?: string
  }
}

interface ImportMetaEnv {
  readonly VITE_APP_BUILD_ID?: string
}
