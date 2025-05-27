// components/AppSidebar.tsx
import * as React from "react"
import { usePathname } from "next/navigation"
import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarRail } from "@/components/ui/sidebar"
import { NavMain } from "./nav-main"
import { NavUser } from "./nav-user"
import { TeamSwitcher } from "./team-switcher"
import { GalleryHorizontalEnd, Home, BotIcon, MessageCircle, Users2 } from "lucide-react"

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname()

  const teams = [
    { name: "DoogWood Gaming", logo: GalleryHorizontalEnd, plan: "Enterprise" },
  ]

  // Build your nav items and mark the active one
  const navMainItems = [
    { title: "Dashboard",    url: "/dashboard",             icon: Home    },
    { title: "DogWood AI",    url: "/dashboard/ai",          icon: BotIcon },
    { title: "Posts",         url: "/dashboard/posts",       icon: MessageCircle },
    { title: "Competitors",   url: "/dashboard/competitors", icon: Users2 },
  ].map(item => ({
    ...item,
    isActive: pathname === item.url,
    
  }))
  
  const [userData, setUserData] = React.useState({
    name: "",
    email: "",
    avatar: "/placeholder.svg?height=32&width=32",
  })
  React.useEffect(() => {
    setUserData({
      name: localStorage.getItem("username") || "",
      email: localStorage.getItem("email") || "",
      avatar: "/placeholder.svg?height=32&width=32",
    })
  }, [])

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navMainItems} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={userData} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}

export default AppSidebar
