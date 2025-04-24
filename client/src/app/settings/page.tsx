import React, { useState, useEffect } from 'react';

const GroupManagement = () => {
  // State for creating groups
  const [formData, setFormData] = useState({
    user_id: '',
    name: '',
    description: ''
  });
  
  // State for managing groups
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [membershipForm, setMembershipForm] = useState({
    username: '',
    password: ''
  });
  const userId = 1;
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingGroups, setIsFetchingGroups] = useState(false);
  const [isAddingMember, setIsAddingMember] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  // Fetch groups on component mount
  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    setIsFetchingGroups(true);
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
      setMessage({ text: 'Groups loaded successfully', type: 'success' });
    } catch (error) {
      setMessage({ text: 'Failed to fetch groups', type: 'error' });
    } finally {
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

  const handleMembershipChange = (e) => {
    const { name, value } = e.target;
    setMembershipForm(prevState => ({
      ...prevState,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.user_id || !formData.name) {
      setMessage({
        text: 'User ID and group name are required fields',
        type: 'error'
      });
      return;
    }

    const requestData = {
      user_id: parseInt(formData.user_id),
      name: formData.name,
      description: formData.description
    };

    setIsLoading(true);
    setMessage({ text: '', type: '' });

    try {
      // Simulated API call
      // const response = await axios.post('/api/createGroup', requestData);
      const mockResponse = {
        data: { id: Math.floor(Math.random() * 1000), ...requestData }
      };
      
      setMessage({
        text: `Group "${mockResponse.data.name}" created successfully!`,
        type: 'success'
      });
      
      // Update groups list with new group
      setGroups(prevGroups => [...prevGroups, mockResponse.data]);
      
      setFormData({
        user_id: formData.user_id,
        name: '',
        description: ''
      });
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
    
    setIsAddingMember(true);
    
    try {
      // API call would go here
      // await axios.post('/api/addGroupMember', {
      //   groupId: selectedGroup.id,
      //   username: membershipForm.username,
      //   password: membershipForm.password
      // });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setMessage({ 
        text: `User "${membershipForm.username}" added to group "${selectedGroup.name}"`, 
        type: 'success' 
      });
      
      setMembershipForm({
        username: '',
        password: ''
      });
    } catch (error) {
      setMessage({ text: 'Failed to add user to group', type: 'error' });
    } finally {
      setIsAddingMember(false);
    }
  };

  return (
    <div className="space-y-8 p-4">
      {/* Message display */}
      {message.text && (
        <div className={`p-4 rounded-md ${message.type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
          {message.text}
        </div>
      )}
      
      {/* Group listing section */}
      <div className="bg-black shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Existing Groups</h2>
        
        {isFetchingGroups ? (
          <div className="text-center py-4">Loading groups...</div>
        ) : (
          <div className="space-y-4">
            <button 
              onClick={fetchGroups}
              className="bg-blue-100 hover:bg-blue-200 text-blue-700 py-1 px-3 rounded text-sm"
            >
              Refresh Groups
            </button>
            
            {groups.length === 0 ? (
              <p className="text-gray-500">No groups found</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {groups.map(group => (
                  <div 
                    key={group.id}
                    onClick={() => setSelectedGroup(group)}
                    className={`border rounded-md p-4 cursor-pointer transition ${
                      selectedGroup?.id === group.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <h3 className="font-medium">{group.name}</h3>
                    <p className="text-sm text-gray-600">{group.description || 'No description'}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Add user to group section */}
      <div className="bg-black shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Add User to Group</h2>
        
        {!selectedGroup ? (
          <p className="text-amber-600">Please select a group first</p>
        ) : (
          <form onSubmit={handleAddMember} className="space-y-4">
            <div className="mb-2">
              <p className="text-sm font-medium text-gray-700">Selected Group: <span className="font-semibold">{selectedGroup.name}</span></p>
            </div>
            
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">Username/Email</label>
              <input
                type="text"
                id="username"
                name="username"
                value={membershipForm.username}
                onChange={handleMembershipChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter username or email"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={membershipForm.password}
                onChange={handleMembershipChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter password"
              />
            </div>
            
            <button
              type="submit"
              disabled={isAddingMember}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isAddingMember ? 'Adding...' : 'Add to Group'}
            </button>
          </form>
        )}
      </div>
      
      {/* Create group section */}
      <div className="bg-black shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Create New Group</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="user_id" className="block text-sm font-medium text-gray-700">User ID</label>
            <input
              type="text"
              id="user_id"
              name="user_id"
              value={formData.user_id}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your user ID"
            />
          </div>
          
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">Group Name</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter group name"
            />
          </div>
          
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description (optional)</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="3"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter group description"
            ></textarea>
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
          >
            {isLoading ? 'Creating...' : 'Create Group'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default GroupManagement;
