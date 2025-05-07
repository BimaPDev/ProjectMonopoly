"use client";

import * as React from "react";
import { ChevronsUpDown, Plus, Users } from "lucide-react";
import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar";

// This is what we'll actually keep in React state:
interface Group {
  ID: number;
  Name: string;
  Description: string;
}

export function TeamSwitcher() {
  const [groups, setGroups] = React.useState<Group[]>([]);
  const [activeGroup, setActiveGroup] = React.useState<Group | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [userID, setUserID] = useState(0);
  

  React.useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    setUserID(Number(localStorage.getItem("userID")));
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `http://localhost:8080/api/groups?userID=${userID}`,
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        } 
      );
      const data = await res.json();
      if (!Array.isArray(data)) {
        console.error("Expected array response, got:", typeof data);
        throw new Error("Invalid response format from server");
      }
      
      setGroups(data);
     
      setActiveGroup(groups[0]);// Set the first group as active by default
      setLoading(false);
      
    } catch (e: any) {
      setError(e.message || "Error fetching groups");
    } 
  };

  const createGroup = async () => {
    const name = window.prompt("New group name:")?.trim();
    if (!name) return;
    const description = window.prompt("Description (optional):")?.trim() || "";
    try {
      const res = await fetch("http://localhost:8080/api/groups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: Number(userID), name, description }),
      });
      if (!res.ok) throw new Error((await res.text()) || "Create failed");
      await fetchGroups();
    } catch (e: any) {
      setError(e.message || "Error creating group");
    }
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton size="lg">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 text-zinc-50 dark:bg-zinc-50 dark:text-zinc-900">
                <Users className="h-4 w-4" />
              </div>
              <div className="flex-1 text-left text-sm leading-tight">
                <span className="font-semibold">
                  {loading
                    ? "Loading..."
                    : error
                    ? "Error"
                    : activeGroup
                    ? activeGroup.Name
                    : "No Groups"}
                </span>
                {activeGroup?.Description && (
                  <span className="block text-xs text-zinc-500 dark:text-zinc-400">
                    {activeGroup.Description}
                  </span>
                )}
              </div>
              <ChevronsUpDown className="h-4 w-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>

          <DropdownMenuContent
            className="w-[--radix-dropdown-menu-trigger-width] min-w-[240px]"
            align="start"
            sideOffset={4}
          >
            <DropdownMenuLabel>Groups</DropdownMenuLabel>

            {error && (
              <DropdownMenuItem disabled key="error">
                <div className="text-red-500">{error}</div>
              </DropdownMenuItem>
            )}

            {loading ? (
              <DropdownMenuItem disabled key="loading">
                Loading groups...
              </DropdownMenuItem>
            ) : groups.length === 0 ? (
              <DropdownMenuItem disabled key="no-groups">
                No groups found
              </DropdownMenuItem>
            ) : (
              groups.map((g) => (
                <DropdownMenuItem
                  key={g.ID}
                  onClick={() => setActiveGroup(g)}
                >
                  <div className="flex h-6 w-6 items-center justify-center rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
                    <Users className="h-4 w-4" />
                  </div>
                  <span className="ml-2">{g.Name || "Unnamed Group"}</span>
                </DropdownMenuItem>
              ))
            )}

            <DropdownMenuSeparator />

            <DropdownMenuItem onClick={createGroup} key="create">
              <Plus className="mr-2 h-4 w-4" />
              Create Group
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}

export default TeamSwitcher;
