import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { GoogleLogin } from "@react-oauth/google"; // Import Google Login

export function LoginForm({ className, ...props }: React.ComponentProps<"div">) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate(); // ✅ Initialize React Router Navigation

  // Handle regular login (email + password)
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      const response = await fetch(`${import.meta.env.VITE_API_CALL}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error("Invalid credentials, please try again.");
      }

      const data = await response.json();

      // ✅ Store token and session ID
      localStorage.setItem("token", data.token);
      localStorage.setItem("sessionId", data.sessionId);

      // ✅ Redirect to the dashboard after successful login
      navigate("/dashboard");

    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred.");
      }
    }
  };

  // Handle Google login
  const handleGoogleLoginSuccess = async (response: any) => {
    const googleToken = response.credential;

    try {
      // Attempt to log in with the Google token
      const loginResponse = await fetch(`${import.meta.env.VITE_API_CALL}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ googleToken }),
      });

      if (!loginResponse.ok) {
        // If login fails (user not found), attempt to register the user
        const registerResponse = await fetch(`${import.meta.env.VITE_API_CALL}/api/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ googleToken }),
        });

        if (!registerResponse.ok) {
          throw new Error("Google login and registration failed.");
        }

        const data = await registerResponse.json();
        localStorage.setItem("token", data.token);
        localStorage.setItem("sessionId", data.sessionId);
        navigate("/dashboard");
        return;
      }

      const data = await loginResponse.json();
      // ✅ Store token and session ID
      localStorage.setItem("token", data.token);
      localStorage.setItem("sessionId", data.sessionId);
      // ✅ Redirect to the dashboard after successful login
      localStorage.setItem("user", JSON.stringify({
        name: data.name,
        email: data.email,
        avatar: data.picture, // URL of the Google profile picture
      }));
      navigate("/dashboard");

    } catch (err) {
      setError("Google login failed. Please try again.");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 animate-gradient bg-gradient"></div>

      {/* Login Form */}
      <div className={cn("relative z-10 flex flex-col gap-6", className)} {...props}>
        <Card className="overflow-hidden border border-gray-800 bg-black text-white shadow-lg w-full max-w-3xl">
          <CardContent className="grid md:grid-cols-2">
            {/* Left Side: Login Form */}
            <form className="p-6 md:p-8 space-y-6" onSubmit={handleLogin}>
              <div className="flex flex-col gap-6">
                <div className="flex flex-col items-center text-center">
                  <h1 className="text-2xl font-bold tracking-wide">Welcome Back</h1>
                  <p className="text-gray-400">Login to your account</p>
                </div>
                <div className="flex justify-center items-center mt-4">
                  <GoogleLogin
                    onSuccess={handleGoogleLoginSuccess}  // Handle Google login success
                    onError={() => setError("Google login failed.")}
                    useOneTap
                    theme="outline"
                  />
                </div>
                <div className="relative flex items-center py-2">
                  <div className="flex-grow border-t border-gray-700"></div>
                  <span className="flex-shrink mx-4 text-gray-400 text-sm">OR</span>
                  <div className="flex-grow border-t border-gray-700"></div>
                </div>
                {error && <p className="text-red-500 text-sm">{error}</p>}
                
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
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
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
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-gray-800 bg-opacity-70 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition duration-200"
                  placeholder="••••••••"
                  required
                />
              </div>
              </div>
                <Button type="submit" className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-3 px-4 rounded-lg shadow-lg transition duration-300 transform hover:translate-y-1 hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed">
                  Login
                </Button>

                <div className="text-center mt-4 text-sm text-gray-400">
                  Don't have an account? <a href="/register" className="text-white underline">Register</a>
                </div>
              </div>
            </form>

            {/* Right Side: Image */}
            <div className="hidden md:block relative py-5">
              <img 
                src="https://i.imgur.com/VmjeljH.png" 
                alt="Login Visual"
                className="w-80 h-80 object-cover"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <style>{`
        
        .bg-gradient {
          background: linear-gradient(0deg,rgb(19, 19, 19),rgb(6, 6, 6));
          background-size: 400% 400%;
        }
      
      `}</style>
      <footer>
      <div className="relative z-10 mt-8 text-center text-gray-500 text-xs">
          <p>© 2025 Dogwood Gaming. All rights reserved.</p>
          <div className="mt-2">
            <a href="https://dogwoodgaming.com/" className="text-gray-400 hover:text-purple-400 hover:underline transition-all duration-200">Home</a>
            <span className="mx-2">|</span>
            <a href="https://dogwoodgaming.com/contact-us/" className="text-gray-400 hover:text-purple-400 hover:underline transition-all duration-200">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
