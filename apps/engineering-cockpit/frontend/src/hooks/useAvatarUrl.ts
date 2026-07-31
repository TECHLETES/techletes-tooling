import { useEffect, useState } from "react"

const AVATAR_QUERY_KEY = "current-user-avatar"

export function useAvatarUrl(avatarUrl?: string) {
  const [objectUrl, setObjectUrl] = useState<string>()

  useEffect(() => {
    if (!avatarUrl) {
      setObjectUrl(undefined)
      return
    }

    const controller = new AbortController()
    let nextObjectUrl: string | undefined

    const loadAvatar = async () => {
      const response = await fetch(avatarUrl, {
        signal: controller.signal,
        credentials: "include",
        headers: {
          "X-Avatar-Query": AVATAR_QUERY_KEY,
        },
      })

      if (!response.ok) {
        setObjectUrl(undefined)
        return
      }

      const blob = await response.blob()
      nextObjectUrl = URL.createObjectURL(blob)
      setObjectUrl(nextObjectUrl)
    }

    void loadAvatar()

    return () => {
      controller.abort()
      if (nextObjectUrl) {
        URL.revokeObjectURL(nextObjectUrl)
      }
    }
  }, [avatarUrl])

  return objectUrl
}
