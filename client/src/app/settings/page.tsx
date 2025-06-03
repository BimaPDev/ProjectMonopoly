import { useState, useEffect } from 'react';
import * as React from "react";
import { ChevronDown, Facebook, Instagram, Linkedin, Twitter, Users, Plus, RefreshCw, UserPlus, AlertCircle, CheckCircle, User2 } from "lucide-react";
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react'
import { InstagramLogoIcon } from '@radix-ui/react-icons';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
const socialPlatforms = [
  {
    id: "instagram",
    name: "instagram",
    icon: Instagram,
    color: "bg-gradient-to-br from-purple-600 to-pink-500",
  },
  {
    id: "facebook",
    name: "facebook",
    icon: Facebook,
    color: "bg-blue-600",
  },
  {
    id: "twitter",
    name: "twitter",
    icon: Twitter,
    color: "bg-sky-500",
  },
  {
    id: "linkedin",
    name: "linkedIn",
    icon: Linkedin,
    color: "bg-blue-700",
  },
];

const GroupManagement = () => {
  // State for creating groups
  const [formData, setFormData] = useState({
    ID: '',
    name: '',
    description: ''
  });
  interface Group {
    ID: number;    
    name: string;  
    description: string; 
  }
  
  // State for managing groups
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [membershipForm, setMembershipForm] = useState({
    username: '',
    password: '',
    platform: ''
  });
  const [userID, setUserID] = React.useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingGroups, setIsFetchingGroups] = useState(false);
  const [isAddingMember, setIsAddingMember] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });
  
  // Fetch groups on component mount
  useEffect(() => {
    fetchGroups();
  }, []);
   const createGroup = async () => {
    if (formData.userID === null) {
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
      setMessage({ text: 'Group created successfully', type: 'success' });
      await fetchGroups();
    } catch (e: any) {
      setMessage({ text: 'Failed to create group', type: 'error' });
      console.error("Error creating group:", e);
      setError(e.message || "Error creating group");
    }
  };
  const fetchGroups = async () => {
    setIsLoading(true)
    const id= localStorage.getItem('userID')
    setUserID(Number(id))
    setIsFetchingGroups(true);
    try {
      
      const res = await fetch(`http://localhost:8080/api/groups?userID=${userID}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" }
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || "Failed to fetch groups");
      }
      
      const data = await res.json() as Group[];
  
      
      if (!Array.isArray(data)) {
        console.error("Expected array response, got:", typeof data);
        throw new Error("Invalid response format from server");
      }
      
      setGroups(data);
      setMessage({ text: 'Groups loaded successfully', type: 'success' });
    } catch (error) {
      setMessage({ text: 'Failed to fetch groups', type: 'error' });
    } finally {
      setIsLoading(false);
      setIsFetchingGroups(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: value
    }));
  };

 const handleMembershipChange = (value: string) => {
  setMembershipForm(prev => ({ ...prev, platform: value }));
};


  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('Form data:', membershipForm);
    if (!formData.ID || !formData.name) {
      setMessage({
        text: 'User ID and group name are required fields',
        type: 'error'
      });
      return;
    }

    const requestData = {
      user_id: parseInt(formData.ID),
      name: formData.name,
      description: formData.description
    };

    setIsLoading(true);
    setMessage({ text: '', type: '' });

    try {
      createGroup();
      } catch (error) {
      const errorMessage = error.response?.data || 'Failed to create group. Please try again.';
      setMessage({ text: errorMessage, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!selectedGroup) {
      setMessage({ text: 'Please select a group first', type: 'error' });
      return;
    }
    
    if (!membershipForm.username || !membershipForm.password) {
      setMessage({ text: 'Username and password are required', type: 'error' });
      return;
    }
   
    const requestData = {
      groupID: selectedGroup.ID,
      userName: membershipForm.username,
      password: membershipForm.password,
      platform: membershipForm.platform
    };

    
    try {
      setIsLoading(true);
      const res = await fetch("http://localhost:8080/api/AddGroupItem", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
      });
      console.log("request happened");
     if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || "Failed to fetch groups");
      }
      
      const data = await res.json;
      console.log(data);
      setMessage({ 
        text: `Account "${membershipForm.username}" added to group "${selectedGroup.name}"`, 
        type: 'success' 
      });
      
      setMembershipForm({
        username: '',
        password: '',
        platform: ''
      });
      } catch (error) {
      const errorMessage = error.response?.data || 'Failed to create group. Please try again.';
      setMessage({ text: errorMessage, type: 'error' });
    } finally {
      setIsLoading(false);
    }
    
  };

  return (
     <div className="min-h-screen p-6 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className='mx-auto space-y-8 max-w-7xl'>
        
        <div className="py-8 text-center">
          <h1 className="mb-4 text-4xl font-bold text-white ">
            Manage Your Groups
          </h1>
          <p className='text-lg text-slate-400'> Manage your social media groups and team members</p>
        </div>
          {/* Message display */}
          {message.text && (
            <div className={`p-4 rounded-xl border backdrop-blur-sm animate-in slide-in-from-top-2 duration-300 ${
            message.type === 'error' 
              ? 'bg-red-500/10 border-red-500/20 text-red-400' 
              : 'bg-green-500/10 border-green-500/20 text-green-400'
          }`}>
             <div className="flex items-center gap-2">
              {message.type === 'error' ? (
                <AlertCircle className="w-4 h-4" />
              ) : (
                <CheckCircle className="w-4 h-4" />
              )}
              {message.text}
            </div>
            </div>
          )}
          
        <div className='grid grid-cols-1 gap-8 xl:grid-cols-3'>
            
          <div className='xl:col-span-2'>
          {/* Group listing section */}
          <div className="flex items-center justify-between p-8 dow-2xl fleborder bg-slate-800/50 backdrop-blur-sm rounded-2xl border-slate-700/50">
            <div>
              <User2></User2>
            <h2 className="mb-4 text-xl font-semibold">Your Groups</h2>
            </div>
            <div >
             <button 
                  onClick={fetchGroups}
                  className="flex items-center gap-2 px-4 py-2 transition-all duration-200 border rounded-lg bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 border-slate-600/50 hover:border-slate-500/50"
                >
                  <RefreshCw className={`w-4 h-4 ${isFetchingGroups ? 'animate-spin' : ''}`} />
                  Refresh Groups
                </button>
            </div>
           
          </div>
          
            {isFetchingGroups ? (
                <div>
                  <div className="py-12 text-center">
                    <div className="inline-flex items-center gap-3 text-slate-400">
                      <div className="w-8 h-8 border-b-2 border-blue-400 rounded-full animate-spin"></div>
                      Loading groups...
                    </div>
                  </div>
                </div>
                
              ):(
                <div className='space-y-4'>
                  {groups.length === 0 ? 
                  (
                    <div className='py-12 text-center'>
                      
                      <Users ></Users>
                      <p className='text-lg text-slate-400'>No groups found</p>
                      <p className='text-sm text-slate-400'> Create your first group to get started</p>
                      <button onClick={createGroup} className='m-5 rounded-lg border-slate-600/30 bg-slate-700/30 hover:shadow-blue-500/25 hover:bg-slate-700/50'>
                        <span>
                        <Plus className='w-4 h-4 mr-2' />
                        Create Group
                        </span>
                      </button>
                    </div>
                    
                  )
                  
                  :(
                    <div className='grid gap-3 m-2 grid-col-1 md:grid-cols-2'>
                      {groups.map( group => (
                        <div
                        key={group.ID}
                        onClick={() => setSelectedGroup(group)}
                      className={`group relative p-6 rounded-xl cursor-pointer transition-all duration-300 border ${
                              selectedGroup?.ID === group.ID 
                                ? 'border-blue-500/50 bg-blue-500/10 shadow-lg shadow-blue-500/25' 
                                : 'border-slate-600/30 bg-slate-700/30 hover:border-slate-500/50 hover:bg-slate-700/50'
                            }`}
                        >
                          <h3 className='font-medium text-slate-400'>{group.name}</h3>
                          <p className='text-sm text-slate-400'>{group.description || 'No description'}</p>
                        </div>
                        
                      ))}
                    </div>
                    
                  )}
                </div>
              )}
        
      </div>
      <div className="p-8 shadow-2xl bg-slate-800/50 backdrop-blur-sm rounded-2xl border-slate-700/50">
          <div className='flex items-center gap-3 mb-2'>
            <div className='p-2 rounded-lg bg-green-500/20'>
              <UserPlus className='text-green-400 '></UserPlus>
            </div>
            <p className='font-semibold font-lg'>Add a social media login</p>
          </div>
           { !selectedGroup ? (
            
            <div className="py-8 text-center">
                  <div className="inline-block p-3 mb-3 rounded-lg bg-amber-500/20">
                    <AlertCircle className="w-6 h-6 text-amber-400" />
                  </div>
                  <p className="font-medium text-amber-400">Select a group first</p>
                  <p className="mt-1 text-sm text-slate-500">Choose a group from the list to add members</p>
                </div>
            
            
           ): (
          <form onSubmit={handleAddMember} className="space-y-4">
            <div className="mb-2">
              <p className="font-medium text-m tex-white">Selected Group: <span className="px-1 bg-gray-700 rounded-lg opacity-1">{selectedGroup.name}</span></p>
            </div>
            
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-white">Username/Email</label>
              <input
                type="text"
                id="username"
                name="username"
                onChange={(e) => setMembershipForm(prev => ({ ...prev, [e.target.name]: e.target.value }))}
                className="mb-1 bg-gray-100 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5  dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-gray-400 dark:focus:ring-blue-500 dark:focus:border-blue-500"
                placeholder="Enter username or email"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                onChange={(e) => setMembershipForm(prev => ({ ...prev, [e.target.name]: e.target.value }))}
                className="mb-1 bg-slate-500 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5  dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-gray-400 dark:focus:ring-blue-500 dark:focus:border-blue-500"
                placeholder="Enter password"
              />
            </div>
            {/* Platform select */}
              <div>
                <Select 
                  onValueChange={(value) => setMembershipForm(prev => ({ ...prev, platform: value }))}
                >
                  
                    <SelectTrigger >
                      <SelectValue placeholder="Select a platform" />
                    </SelectTrigger>
                  
                  <SelectContent>
                    {socialPlatforms.map((platform) => (
                      <SelectItem 
                        key={platform.id} 
                        value={platform.name}
                      >
                        <div className="flex items-center gap-2">
                          <div
                            className={cn(
                              "flex h-6 w-6 items-center justify-center rounded-full text-white",
                              platform.color
                            )}
                          >
                            <platform.icon className="w-3 h-3" />
                          </div>
                          {platform.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
            </div>
            
            <button
              type="submit"
              disabled={isAddingMember}
              className="w-full px-4 py-2 font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isAddingMember ? 'Adding...' : 'Add to Group'}
            </button>
          </form>
          
          )}   
              
      </div>
    </div>
    </div>
    </div>
  );
};

export default GroupManagement;
