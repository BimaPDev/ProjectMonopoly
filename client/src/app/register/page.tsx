"use client";
import { useState } from 'react';
import { GoogleLogin } from "@react-oauth/google";
import { redirect } from 'react-router-dom';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [signSuccess, setSuccess] = useState(false);
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
      const response = await fetch("http://67.217.246.210:8080/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          username: formData.email,
          email: formData.email, 
          password: formData.password
        }),
      });
  
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Registration failed. Please try again.");
      }
  
      const data = await response.json();
  
      // Store token and session ID
      localStorage.setItem("token", data.token);
      localStorage.setItem("sessionId", data.sessionId);
      
      setSuccess(true);
      setError("Account created please log in");
      redirect("/login");
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
      const response = await fetch("http://67.217.246.210:8080/api/register", {
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
    setError("Google Sign-In failed. Please try again or use email registration.");
  };

  return (
    <div
      className="min-h-screen text-white px-6 py-12 flex items-center justify-center"
      style={{
        background: "linear-gradient(135deg, #212121, #000000)",
        backgroundSize: "cover",
        backgroundAttachment: "fixed"
      }}
    >
      <div className="w-full max-w-md">
       
        <div className="absolute inset-0 bg-black bg-opacity-60 backdrop-blur-sm z-0"></div>
        
        <div className="relative z-10 flex flex-col items-center mb-8">
          <img 
            src="https://dogwoodgaming.com/wp-content/uploads/2021/12/dogwood-gaming-logo.png" 
            alt="Dogwood Gaming Logo"
            className="w-64 h-auto mb-6 drop-shadow-lg"
          />
          <h1 className="text-4xl font-extrabold tracking-wide mb-2 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">
            Join Dogwood Gaming
          </h1>
          <p className="text-gray-300 text-center max-w-sm">
            Create your account to access exclusive gaming tools and resources
          </p>
        </div>
        
        
        
        <div className="relative z-10 bg-gradient-to-b from-gray-900 to-black p-8 rounded-xl border border-gray-800 shadow-2xl backdrop-blur">
          {error && (
            <div className="mb-6 p-4 bg-red-900 bg-opacity-70 border-l-4 border-red-500 rounded text-white text-sm animate-pulse">
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2 text-red-300" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            </div>
          )}
          
          <form className="space-y-6" onSubmit={handleSubmit}>
            
            <GoogleLogin
              onSuccess={handleGoogleSignInSuccess}
              onError={handleGoogleSignInError}
              className="w-full"
              render={(renderProps) => (
                <button
                  onClick={renderProps.onClick}
                  disabled={renderProps.disabled}
                  className="w-full flex items-center justify-center bg-white text-gray-800 font-medium py-3 px-4 rounded-lg hover:bg-gray-100 transition duration-300 transform hover:scale-105"
                >
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M21.35,11.1H12.18V13.83H18.69C18.36,15.64 16.96,17.45 14.37,17.45C11.25,17.45 8.89,15.02 8.89,12C8.89,8.98 11.26,6.55 14.38,6.55C16.05,6.55 17.16,7.22 17.84,7.86L19.85,5.82C18.4,4.5 16.7,3.59 14.4,3.59C9.8,3.59 6,7.25 6,12.01C6,16.77 9.8,20.43 14.4,20.43C18.7,20.43 21.7,17.6 21.7,12.35C21.7,11.8 21.64,11.45 21.56,11.1H21.35Z"
                    />
                  </svg>
                  Continue with Google
                </button>
              )}
            />
            
            {/* Divider */}
            <div className="relative flex items-center py-2">
              <div className="flex-grow border-t border-gray-700"></div>
              <span className="flex-shrink mx-4 text-gray-400 text-sm">OR</span>
              <div className="flex-grow border-t border-gray-700"></div>
            </div>
            
            <div className="space-y-1">
              <label htmlFor="email" className="block text-sm font-medium text-gray-300">Email Address</label>
              <div className="relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                  </svg>
                </div>
                <input 
                  type="email" 
                  id="email" 
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-gray-800 bg-opacity-70 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition duration-200"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>
            
            
            <div className="space-y-1">
              <label htmlFor="password" className="block text-sm font-medium text-gray-300">Password</label>
              <div className="relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <input 
                  type="password" 
                  id="password" 
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-gray-800 bg-opacity-70 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition duration-200"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>
            
            
            <div className="space-y-1">
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300">Confirm Password</label>
              <div className="relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <input 
                  type="password" 
                  id="confirmPassword" 
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-gray-800 bg-opacity-70 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition duration-200"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>
            
            
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="terms"
                  type="checkbox"
                  checked={agreeToTerms}
                  onChange={() => setAgreeToTerms(!agreeToTerms)}
                  className="w-4 h-4 bg-gray-800 border-gray-700 rounded focus:ring-purple-500 text-purple-600 transition duration-200"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="terms" className="text-gray-300">
                  I agree to the <a href="#" className="text-purple-400 hover:text-purple-300 hover:underline transition duration-200">Terms and Conditions</a>
                </label>
              </div>
            </div>
            
            
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-3 px-4 rounded-lg shadow-lg transition duration-300 transform hover:translate-y-1 hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating Account...
                </span>
              ) : 'CREATE ACCOUNT'}
            </button>
            
            {/* {signSuccess &&(
          <div className='relative flex'>
            <div className='bg-black w-full y-full text-center'>
            <span style={{margin:0, color:"red",fontSize:"25px"}}>&#33;</span> <span style={{fontWeight:"bold"}}> Account has been created, please log in.</span>
           </div>
          </div>
        )} */}
            
            <div className="text-center mt-6 text-sm text-gray-400">
              Already have an account? 
              <a href="/login" className="ml-1 text-purple-400 hover:text-purple-300 hover:underline transition duration-200">
                Sign in
              </a>
            </div>
          </form>
        </div>
        
        
        <div className="relative z-10 mt-8 text-center text-gray-500 text-xs">
          <p>© 2025 Dogwood Gaming. All rights reserved.</p>
          <div className="mt-2">
            <a href="https://dogwoodgaming.com/" className="text-gray-400 hover:text-purple-400 hover:underline transition-all duration-200">Home</a>
            <span className="mx-2">|</span>
            <a href="https://dogwoodgaming.com/contact-us/" className="text-gray-400 hover:text-purple-400 hover:underline transition-all duration-200">Contact</a>
          </div>
        </div>
      </div>
    </div>
  );
}