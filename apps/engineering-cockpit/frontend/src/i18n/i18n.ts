import i18n from "i18next"
import LanguageDetector from "i18next-browser-languagedetector"
import { initReactI18next } from "react-i18next"
import enTranslation from "@/locales/en/translation.json"
import nlTranslation from "@/locales/nl/translation.json"

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        translation: enTranslation,
      },
      nl: {
        translation: nlTranslation,
      },
    },
    fallbackLng: "en",
    supportedLngs: ["en", "nl"],
    defaultNS: "translation",
    interpolation: {
      escapeValue: false,
    },
  })

export default i18n
