import { useState, useEffect } from 'react';
import * as React from "react";
import { Facebook, Instagram, Linkedin, Twitter, Users, Plus, RefreshCw, UserPlus, AlertCircle, CheckCircle, User2, UserRoundPen } from "lucide-react";

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
  interface GroupItem{
    ID: number,
    Platform: string,
    Updated: string,
    Username: string,
    Password: string,
    
  }
  // State for managing groups
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
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
  const [groupItems, setGroupItems] = useState<GroupItem[]>([]);
  const [editingItem, setEditingItem] = useState<null | string>(null);
  const [editForm, setEditForm] = useState<{ Username: string; Password: string }>({ Username: '', Password: '' });
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState("")

  
  // Fetch groups on component mount
  useEffect(() => {
    fetchGroups();
  }, []);
  
  useEffect(() => {
  if (selectedGroup) {
    fetchGroupItems();
  }
}, [selectedGroup]);
   const createGroup = async () => {
    if (formData.ID === null) {
      setError("User ID not found. Please log in again.");
      return;
    }
    
    const name = window.prompt("New group name:")?.trim();
    if (!name) return;
    
    const description = window.prompt("Description (optional):")?.trim() || "";
    
    try {
      const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/groups`, {
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
      
    }
  };
   const processGroupItems = (Data: any) =>{
     Data.forEach(Data => {
       const apiGroupID = Data.group_id;
       const apiPlatform = Data.platform;
       const apiUsername = Data.data.RawMessage.username;
       const apiPassword = Data.data.RawMessage.password;
       const date = new Date(Data.updated_at.Time);
       const formattedDate:string = date.toLocaleString();

       setGroupItems(prev => {
         const isDupe = prev.some(item => item.ID === apiGroupID && item.Platform === apiPlatform);
         if (isDupe) return prev;
         return [
           ...prev,
           {
             ID: apiGroupID,
             Platform: apiPlatform,
             Updated: formattedDate,
             Username: apiUsername,
             Password: apiPassword
           }
         ];
       });
     });


   }
  const fetchGroupItems = async () => {
    if (!selectedGroup) {
      setMessage({ text: 'No group selected', type: 'error' });
      return;
    }
    const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/GetGroupItem?groupID=${selectedGroup.ID}`,{
      method: "GET",
      headers: {"Content-Type": "application/json"},
    });
    
    if(!res.ok){
      const errorText = await res.text();
      throw new Error(errorText || "Error happened when fetching group items");
    }
    const Data = await res.json() as GroupItem[];
    processGroupItems(Data)
    
  }
  const startEdit = (itemEdited) => {
    setEditingItem(itemEdited.ID + itemEdited.Platform);
    setEditForm({
      Username: itemEdited.Username,
      Password: itemEdited.Password

    });

  };

  const cancelEdit = () => {
    setEditingItem(null);
    setEditForm({});

  };

  const saveEdit = async () =>{

    
  };



  
  const fetchGroups = async () => {
    setIsLoading(true)
    const id= localStorage.getItem('userID')
    setUserID(Number(id))
    setIsFetchingGroups(true);
    try {
      
      const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/groups?userID=${userID}`, {
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
      setMessage({ text: "'Failed to create group. Please try again.'", type: 'error' });
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
    console.log(requestData)
    
    try {
      setIsLoading(true);
      const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/AddGroupItem`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestData)
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
      
   
      setMessage({ text: "Failed to create group. Please try again.", type: 'error' });
    } finally {
      setIsLoading(false);
    }
    
  };

  return (
     <div className="h-full pd-3 w-3xl bg-gradient-to-br from-black-900 via-slate-800 to-slate-900">
      <div className='mx-auto space-y-8 max-w-7xl'>
        
        <div className="py-3 text-center">
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
          
        <div className='grid h-full grid-cols-1 gap-2 xl:grid-cols-3'>
            
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
                      <div className="flex justify-center w-full mt-5">
                        <button 
                          onClick={createGroup}
                          className="flex items-center gap-2 px-4 py-2 transition-all duration-200 border rounded-lg bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 border-slate-600/50 hover:border-slate-500/50"
                        >
                          <Plus className="w-4 h-4" />
                          Create Group
                        </button>
                      </div>
                    </div>
                    
                  )
                  
                  :(
                    <div className='grid gap-3 m-2 grid-col-1 md:grid-cols-2'>
                      {groups.map( group => (
                        <div
                        key={group.ID}
                       onClick={() => {
                          setSelectedGroup(prev => prev?.ID === group.ID ? null : group);
                        }}

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
      
      <div className="gap-3 px-3 pt-3 shadow-2xl bg-slate-800/50 backdrop-blur-sm rounded-2xl border-slate-700/50">
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
                  <p className="mt-1 text-sm text-slate-500">Choose a group from the list to add login</p>
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
      
      
      <div className='gap-3  mt-4 shadow-2xl bg-slate-800/50 backdrop-blur-sm rounded-2xl border-slate-700/50'>
        <div className='flex items-center gap-3 p-3'>
          <div className='p-2 rounded-lg bg-green-500/20'>
            <UserRoundPen className='text-green-400'></UserRoundPen>

          </div>
          <p className='font-semibold font-lg'>Edit a social media login</p>
          {groupItems.length > 2  && (
              <div className="flex space-x-2">
                <svg width="22" height="22" fill="none" viewBox="0 0 22 22" className="size-5 flex-none">
                  <path fill="currentColor" className="dark:[fill-opacity:0.1]" fillOpacity="0.05" fillRule="evenodd"
                        d="M10.5 8.77V2a1.5 1.5 0 1 0-3 0v10.929a3.5 3.5 0 0 1-1.025 2.474l-.008.009a6.5 6.5 0 0 0-1.87-3.937l-.536-.536a1.5 1.5 0 1 0-2.122 2.121l.536.536A3.5 3.5 0 0 1 3.5 16.07v.1a3.5 3.5 0 0 0 1.025 2.475l1.829 1.828A3.5 3.5 0 0 0 8.828 21.5h7.758a2.5 2.5 0 0 0 1.768-.733l.242-.242a6.5 6.5 0 0 0 1.904-4.596v-2.29a3.5 3.5 0 0 0-2.814-3.432z"
                        clipRule="evenodd"></path>
                  <path fill="currentColor"
                        d="M10.5 8.77H10v.41l.402.08zm-4.025 6.633-.354-.353zm-.008.009-.498.05.107 1.048.744-.745zm-1.87-3.937-.354.353zm-.536-.536-.354.354zm-2.122 0 .354.354zm0 2.121.354-.353zm.536.536-.354.353zm2.05 5.05L4.172 19zm1.829 1.828L6 20.829zm12 .293.353.354zm.242-.242-.353-.354zm-.91-10.318.099-.49zM10 2v6.77h1V2zM9 1a1 1 0 0 1 1 1h1a2 2 0 0 0-2-2zM8 2a1 1 0 0 1 1-1V0a2 2 0 0 0-2 2zm0 6.17V2H7v6.17zM8 9.5V8.17H7V9.5zm0 3.429V9.5H7v3.429zm-1.172 2.828A4 4 0 0 0 8 12.929H7a3 3 0 0 1-.879 2.12zm-.008.008.008-.008-.707-.707-.008.008zm-2.577-3.937a6 6 0 0 1 1.726 3.634l.995-.1A7 7 0 0 0 4.95 11.12zm-.536-.535.536.535.707-.707-.536-.536zm-1.414 0a1 1 0 0 1 1.414 0l.707-.708a2 2 0 0 0-2.828 0zm0 1.414a1 1 0 0 1 0-1.415l-.707-.707a2 2 0 0 0 0 2.829zm.535.535-.535-.535-.707.707.535.535zM4 16.071a4 4 0 0 0-1.172-2.829l-.707.707A3 3 0 0 1 3 16.071zm0 .1v-.1H3v.1zm.879 2.122A3 3 0 0 1 4 16.17H3A4 4 0 0 0 4.172 19zm1.828 1.828L4.88 18.293 4.172 19 6 20.828zM8.828 21a3 3 0 0 1-2.12-.88L6 20.829A4 4 0 0 0 8.828 22zm7.758 0H8.828v1h7.758zM18 20.414a2 2 0 0 1-1.414.586v1a3 3 0 0 0 2.121-.88zm.243-.243-.243.243.707.707.243-.243zM20 15.93a6 6 0 0 1-1.757 4.242l.707.707a7 7 0 0 0 2.05-4.95zm0-2.29v2.29h1v-2.29zm-2.412-2.941A3 3 0 0 1 20 13.639h1a4 4 0 0 0-3.215-3.922zM10.402 9.26l7.186 1.438.197-.981-7.187-1.437z"></path>
                  <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round"
                        d="M1.5 4.677a14 14 0 0 1 4-1.736m11 1.736a14 14 0 0 0-4-1.736"></path>
                </svg>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Scroll vertically</p></div>
          )}
        </div>
        {!selectedGroup ? (

            <div className="py-8 text-center">
              <p className="mt-1 text-sm text-slate-500">Choose a group from the list to edit login</p>
            </div>


        ) : (
            <div className='p-3  max-h-[300px] overflow-y-auto'>

              {groupItems.map(item => {
                const isEditing = editingItem === (item.ID + item.Platform);
                return (
                    <div
                        key={item.ID + item.Platform}
                    >
                      {isEditing ? (
                          <div className='w-md'>
                            <div className='flex flex-col w-md'>
                              <input
                                  value={editForm.Username}
                                  onChange={(e) => setEditForm(prev => ({...prev, Username: e.target.value}))}
                                  placeholder="Username"
                                  className="mb-1 bg-gray-100 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5  dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-gray-400 dark:focus:ring-blue-500 dark:focus:border-blue-500"
                              />
                              <div className='relative'>
                                <input
                                    value={editForm.Password}
                                    onChange={(e) => setEditForm(prev => ({...prev, Password: e.target.value}))}
                                    placeholder="Password"
                                    type={showPass ? 'text' : 'password'}
                                    className="mb-1 bg-gray-100 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5  dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-gray-400 dark:focus:ring-blue-500 dark:focus:border-blue-500"
                                />
                                <button
                                    className='absolute text-gray-500 -translate-y-1/2 right-2 top-1/2 hover:text-gray-300'
                                    onClick={() => {
                                      setShowPass(prev => !prev);
                                    }}
                          >
                            <span>{showPass ? <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-eye-icon lucide-eye"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>: <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-eye-closed-icon lucide-eye-closed"><path d="m15 18-.722-3.25"/><path d="M2 8a10.645 10.645 0 0 0 20 0"/><path d="m20 15-1.726-2.05"/><path d="m4 15 1.726-2.05"/><path d="m9 18 .722-3.25"/></svg> }</span>
                          </button>
                        </div>
                        <div className='mt-2'>
                        <button className = "w-full py-1 mt-2 mb-2 font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"onClick={() => saveEdit(item)}>Save</button>
                        <button className = "w-full px-2 py-1 font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"onClick={cancelEdit}>Cancel</button>
                        </div>
                      </div>
                    </div>

                  ): (
                      <div>
                        <div className='flex flex-col justify-center gap-4 mb-4'>
                          <div className={"flex gap-x-2 items-center"}>
                            <span className='font-semibold'>Username: {item.Username}</span>
                            {(() => {
                              const platform = socialPlatforms.find(p => p.id === item.Platform);
                              const Icon = platform?.icon;
                              return Icon ? (
                                  <div
                                      className={`flex h-8 w-8 items-center justify-center rounded-full text-white ${platform.color}`}
                                  >
                                    <Icon className="w-6 h-6" />
                                  </div>
                              ) : <span className={"text-sm"}> {item.Platform}</span>;
                            })()}
                          </div>


                          <div className='relative'>
                            <span className='font-semibold'>Password:</span>
                            <span> {showPass ? item.Password : '••••••••••'}</span>
                            <button
                                className='absolute ml-2 text-gray-500 -translate-y-1/2 right-48 top-1/2 hover:text-gray-300'
                                onClick={() => {
                                  setShowPass(prev => !prev);
                                }}
                            >
                              <span>{showPass ?
                                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
                                       fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                                       strokeLinejoin="round" className="lucide lucide-eye-icon lucide-eye">
                                    <path
                                        d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/>
                                    <circle cx="12" cy="12" r="3"/>
                                  </svg> :
                                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
                                       fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                                       strokeLinejoin="round"
                                       className="lucide lucide-eye-closed-icon lucide-eye-closed">
                                    <path d="m15 18-.722-3.25"/>
                                    <path d="M2 8a10.645 10.645 0 0 0 20 0"/>
                                    <path d="m20 15-1.726-2.05"/>
                                    <path d="m4 15 1.726-2.05"/>
                                    <path d="m9 18 .722-3.25"/>
                                  </svg>}</span>
                            </button>
                            <span className='absolute text-xs text-slate-400 right-2'>Updated: {item.Updated}</span>
                          </div>

                        </div>
                        <button
                            className="w-full px-4 py-2 font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                            onClick={() => startEdit(item)}>Edit
                        </button>
                        <div>
                          <hr className="h-px my-8 bg-gray-200 border-0 dark:bg-gray-700"/>
                        </div>
                      </div>

                  )}
                </div>
              );
            })}
           </div>)}
      </div>
     </div>
    </div>
    </div>
    </div>
  );
};

export default GroupManagement;
