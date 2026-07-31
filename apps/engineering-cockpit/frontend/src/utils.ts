import { AxiosError } from "axios"

function extractErrorMessage(err: AxiosError<unknown>): string {
  if (err instanceof AxiosError) {
    const responseData = err.response?.data as
      | { detail?: string | Array<{ msg?: string }> }
      | undefined
    const errDetail = responseData?.detail

    if (Array.isArray(errDetail) && errDetail.length > 0) {
      return errDetail[0]?.msg || err.message
    }

    if (typeof errDetail === "string") {
      return errDetail
    }

    return err.message
  }

  const errDetail = (err as { detail?: string | Array<{ msg?: string }> })
    .detail
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    return errDetail[0]?.msg || "Something went wrong."
  }
  if (typeof errDetail === "string") {
    return errDetail
  }
  return "Something went wrong."
}

export const handleError = function (
  this: (msg: string) => void,
  err: AxiosError<unknown>,
) {
  const errorMessage = extractErrorMessage(err)
  this(errorMessage)
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}
