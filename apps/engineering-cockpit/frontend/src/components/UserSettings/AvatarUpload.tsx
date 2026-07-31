import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Camera, Trash2 } from "lucide-react"
import { useRef } from "react"
import { useTranslation } from "react-i18next"
import type { UserPublic } from "@/client"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import useAuth from "@/hooks/useAuth"
import { useAvatarUrl } from "@/hooks/useAvatarUrl"
import useCustomToast from "@/hooks/useCustomToast"
import { UsersService } from "@/services"

export function AvatarUpload() {
  const { t } = useTranslation()
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const avatarDownloadUrl = currentUser?.avatar_url
    ? UsersService.getCurrentUserAvatarDownloadUrl()
    : undefined
  const resolvedAvatarUrl = useAvatarUrl(avatarDownloadUrl)

  const uploadMutation = useMutation({
    mutationFn: (file: File) => UsersService.uploadAvatar(file),
    onSuccess: () => {
      showSuccessToast(t("settings.profile.avatar.success"))
      queryClient.invalidateQueries()
    },
    onError: (error: Error) => showErrorToast(error.message),
  })

  const deleteMutation = useMutation({
    mutationFn: () => UsersService.deleteAvatar(),
    onSuccess: () => {
      showSuccessToast(t("settings.profile.avatar.deleted"))
      queryClient.invalidateQueries()
    },
    onError: (error: Error) => showErrorToast(error.message),
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  const getInitials = (user: UserPublic) => {
    if (user.full_name) {
      return user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    }
    return user.email?.[0]?.toUpperCase() || "?"
  }

  return (
    <div className="flex flex-col items-center gap-4">
      <Avatar className="h-24 w-24">
        <AvatarImage
          src={resolvedAvatarUrl}
          alt={currentUser?.full_name || "Avatar"}
        />
        <AvatarFallback className="text-lg">
          {currentUser ? getInitials(currentUser as UserPublic) : "?"}
        </AvatarFallback>
      </Avatar>
      <div className="flex gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={handleFileChange}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadMutation.isPending || deleteMutation.isPending}
        >
          <Camera className="mr-2 h-4 w-4" />
          {resolvedAvatarUrl
            ? t("settings.profile.avatar.change")
            : t("settings.profile.avatar.upload")}
        </Button>
        {resolvedAvatarUrl && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => deleteMutation.mutate()}
            disabled={uploadMutation.isPending || deleteMutation.isPending}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            {t("settings.profile.avatar.remove")}
          </Button>
        )}
      </div>
    </div>
  )
}
