import { useTranslation } from "react-i18next"
import { toast } from "sonner"

const useCustomToast = () => {
  const { t } = useTranslation()

  const showSuccessToast = (description: string) => {
    toast.success(t("toast.successTitle"), {
      description,
    })
  }

  const showErrorToast = (description: string) => {
    toast.error(t("toast.errorTitle"), {
      description,
    })
  }

  const showToast = (
    title: string,
    description: string,
    type: "success" | "error",
  ) => {
    if (type === "success") {
      toast.success(title, {
        description,
      })
    } else if (type === "error") {
      toast.error(title, {
        description,
      })
    }
  }

  return { showSuccessToast, showErrorToast, showToast }
}

export default useCustomToast
