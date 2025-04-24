"use client";

import * as React from "react";
import { ChevronsUpDown, Plus, Users } from "lucide-react";

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

// Match the structure returned by your GetGroups handler
interface Group {
  id: number;
  name: string;
  description: string;
}

export function TeamSwitcher() {
  const [groups, setGroups] = React.useState<Group[]>([]);
  const [activeGroup, setActiveGroup] = React.useState<Group | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  
  // In a real app you'd get this from your auth context/JWT
  const userId = 1;

  // Fetch groups on mount
  React.useEffect(() => {
    fetchGroups();
  }, []);

  // Function to fetch groups
  const fetchGroups = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log(`Fetching groups for user ${userId}...`);
      const res = await fetch(`http://localhost:8080/api/groups?user_id=${userId}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" }
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || "Failed to fetch groups");
      }
      
      const data = await res.json() as Group[];
      console.log("API response:", data);
      
      if (!Array.isArray(data)) {
        console.error("Expected array response, got:", typeof data);
        throw new Error("Invalid response format from server");
      }
      
      setGroups(data);
      
      if (data.length > 0) {
        setActiveGroup(data[0]);
      }
    } catch (err: any) {
      console.error("Error fetching groups:", err);
      setError(err.message || "An error occurred while fetching groups");
    } finally {
      setLoading(false);
    }
  };

  // Create a new group
  const createGroup = async () => {
    const name = window.prompt("Enter new group name:")?.trim();
    if (!name) return;
    
    const description = window.prompt("Enter group description (optional):")?.trim() || "";
    
    try {
      console.log("Creating group with data:", { user_id: userId, name, description });
      const res = await fetch("http://localhost:8080/api/groups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          name,
          description,
        }),
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || "Failed to create group");
      }
      
      const newGroup = await res.json() as Group;
      console.log("Created group:", newGroup);
      
      // Add the new group to the list and set it as active
      setGroups(prev => [...prev, newGroup]);
      setActiveGroup(newGroup);
      
      // Refresh the group list to ensure everything is in sync
      fetchGroups();
      
    } catch (err: any) {
      console.error("Error creating group:", err);
      setError(err.message || "An error occurred while creating the group");
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
                  {loading ? "Loading..." : 
                   error ? "Error loading groups" :
                   activeGroup ? activeGroup.name : "No Groups"}
                </span>
                {activeGroup && activeGroup.description && (
                  <span className="block text-xs text-zinc-500 dark:text-zinc-400">
                    {activeGroup.description}
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
              <DropdownMenuItem>
                <div className="text-red-500">{error}</div>
              </DropdownMenuItem>
            )}

            {loading ? (
              <DropdownMenuItem disabled>Loading groups...</DropdownMenuItem>
            ) : groups.length === 0 ? (
              <DropdownMenuItem disabled>No groups found</DropdownMenuItem>
            ) : (
              groups.map((group) => (
                <DropdownMenuItem
                  key={group.id}
                  onClick={() => setActiveGroup(group)}
                >
                  <div className="flex h-6 w-6 items-center justify-center rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
                    <Users className="h-4 w-4" />
                  </div>
                  <span className="ml-2">{group.name}</span>
                </DropdownMenuItem>
              ))
            )}

            <DropdownMenuSeparator />

            <DropdownMenuItem onClick={createGroup}>
              <Plus className="mr-2 h-4 w-4" />
              Create Group
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
