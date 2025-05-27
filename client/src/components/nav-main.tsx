// components/nav-main.tsx
import * as React from "react"
import { usePathname } from "next/navigation"
import { ChevronRight, LucideIcon } from "lucide-react"

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar"

interface NavMainProps {
  items: {
    title: string
    url: string
    icon?: LucideIcon
    items?: { title: string; url: string }[]
  }[]
}

export function NavMain({ items }: NavMainProps) {
  const pathname = usePathname()

  return (
    <SidebarGroup>
      <SidebarGroupLabel>Navigation</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => {
          // is this item (or one of its subs) active?
          const isParentActive =
            pathname === item.url ||
            !!item.items?.find((sub) => pathname === sub.url)

          // leaf node
          if (!item.items?.length) {
            return (
              <SidebarMenuItem key={item.url}>
                <SidebarMenuButton
                  asChild
                  isActive={pathname === item.url}
                  tooltip={item.title}
                >
                  <a href={item.url} className="flex items-center space-x-2">
                    {item.icon && <item.icon className="w-4 h-4" />}
                    <span>{item.title}</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          }

          // has sub-menu
          return (
            <Collapsible
              key={item.url}
              asChild
              defaultOpen={isParentActive}
              className="group/collapsible"
            >
              <SidebarMenuItem>
                <CollapsibleTrigger asChild>
                  <SidebarMenuButton
                    isActive={isParentActive}
                    tooltip={item.title}
                    className="flex items-center space-x-2"
                  >
                    {item.icon && <item.icon className="w-4 h-4" />}
                    <span>{item.title}</span>
                    <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                  </SidebarMenuButton>
                </CollapsibleTrigger>

                <CollapsibleContent>
                  <SidebarMenuSub>
                    {item.items.map((sub) => (
                      <SidebarMenuSubItem key={sub.url}>
                        <SidebarMenuSubButton
                          asChild
                          isActive={pathname === sub.url}
                        >
                          <a className="pl-8 block" href={sub.url}>
                            {sub.title}
                          </a>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    ))}
                  </SidebarMenuSub>
                </CollapsibleContent>
              </SidebarMenuItem>
            </Collapsible>
          )
        })}
      </SidebarMenu>
    </SidebarGroup>
  )
}
