import { ChevronDown, Languages } from "lucide-react"
import { useTranslation } from "react-i18next"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const AVAILABLE_LANGUAGES = [{ code: "en" }, { code: "nl" }] as const

type SupportedLanguage = (typeof AVAILABLE_LANGUAGES)[number]["code"]

function getLanguageCode(value: string | undefined): SupportedLanguage {
  const normalizedValue = value?.split("-")[0]

  return normalizedValue === "nl" ? "nl" : "en"
}

function getLanguageLabel(
  language: SupportedLanguage,
  t: (key: "language.dutch" | "language.english") => string,
) {
  return language === "nl" ? t("language.dutch") : t("language.english")
}

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation()
  const currentLanguage = getLanguageCode(
    i18n.resolvedLanguage ?? i18n.language,
  )
  const selectedLanguage =
    AVAILABLE_LANGUAGES.find((language) => language.code === currentLanguage) ??
    AVAILABLE_LANGUAGES[0]

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="min-w-36 justify-between gap-3"
          data-testid="language-button"
        >
          <span className="flex items-center gap-2">
            <Languages className="size-4" />
            <span>{getLanguageLabel(selectedLanguage.code, t)}</span>
          </span>
          <ChevronDown className="size-4 text-muted-foreground" />
          <span className="sr-only">{t("language.toggleLanguage")}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-44">
        <DropdownMenuLabel>{t("language.title")}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuRadioGroup
          value={currentLanguage}
          onValueChange={(value) => {
            void i18n.changeLanguage(value)
          }}
        >
          {AVAILABLE_LANGUAGES.map((language) => (
            <DropdownMenuRadioItem key={language.code} value={language.code}>
              {getLanguageLabel(language.code, t)}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default LanguageSwitcher
