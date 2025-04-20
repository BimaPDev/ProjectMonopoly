import React, { useState } from 'react';
import axios from 'axios';

const CreateGroupSettings = () => {
  const [formData, setFormData] = useState({
    user_id: '',
    name: '',
    description: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
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
      const response = await axios.post('/createGroup', requestData);
      setMessage({ 
        text: `Group "${response.data.name}" created successfully!`, 
        type: 'success' 
      });
      
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

  return (
    <div className="max-w-lg mx-auto p-8 bg-black text-white border border-gray-700">
      <h2 className="text-xl font-normal mb-6 uppercase tracking-wider">Create New Group</h2>
      
      {message.text && (
        <div className={`p-3 mb-4 border ${message.type === 'success' ? 'border-white text-green-300' : 'border-red-500 text-red-300'}`}>
          {message.text}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="user_id" className="block text-sm uppercase tracking-wider mb-1 text-gray-300">
            User ID
          </label>
          <input
            type="number"
            id="user_id"
            name="user_id"
            value={formData.user_id}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-600 bg-black text-white focus:outline-none focus:border-white"
            required
          />
        </div>
        
        <div>
          <label htmlFor="name" className="block text-sm uppercase tracking-wider mb-1 text-gray-300">
            Group Name
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-600 bg-black text-white focus:outline-none focus:border-white"
            required
          />
        </div>
        
        
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full py-3 px-4 text-sm uppercase tracking-wider font-medium
            ${isLoading ? 'bg-gray-800 text-gray-500 cursor-not-allowed' : 'bg-white text-black hover:bg-gray-200'}`}
        >
          {isLoading ? 'Creating...' : 'Create Group'}
        </button>
      </form>
    </div>
  );
};

export default CreateGroupSettings;