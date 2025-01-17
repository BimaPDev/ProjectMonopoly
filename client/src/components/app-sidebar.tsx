import * as React from "react";
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
import { RadiobuttonIcon } from "@radix-ui/react-icons";

const data = {
  user: {
    name: "Testing User",
    email: "Testing@Testing.co",
    avatar: "/placeholder.svg?height=32&width=32",
  },
  teams: [
    {
      name: "DoogWood Gaming",
      logo: GalleryHorizontalEnd,
      plan: "Enterprise",
    },
  ],
  navMain: [
    {
      title: "Dashboard",
      url: "/",
      icon: Home,
      isActive: true,
    },
    {
      title: "DogWood AI",
      url: "/Ai",
      icon: BotIcon,
    },

    {
      title: "Content",
      url: "#",
      icon: MessageCircle,
      items: [
        {
          title: "Posts",
          url: "/posts",
        },
        {
          title: "Scheduler",
          url: "#",
        },
        {
          title: "Media Library",
          url: "#",
        },
      ],
    },
    {
      title: "Analytics",
      url: "#",
      icon: TrendingUp,
      items: [
        {
          title: "Overview",
          url: "#",
        },
        {
          title: "Engagement",
          url: "#",
        },
        {
          title: "Audience",
          url: "#",
        },
      ],
    },

    {
      title: "Campaigns",
      url: "#",
      icon: Share2,
      items: [
        {
          title: "Active",
          url: "#",
        },
        {
          title: "Drafts",
          url: "#",
        },
        {
          title: "Archive",
          url: "#",
        },
      ],
    },
    {
      title: "Calendar",
      url: "#",
      icon: Calendar,
    },
    {
      title: "Hashtags",
      url: "#",
      icon: Hash,
    },
    {
      title: "Competitors",
      url: "/competitors",
      icon: Users2,
    },
    {
      title: "Reports",
      url: "#",
      icon: BarChart3,
    },
    {
      title: "Settings",
      url: "#",
      icon: Settings2,
    },
    
  ],
  projects: [
    {
      name: "Summer Campaign",
      url: "#",
      icon: Share2,
    },
    {
      name: "Product Launch",
      url: "#",
      icon: Share2,
    },
    {
      name: "Holiday Season",
      url: "#",
      icon: Share2,
    },
  ],
};



export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavProjects projects={data.projects} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
