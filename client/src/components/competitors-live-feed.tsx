"use client";

import * as React from "react";
import {
  ArrowLeft,
  Instagram,
  Linkedin,
  MoreHorizontal,
  Twitter,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Sample data for the live feed
const livePosts = [
  {
    id: 1,
    competitor: {
      name: "Test",
      logo: "/placeholder.svg?height=40&width=40",
    },
    platform: "instagram",
    content:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. 🚀 #TechInnovation #ComingSoon",
    media: "/placeholder.svg?height=600&width=600",
    postedAt: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
    likes: 1234,
    comments: 89,
  },
  {
    id: 2,
    competitor: {
      name: "Test",
      logo: "/placeholder.svg?height=40&width=40",
    },
    platform: "twitter",
    content:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. 🤝",
    media: "/placeholder.svg?height=800&width=600",
    postedAt: new Date(Date.now() - 1000 * 60 * 45), // 45 minutes ago
    likes: 892,
    comments: 56,
  },
  {
    id: 3,
    competitor: {
      name: "Test",
      logo: "/placeholder.svg?height=40&width=40",
    },
    platform: "linkedin",
    content:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
    media: "/placeholder.svg?height=400&width=600",
    postedAt: new Date(Date.now() - 1000 * 60 * 60), // 1 hour ago
    likes: 445,
    comments: 32,
  },
  {
    id: 4,
    competitor: {
      name: "TestTest",
      logo: "/placeholder.svg?height=40&width=40",
    },
    platform: "instagram",
    content:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. ✨ #DesignThinking #Innovation",
    media: "/placeholder.svg?height=600&width=400",
    postedAt: new Date(Date.now() - 1000 * 60 * 90), // 1.5 hours ago
    likes: 2103,
    comments: 167,
  },
  {
    id: 5,
    competitor: {
      name: "Test",
      logo: "/placeholder.svg?height=40&width=40",
    },
    platform: "linkedin",
    content:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
    media: "/placeholder.svg?height=500&width=600",
    postedAt: new Date(Date.now() - 1000 * 60 * 120), // 2 hours ago
    likes: 1567,
    comments: 89,
  },
];

const platformIcons = {
  instagram: Instagram,
  twitter: Twitter,
  linkedin: Linkedin,
};

const platformColors = {
  instagram: "text-pink-500",
  twitter: "text-sky-500",
  linkedin: "text-blue-700",
};

export function CompetitorsLiveFeed() {
  return (
    <div className="flex-1 space-y-4 p-4 pt-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="mr-2" asChild>
            <a href="/competitors">
              <ArrowLeft className="h-4 w-4" />
            </a>
          </Button>
          <h2 className="text-3xl font-bold tracking-tight">Live Feed</h2>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {livePosts.map((post) => {
          const PlatformIcon =
            platformIcons[post.platform as keyof typeof platformIcons];
          const platformColor =
            platformColors[post.platform as keyof typeof platformColors];

          return (
            <Card key={post.id} className="overflow-hidden">
              <CardHeader className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Avatar className="h-8 w-8">
                      <AvatarImage
                        src={post.competitor.logo}
                        alt={post.competitor.name}
                      />
                      <AvatarFallback>
                        {post.competitor.name.slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">
                        {post.competitor.name}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatDistanceToNow(post.postedAt, {
                          addSuffix: true,
                        })}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <PlatformIcon className={`h-4 w-4 ${platformColor}`} />
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                          <span className="sr-only">More options</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>View Original</DropdownMenuItem>
                        <DropdownMenuItem>Copy Link</DropdownMenuItem>
                        <DropdownMenuItem>Share</DropdownMenuItem>
                        <DropdownMenuItem>Save</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="relative aspect-square">
                  <img
                    src={post.media}
                    alt="Post media"
                    className="object-cover w-full h-full"
                  />
                </div>
                <div className="p-4">
                  <p className="text-sm">{post.content}</p>
                  <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                    <span>{post.likes.toLocaleString()} likes</span>
                    <span>{post.comments.toLocaleString()} comments</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
