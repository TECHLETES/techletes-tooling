import { Appearance } from "@/components/Common/Appearance"
import { LanguageSwitcher } from "@/components/Common/LanguageSwitcher"
import { Logo } from "@/components/Common/Logo"
import { Card, CardContent } from "@/components/ui/card"
import { Footer } from "./Footer"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <div className="bg-secondary dark:bg-sidebar relative hidden lg:flex lg:items-center lg:justify-center">
        <Logo variant="full" className="h-16" asLink={false} />
      </div>
      <div className="flex flex-col gap-4 p-6 md:p-10">
        <div className="flex justify-end gap-2">
          <Appearance />
          <LanguageSwitcher />
        </div>
        <div className="flex flex-1 items-center justify-center">
          <Card className="w-full max-w-md">
            <CardContent className="py-6">{children}</CardContent>
          </Card>
        </div>
        <Footer />
      </div>
    </div>
  )
}
