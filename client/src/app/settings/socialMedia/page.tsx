import { useState, useEffect } from 'react';
import * as React from "react";
import { Facebook, Instagram, Linkedin, Twitter, Users, Plus, RefreshCw, UserPlus, AlertCircle, CheckCircle, User2, UserRoundPen, Eye, EyeOff } from "lucide-react";
import { FaTiktok } from "react-icons/fa";
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
        name: "Instagram",
        icon: Instagram,
        color: "bg-gradient-to-br from-purple-600 to-pink-500",
    },
    {
        id: "facebook",
        name: "Facebook",
        icon: Facebook,
        color: "bg-blue-600",
    },
    {
        id: "twitter",
        name: "Twitter",
        icon: Twitter,
        color: "bg-sky-500",
    },
    {
        id: "linkedin",
        name: "Linkedin",
        icon: Linkedin,
        color: "bg-blue-700",
    },
    {
        id: 'tiktok',
        name: 'TikTok',
        icon: FaTiktok,
        color: 'bg-black'
    }
];

export default function SocialMedia() {
    console.log("SocialMedia Component Loaded: Ver 1.1 (Auth Fix)");
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

    interface GroupItem {
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
            const res = await fetch(`/api/groups`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem('token')}`
                },
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

    const processGroupItems = (Data: any) => {
        Data.forEach(Data => {
            const apiGroupID = Data.group_id;
            const apiPlatform = Data.platform;
            const apiUsername = Data.data.RawMessage.username;
            const apiPassword = Data.data.RawMessage.password;
            const date = new Date(Data.updated_at.Time);
            const formattedDate: string = date.toLocaleString();

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
        const res = await fetch(`/api/GroupItem?groupID=${selectedGroup.ID}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem('token')}`
            },
        });

        if (!res.ok) {
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
        setEditForm({ Username: '', Password: '' });
    };

    const saveEdit = async (item) => {
        try {
            const requestData = {
                userName: editForm.Username,
                password: editForm.Password,
                GroupID: selectedGroup?.ID,
                platform: item.Platform
            };

            const res = await fetch(`/api/AddGroupItem`, {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(requestData)
            });

            if (res.ok) {
                setMessage({ text: 'Login Updated!', type: 'success' });
                setEditingItem(null);
                setEditForm({ Username: '', Password: '' });
                await fetchGroupItems();
            } else {
                const errorText = await res.text();
                console.error('Update failed:', errorText);
                setMessage({ text: 'Login Not Updated!', type: 'error' });
            }
        } catch (e) {
            console.error('Error updating login:', e);
            setMessage({ text: 'Could not update login', type: 'error' });
        } finally {
            fetchGroupItems();
        }
    };

    const fetchGroups = async () => {
        setIsLoading(true);
        const id = localStorage.getItem('userID');
        const numericID = Number(id);
        setUserID(numericID);

        setIsFetchingGroups(true);
        try {
            const res = await fetch(`/api/groups?userID=${numericID}`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (res.status === 401) {
                console.error("401 Unauthorized: Redirecting to login");
                localStorage.removeItem('token');
                window.location.href = '/login';
                return;
            }

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
            const res = await fetch(`/api/AddGroupItem`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(requestData)
            });

            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(errorText || "Failed to fetch groups");
            }

            const data = await res.json;
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
        <div className="min-h-screen text-white bg-black">
            <div className="container px-6 py-8 mx-auto max-w-7xl">
                {/* Header */}
                <div className="mb-8 text-center">
                    <h1 className="mb-3 text-3xl font-semibold text-white">
                        Manage Your Groups
                    </h1>
                    <p className="text-lg text-gray-400">
                        Manage your social media groups and team members
                    </p>
                </div>

                {/* Message display */}
                {message.text && (
                    <div className={`p-4 rounded-xl border backdrop-blur-sm mb-6 ${message.type === 'error'
                        ? 'bg-red-900/20 border-red-500/30 text-red-300'
                        : 'bg-emerald-900/20 border-emerald-500/30 text-emerald-300'
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

                <div className="grid h-full grid-cols-1 gap-6 xl:grid-cols-3">
                    {/* Groups Section */}
                    <div className="space-y-6 xl:col-span-2">
                        {/* Groups Header */}
                        <div className="p-6 bg-black border border-gray-800 rounded-xl">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <div className="p-3 rounded-lg bg-blue-500/10">
                                        <User2 className="w-6 h-6 text-blue-400" />
                                    </div>
                                    <h2 className="text-xl font-semibold text-white">Your Groups</h2>
                                </div>
                                <button
                                    onClick={fetchGroups}
                                    className="flex items-center gap-2 px-4 py-2 text-gray-300 transition-colors bg-black border border-gray-700 rounded-lg hover:bg-black hover:text-white hover:border-gray-600"
                                >
                                    <RefreshCw className={`w-4 h-4 ${isFetchingGroups ? 'animate-spin' : ''}`} />
                                    Refresh Groups
                                </button>
                            </div>
                        </div>

                        {/* Groups Content */}
                        {isFetchingGroups ? (
                            <div className="p-12 bg-black border border-gray-800 rounded-xl">
                                <div className="text-center">
                                    <div className="inline-flex items-center gap-3 text-gray-400">
                                        <div className="w-8 h-8 border-b-2 border-blue-400 rounded-full animate-spin"></div>
                                        Loading groups...
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {groups.length === 0 ? (
                                    <div className="p-12 bg-black border border-gray-800 rounded-xl">
                                        <div className="text-center">
                                            <div className="inline-block p-4 mb-4 border rounded-full bg-black border-gray-800">
                                                <Users className="w-8 h-8 text-gray-400" />
                                            </div>
                                            <p className="mb-2 text-lg text-gray-300">No groups found</p>
                                            <p className="mb-6 text-sm text-gray-400">Create your first group to get started</p>
                                            <button
                                                onClick={createGroup}
                                                className="flex items-center gap-2 px-6 py-3 mx-auto text-white transition-colors bg-blue-600 rounded-lg hover:bg-blue-700"
                                            >
                                                <Plus className="w-4 h-4" />
                                                Create Group
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                        {groups.map(group => (
                                            <div
                                                key={group.ID}
                                                onClick={() => {
                                                    setSelectedGroup(prev => prev?.ID === group.ID ? null : group);
                                                }}
                                                className={`p-6 rounded-xl cursor-pointer transition-all duration-300 border ${selectedGroup?.ID === group.ID
                                                    ? 'border-blue-500/50 bg-blue-900/10 shadow-lg shadow-blue-500/10'
                                                    : 'border-gray-800 bg-black hover:border-gray-700 hover:bg-black'
                                                    }`}
                                            >
                                                <h3 className="mb-1 font-medium text-white">{group.name}</h3>
                                                <p className="text-sm text-gray-400">{group.description || 'No description'}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                        <div className="p-6 bg-black border border-gray-800 rounded-xl">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-3 rounded-lg bg-purple-500/10">
                                    <UserRoundPen className="w-6 h-6 text-purple-400" />
                                </div>
                                <h3 className="text-lg font-semibold text-white">Edit Logins</h3>
                            </div>

                            {!selectedGroup ? (
                                <div className="py-8 text-center">
                                    <p className="text-sm text-gray-400">Choose a group from the list to edit logins</p>
                                </div>
                            ) : (
                                <div className="max-h-[400px] overflow-y-auto space-y-4">
                                    {groupItems.map(item => {
                                        const isEditing = editingItem === (item.ID + item.Platform);
                                        return (
                                            <div key={item.ID + item.Platform} className="p-4 border border-gray-800 rounded-lg bg-black">
                                                {isEditing ? (
                                                    <div className="space-y-4">
                                                        <div>
                                                            <label className="block mb-2 text-sm font-medium text-white">Username</label>
                                                            <input
                                                                value={editForm.Username}
                                                                onChange={(e) => setEditForm(prev => ({ ...prev, Username: e.target.value }))}
                                                                placeholder="Username"
                                                                className="w-full p-3 text-white bg-black border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder:text-gray-400"
                                                            />
                                                        </div>
                                                        <div className='w-full'>
                                                            <label className="block mb-2 text-sm font-medium text-white">Password</label>
                                                            <div className="relative">
                                                                <input
                                                                    value={editForm.Password}
                                                                    onChange={(e) => setEditForm(prev => ({ ...prev, Password: e.target.value }))}
                                                                    placeholder="Password"
                                                                    type={showPass ? 'text' : 'password'}
                                                                    className="w-full p-3 pr-10 text-white bg-black border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder:text-gray-400"
                                                                />
                                                                <div className='flex justify-end w-full'>
                                                                    <button
                                                                        type="button"
                                                                        className="absolute text-gray-400 transform -translate-y-1/2 right-6 top-1/2 hover:text-gray-300"
                                                                        onClick={() => setShowPass(prev => !prev)}
                                                                    >
                                                                        {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="flex space-x-2">
                                                            <button
                                                                className="flex-1 px-4 py-2 text-white transition-colors bg-blue-600 rounded-lg hover:bg-blue-700"
                                                                onClick={() => saveEdit(item)}
                                                            >
                                                                Save
                                                            </button>
                                                            <button
                                                                className="flex-1 px-4 py-2 text-white transition-colors bg-gray-700 rounded-lg hover:bg-gray-600"
                                                                onClick={cancelEdit}
                                                            >
                                                                Cancel
                                                            </button>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div className="space-y-3">
                                                        <div className="flex items-center gap-3">
                                                            <span className="font-medium text-white">Username: {item.Username}</span>
                                                            {(() => {
                                                                const platform = socialPlatforms.find(p => p.id === item.Platform.toLowerCase());
                                                                const Icon = platform?.icon;
                                                                return Icon ? (
                                                                    <div className={`flex h-6 w-6 items-center justify-center rounded-full text-white ${platform.color}`}>
                                                                        <Icon className="w-4 h-4" />
                                                                    </div>
                                                                ) : <span className="text-sm text-gray-400">{item.Platform}</span>;
                                                            })()}
                                                        </div>

                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center w-full gap-2">
                                                                <span className="font-medium text-white">Password:</span>
                                                                <span className="text-gray-300">{showPass ? item.Password : '••••••••••'}</span>
                                                                <div className='flex justify-end w-full'>
                                                                    <button
                                                                        className="mr-20 text-gray-400 hover:text-gray-300"
                                                                        onClick={() => setShowPass(prev => !prev)}
                                                                    >
                                                                        {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                                                    </button>
                                                                </div>
                                                            </div>

                                                        </div>
                                                        <span className="text-xs text-gray-400">Updated: {item.Updated}</span>
                                                        <button
                                                            className="w-full px-4 py-2 text-white transition-colors bg-blue-600 rounded-lg hover:bg-blue-700"
                                                            onClick={() => startEdit(item)}
                                                        >
                                                            Edit
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    </div>


                    {/* Right Sidebar */}
                    <div className="space-y-6">
                        {/* Add Social Media Login */}
                        <div className="p-6 bg-black border border-gray-800 rounded-xl">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-3 rounded-lg bg-emerald-500/10">
                                    <UserPlus className="w-6 h-6 text-emerald-400" />
                                </div>
                                <h3 className="text-lg font-semibold text-white">Add Social Media Login</h3>
                            </div>

                            {!selectedGroup ? (
                                <div className="py-8 text-center">
                                    <div className="inline-block p-3 mb-3 rounded-lg bg-amber-500/10">
                                        <AlertCircle className="w-6 h-6 text-amber-400" />
                                    </div>
                                    <p className="mb-1 font-medium text-amber-400">Select a group first</p>
                                    <p className="text-sm text-gray-400">Choose a group from the list to add login</p>
                                </div>
                            ) : (
                                <form onSubmit={handleAddMember} className="space-y-4">
                                    <div className="mb-4">
                                        <p className="text-sm text-gray-400">Selected Group:</p>
                                        <p className="font-medium text-white">{selectedGroup.name}</p>
                                    </div>

                                    <div>
                                        <label htmlFor="username" className="block mb-2 text-sm font-medium text-white">
                                            Username/Email
                                        </label>
                                        <input
                                            type="text"
                                            id="username"
                                            name="username"
                                            value={membershipForm.username}
                                            onChange={(e) => setMembershipForm(prev => ({ ...prev, [e.target.name]: e.target.value }))}
                                            className="w-full p-3 text-white bg-black border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder:text-gray-400"
                                            placeholder="Enter username or email"
                                        />
                                    </div>

                                    <div>
                                        <label htmlFor="password" className="block mb-2 text-sm font-medium text-white">
                                            Password
                                        </label>
                                        <input
                                            type="password"
                                            id="password"
                                            name="password"
                                            value={membershipForm.password}
                                            onChange={(e) => setMembershipForm(prev => ({ ...prev, [e.target.name]: e.target.value }))}
                                            className="w-full p-3 text-white bg-black border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder:text-gray-400"
                                            placeholder="Enter password"
                                        />
                                    </div>

                                    <div>
                                        <label className="block mb-2 text-sm font-medium text-white">Platform</label>
                                        <Select
                                            onValueChange={(value) => setMembershipForm(prev => ({ ...prev, platform: value }))}
                                        >
                                            <SelectTrigger className="text-white bg-black border-gray-700">
                                                <SelectValue placeholder="Select a platform" />
                                            </SelectTrigger>
                                            <SelectContent className="bg-black border-gray-700">
                                                {socialPlatforms.map((platform) => (
                                                    <SelectItem
                                                        key={platform.id}
                                                        value={platform.name}
                                                        className="text-white hover:bg-black hover:border-gray-600"
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
                                        className="w-full px-4 py-3 font-medium text-white transition-colors bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                                    >
                                        {isAddingMember ? 'Adding...' : 'Add to Group'}
                                    </button>
                                </form>
                            )}
                        </div>

                        {/* Edit Social Media Login */}

                    </div>
                </div>
            </div>
        </div>
    );
};

