"use client";
import { useState } from 'react';
import { GoogleLogin } from "@react-oauth/google";

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [agreeToTerms, setAgreeToTerms] = useState(false);

  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData(prev => ({ ...prev, [id]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Basic validation
    if (!formData.email || !formData.password) {
      setError('Email and password are required');
      setLoading(false);
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (!agreeToTerms) {
      setError('You must agree to the terms and conditions');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8080/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          email: formData.email, 
          password: formData.password 
        }),
      });

      if (!response.ok) {
        throw new Error("Invalid credentials, please try again.");
      }

      const data = await response.json();

      // Store token and session ID
      localStorage.setItem("token", data.token);
      localStorage.setItem("sessionId", data.sessionId);

    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignInSuccess = async (credentialResponse) => {
    console.log("Google Sign-In Success:", credentialResponse);
    
    const googleToken = credentialResponse.credential;
    
    try {
      const response = await fetch("http://127.0.0.1:8080/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          googleToken,
        }),
      });
  
      const data = await response.json();
  
      if (!response.ok) {
        setError(data.message);
        return;
      }
  
      // Store token and session ID
      localStorage.setItem("token", data.token);
      localStorage.setItem("sessionId", data.sessionId);
  
      alert("User registered successfully!");
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred.");
      }
    }
  };

  // Handle Google sign-in error
  const handleGoogleSignInError = () => {
    console.log("Google Sign-In Failed");
  };

  return (
    <div
      className="flex flex-col items-center justify-center min-h-screen text-white px-6"
      style={{
        background: "linear-gradient(-60deg, rgb(72, 72, 72), rgb(0, 0, 0))",
      }}
    >
      <div className="mb-8">
        <img 
          src="https://dogwoodgaming.com/wp-content/uploads/2021/12/dogwood-gaming-logo.png" 
          alt="Dogwood Gaming Logo"
          className="w-64 h-auto"
        />
      </div>
      <h1 className="text-4xl font-extrabold tracking-wide mb-8">Register Below</h1>
      
      <div className="w-full max-w-md bg-black bg-opacity-50 p-8 rounded-lg border border-gray-700 shadow-xl">
        {error && (
          <div className="mb-4 p-3 bg-red-900 border border-red-700 rounded text-white text-sm">
            {error}
          </div>
        )}
        
        <form className="space-y-6" onSubmit={handleSubmit}>
          {/* Google Sign-in Button */}
          <GoogleLogin
            onSuccess={handleGoogleSignInSuccess}
            onError={handleGoogleSignInError}
            className="w-full flex items-center justify-center bg-white text-gray-800 font-medium py-3 px-4 rounded-md hover:bg-gray-100 transition duration-300"
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M21.35,11.1H12.18V13.83H18.69C18.36,15.64 16.96,17.45 14.37,17.45C11.25,17.45 8.89,15.02 8.89,12C8.89,8.98 11.26,6.55 14.38,6.55C16.05,6.55 17.16,7.22 17.84,7.86L19.85,5.82C18.4,4.5 16.7,3.59 14.4,3.59C9.8,3.59 6,7.25 6,12.01C6,16.77 9.8,20.43 14.4,20.43C18.7,20.43 21.7,17.6 21.7,12.35C21.7,11.8 21.64,11.45 21.56,11.1H21.35Z"
              />
            </svg>
            Continue with Google
          </GoogleLogin>
          
          {/* Divider */}
          <div className="relative flex items-center py-2">
            <div className="flex-grow border-t border-gray-700"></div>
            <span className="flex-shrink mx-4 text-gray-400 text-sm">OR</span>
            <div className="flex-grow border-t border-gray-700"></div>
          </div>
          
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1">Email Address</label>
            <input 
              type="email" 
              id="email" 
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent"
              required
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">Password</label>
            <input 
              type="password" 
              id="password" 
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-1">Confirm Password</label>
            <input 
              type="password" 
              id="confirmPassword" 
              value={formData.confirmPassword}
              onChange={handleChange}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent"
              required
            />
          </div>
          
          <div className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id="terms"
                type="checkbox"
                checked={agreeToTerms}
                onChange={() => setAgreeToTerms(!agreeToTerms)}
                className="w-4 h-4 bg-gray-800 border-gray-700 rounded focus:ring-white"
              />
            </div>
            <div className="ml-3 text-sm">
              <label htmlFor="terms" className="text-gray-300">I agree to the <a href="#" className="text-white underline">Terms and Conditions</a></label>
            </div>
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white text-black font-bold py-3 px-4 rounded-md hover:bg-gray-200 transition duration-300 disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'CREATE ACCOUNT'}
          </button>
          
          <div className="text-center mt-4 text-sm text-gray-400">
            Already have an account? <a href="/login" className="text-white underline">Sign in</a>
          </div>
        </form>
      </div>
    </div>
  );
}
