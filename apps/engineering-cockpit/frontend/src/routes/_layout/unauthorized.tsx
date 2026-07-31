import { createFileRoute, Link } from "@tanstack/react-router"
import { Home, Lock, Shield } from "lucide-react"
import { useTranslation } from "react-i18next"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import useAuth from "@/hooks/useAuth"
import i18n from "@/i18n/i18n"

export const Route = createFileRoute("/_layout/unauthorized")({
  component: UnauthorizedPage,
  head: () => ({
    meta: [
      {
        title: `${i18n.t("unauthorized.metaTitle")} - Fullstack Template`,
      },
    ],
  }),
})

function UnauthorizedPage() {
  const { user, isSuperAdmin } = useAuth()
  const { t } = useTranslation()

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-background to-muted/50">
      <Card className="w-full max-w-md border-destructive/20">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="rounded-full bg-destructive/10 p-4">
              <Lock className="h-8 w-8 text-destructive" />
            </div>
          </div>
          <CardTitle className="text-2xl">{t("unauthorized.title")}</CardTitle>
          <CardDescription>{t("unauthorized.description")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>
              {user?.email ? (
                <>
                  {t("unauthorized.signedInAs")}{" "}
                  <span className="font-medium text-foreground">
                    {user.email}
                  </span>
                </>
              ) : (
                t("unauthorized.notSignedIn")
              )}
            </p>
            <p>{t("unauthorized.helpText")}</p>
          </div>

          {isSuperAdmin() && (
            <div className="rounded-md bg-info/10 border border-info/20 p-3">
              <div className="flex items-start gap-2">
                <Shield className="h-5 w-5 text-info mt-0.5 flex-shrink-0" />
                <p className="text-sm text-info">
                  {t("unauthorized.superAdminHint")}
                </p>
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <Button asChild variant="outline" className="flex-1">
              <Link to="/">
                <Home className="mr-2 h-4 w-4" />
                {t("unauthorized.backHome")}
              </Link>
            </Button>
            {isSuperAdmin() && (
              <Button asChild className="flex-1">
                <Link to="/admin">
                  <Shield className="mr-2 h-4 w-4" />
                  {t("unauthorized.adminPanel")}
                </Link>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
