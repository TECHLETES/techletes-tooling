import { defineConfig } from "i18next-cli"

export default defineConfig({
  locales: ["en", "nl"],
  extract: {
    input: ["src/**/*.{ts,tsx}"],
    output: "src/locales/{{language}}/{{namespace}}.json",
    defaultNS: "translation",
    keySeparator: ".",
    sort: true,
    indentation: 2,
    primaryLanguage: "nl",
    defaultValue: "",
    useTranslationNames: ["useTranslation"],
  },
  types: {
    input: ["src/locales/nl/**/*.json"],
    basePath: "src/locales/nl",
    output: "src/@types/i18next.d.ts",
    resourcesFile: "src/@types/i18next-resources.d.ts",
  },
})
