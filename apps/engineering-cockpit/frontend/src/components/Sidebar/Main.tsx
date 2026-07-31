import { Link as RouterLink, useRouterState } from "@tanstack/react-router"
import type { LucideIcon } from "lucide-react"

import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  useSidebar,
} from "@/components/ui/sidebar"

export type Item = {
  icon: LucideIcon
  title: string
  path: string
  permission?: string
  children?: Item[]
}

interface MainProps {
  items: Item[]
}

export function Main({ items }: MainProps) {
  const { isMobile, setOpenMobile } = useSidebar()
  const router = useRouterState()
  const currentPath = router.location.pathname

  const isItemActive = (item: Item): boolean =>
    currentPath === item.path || currentPath.startsWith(`${item.path}/`)

  const handleMenuClick = () => {
    if (isMobile) {
      setOpenMobile(false)
    }
  }

  return (
    <SidebarMenu>
      {items.map((item) => {
        const isActive = isItemActive(item)
        const visibleChildren = item.children

        return (
          <SidebarMenuItem key={item.title}>
            <SidebarMenuButton tooltip={item.title} isActive={isActive} asChild>
              <RouterLink to={item.path} onClick={handleMenuClick}>
                <item.icon />
                <span>{item.title}</span>
              </RouterLink>
            </SidebarMenuButton>
            {isActive && visibleChildren && visibleChildren.length > 0 && (
              <SidebarMenuSub>
                {visibleChildren.map((child) => {
                  const isChildActive = isItemActive(child)

                  return (
                    <SidebarMenuSubItem key={child.title}>
                      <SidebarMenuSubButton isActive={isChildActive} asChild>
                        <RouterLink to={child.path} onClick={handleMenuClick}>
                          <child.icon />
                          <span>{child.title}</span>
                        </RouterLink>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                  )
                })}
              </SidebarMenuSub>
            )}
          </SidebarMenuItem>
        )
      })}
    </SidebarMenu>
  )
}
