import * as React from "react";
import { useState, useEffect } from "react";
import {
  BarChart3,
  BotIcon,
  Calendar,
  GalleryHorizontalEnd,
  Hash,
  Home,
  MessageCircle,
  Settings2,
  Share2,
  TrendingUp,
  Users2,
} from "lucide-react";

import { NavMain } from "./nav-main";
import { NavProjects } from "./nav-projects";
import { NavUser } from "./nav-user";
import { TeamSwitcher } from "./team-switcher";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
 
  const [userData, setUserData] = useState({
    name: "",
    email: "",
    avatar: "/placeholder.svg?height=32&width=32",
  });

  useEffect(() => {
    // Only access localStorage after component mounts (client-side)
    setUserData({
      name: localStorage.getItem("username") || "",
      email: localStorage.getItem("email") || "",
      avatar: "/placeholder.svg?height=32&width=32",
    });
  }, []);

  const teams = [
    {
      name: "DoogWood Gaming",
      logo: GalleryHorizontalEnd,
      plan: "Enterprise",
    },
  ];

  const navMain = [
    {
      title: "Dashboard",
      url: "/dashboard",
      icon: Home,
      isActive: true,
    },
    {
      title: "DogWood AI",
      url: "/dashboard/ai",
      icon: BotIcon,
    },
    {
      title: "Content",
      url: "#",
      icon: MessageCircle,
      items: [
        {
          title: "Posts",
          url: "/dashboard/posts",
        },
      ],
    },
    {
      title: "Competitors",
      url: "/dashboard/competitors",
      icon: Users2,
    },
  ];

  const projects = [];
  
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navMain} />
        <NavProjects projects={projects} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={userData} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
export default AppSidebar;