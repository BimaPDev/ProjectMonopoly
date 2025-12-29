// components/AppSidebar.tsx
import * as React from "react"
import { useLocation } from "react-router-dom"
import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarRail } from "@/components/ui/sidebar"
import { NavMain } from "./nav-main"
import { NavUser } from "./nav-user"
import { TeamSwitcher } from "./team-switcher"
import { Home, BotIcon, MessageCircle, Users2 } from "lucide-react"

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation()
  const pathname = location.pathname

  // Build your nav items and mark the active one
  const navMainItems = [
    { title: "Dashboard", url: "/dashboard", icon: Home },
    {
      title: "Media Workshop",
      url: "/dashboard/ai",
      icon: BotIcon,
      items: [
        { title: "AI Assistant", url: "/dashboard/ai" },
        { title: "Campaigns", url: "/dashboard/campaigns" },
        { title: "Game Context", url: "/dashboard/gamecontext" },
        { title: "Marketing Generator", url: "/dashboard/marketing" }
      ]
    },
    { title: "Posts", url: "/dashboard/posts", icon: MessageCircle },
    { title: "Competitors", url: "/dashboard/competitors", icon: Users2 },
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
        <TeamSwitcher />
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
