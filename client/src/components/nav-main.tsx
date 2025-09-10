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
    isActive?: boolean
    items?: { title: string; url: string }[]
  }[]
}

export function NavMain({ items }: NavMainProps) {
  const pathname = usePathname()

  const isItemActive = (item: NavMainProps['items'][0]) => {
    return item.isActive ?? (pathname === item.url)
  }

  const isParentActive = (item: NavMainProps['items'][0]) => {
    if (!item.items?.length) return isItemActive(item)
    return isItemActive(item) || item.items.some(sub => pathname === sub.url)
  }

  const renderLeafItem = (item: NavMainProps['items'][0]) => (
    <SidebarMenuItem key={item.url}>
      <SidebarMenuButton
        asChild
        isActive={isItemActive(item)}
        tooltip={item.title}
      >
        <a 
          href={item.url} 
          className="group flex items-center gap-3 rounded-lg px-3 py-2 transition-all duration-200 hover:scale-[1.02] hover:shadow-sm"
        >
          {item.icon && (
            <item.icon className="h-4 w-4 transition-colors duration-200 group-hover:scale-110" />
          )}
          <span className="font-medium">{item.title}</span>
        </a>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )

  const renderCollapsibleItem = (item: NavMainProps['items'][0]) => (
    <Collapsible
      key={item.url}
      asChild
      defaultOpen={isParentActive(item)}
      className="group/collapsible"
    >
      <SidebarMenuItem>
        <CollapsibleTrigger asChild>
          <SidebarMenuButton
            isActive={isParentActive(item)}
            tooltip={item.title}
            className="group flex w-full items-center gap-3 rounded-lg px-3 py-2 transition-all duration-200 hover:scale-[1.02] hover:shadow-sm"
          >
            {item.icon && (
              <item.icon className="h-4 w-4 transition-all duration-200 group-hover:scale-110" />
            )}
            <span className="flex-1 font-medium text-left">{item.title}</span>
            <ChevronRight className="h-4 w-4 shrink-0 transition-all duration-300 ease-out group-data-[state=open]/collapsible:rotate-90 group-hover:scale-110" />
          </SidebarMenuButton>
        </CollapsibleTrigger>

        <CollapsibleContent className="overflow-hidden transition-all duration-300 ease-out data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down">
          <SidebarMenuSub className="border-l-2 border-border/20 ml-2 pl-0">
            {item.items?.map((sub) => (
              <SidebarMenuSubItem key={sub.url}>
                <SidebarMenuSubButton
                  asChild
                  isActive={pathname === sub.url}
                >
                  <a 
                    className="group flex items-center rounded-lg py-2 pl-8 pr-3 transition-all duration-200 hover:translate-x-1 hover:shadow-sm" 
                    href={sub.url}
                  >
                    <span className="relative">
                      <span className="absolute -left-6 top-1/2 h-px w-4 bg-border/40 transition-all duration-200 group-hover:w-5 group-hover:bg-border/60"></span>
                      {sub.title}
                    </span>
                  </a>
                </SidebarMenuSubButton>
              </SidebarMenuSubItem>
            ))}
          </SidebarMenuSub>
        </CollapsibleContent>
      </SidebarMenuItem>
    </Collapsible>
  )

  return (
    <SidebarGroup className="space-y-2">
      <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
        Navigation
      </SidebarGroupLabel>
      <SidebarMenu className="space-y-1">
        {items.map((item) => (
          item.items?.length 
            ? renderCollapsibleItem(item)
            : renderLeafItem(item)
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
}