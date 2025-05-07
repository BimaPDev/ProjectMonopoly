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

interface Group {
  ID: number;
  name: string;
  description: string;
}

export function TeamSwitcher() {
  const [groups, setGroups] = React.useState<Group[]>([]);
  const [activeGroup, setActiveGroup] = React.useState<Group | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [userID, setUserID] = React.useState<number | null>(null);
  const [isOpen, setIsOpen] = React.useState(false);
  
  // First effect - load userID from localStorage when component mounts
  React.useEffect(() => {
    try {
      const storedUserID = localStorage.getItem("userID");
     
      
      if (storedUserID) {

        const parsedUserID = Number(storedUserID);
        setUserID(parsedUserID);
        
      } else {
        
        setUserID(1); // Default testing ID
      }
    } catch (err) {
      console.error('Error accessing localStorage:', err);
      setError('Error accessing user data');
    }
  }, []);

  // Second effect - fetch groups whenever userID changes
  React.useEffect(() => {
    if (userID !== null) {
      fetchGroups();
    }
  }, [userID]);

  const fetchGroups = async () => {
    if (userID === null) return;
    
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
      
      if (!res.ok) {
        throw new Error(`Error fetching groups: ${res.status}`);
      }
      
      const data = await res.json();
     
      
      if (!Array.isArray(data)) {
        console.error("Expected array response, got:", typeof data);
        throw new Error("Invalid response format from server");
      }
      
     
      setGroups(data);
      
      // Set active group if there are groups available
      if (data.length > 0) {
        setActiveGroup(data[0]);
      }
      
    } catch (e: any) {
      console.error("Error fetching groups:", e);
      setError(e.message || "Error fetching groups");
    } finally {
      setLoading(false);
    }
  };

  const createGroup = async () => {
    if (userID === null) {
      setError("User ID not found. Please log in again.");
      return;
    }
    
    const name = window.prompt("New group name:")?.trim();
    if (!name) return;
    
    const description = window.prompt("Description (optional):")?.trim() || "";
    
    try {
      const res = await fetch("http://localhost:8080/api/groups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userID, name, description }),
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || `Create failed with status: ${res.status}`);
      }
      
      await fetchGroups();
    } catch (e: any) {
      console.error("Error creating group:", e);
      setError(e.message || "Error creating group");
    }
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
          <DropdownMenuTrigger asChild onClick={() => {
            console.log('Dropdown clicked, groups:', groups);
            setIsOpen(!isOpen);
          }}>
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
                    ? activeGroup.name
                    : "No Groups"}
                </span>
                {activeGroup?.description && (
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
              <>
                
                {groups.map((g) => (
                  <DropdownMenuItem
                    key={g.ID}
                    onClick={() => {
                      console.log('Selected group:', g);
                      setActiveGroup(g);
                    }}
                  >
                    <div className="flex h-6 w-6 items-center justify-center rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
                      <Users className="h-4 w-4" />
                    </div>
                    <span className="ml-2">{g.name}</span>
                  </DropdownMenuItem>
                ))}
              </>
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