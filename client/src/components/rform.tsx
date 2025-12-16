import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { GoogleLogin } from "@react-oauth/google"; // Import Google Login

export function LoginForm({ className, ...props }: React.ComponentProps<"div">) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate(); // ✅ Initialize React Router Navigation

  // Handle regular login (email + password)
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      const response = await fetch(`/api/login`, {
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
      localStorage.setItem("username",)
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
      const loginResponse = await fetch("http://127.0.0.1:8080/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ googleToken }),
      });

      if (!loginResponse.ok) {
        throw new Error("Google login failed.");
      }

      const data = await loginResponse.json();

      // ✅ Store token and session ID
      localStorage.setItem("token", data.token);
      localStorage.setItem("sessionId", data.sessionId);

      // ✅ Redirect to the dashboard after successful login
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
        <Card className="w-full max-w-3xl overflow-hidden text-white bg-black border border-gray-800 shadow-lg">
          <CardContent className="grid md:grid-cols-2">
            {/* Left Side: Login Form */}
            <form className="p-6 space-y-6 md:p-8" onSubmit={handleLogin}>
              <div className="flex flex-col gap-6">
                <div className="flex flex-col items-center text-center">
                  <h1 className="text-2xl font-bold tracking-wide">Welcome Back</h1>
                  <p className="text-gray-400">Login to your account</p>
                </div>
                {error && <p className="text-sm text-red-500">{error}</p>}
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-gray-300">Username</Label>
                  <Input
                  id="username"
                  type="text"
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Username"
                  className="text-white bg-gray-900 border border-gray-700 focus:ring-gray-500 focus:border-white"
                  required
                  >
                  </Input>
                  <Label htmlFor="email" className="text-gray-300">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="email@example.com"
                    className="text-white bg-gray-900 border border-gray-700 focus:ring-gray-500 focus:border-white"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-gray-300">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    placeholder="Enter your password"
                    onChange={(e) => setPassword(e.target.value)}
                    className="text-white bg-gray-900 border border-gray-700 focus:ring-gray-500 focus:border-white"
                    required
                  />
                </div>
                <Button type="submit" className="w-full font-semibold text-black bg-white hover:bg-gray-200">
                  Login
                </Button>

                {/* Google Login Button */}
                <div className="flex items-center justify-center mt-4">
                  <GoogleLogin
                    onSuccess={handleGoogleLoginSuccess}  // Handle Google login success
                    onError={() => setError("Google login failed.")}
                    useOneTap
                    theme="outline"
                  />
                </div>
              </div>
            </form>

            {/* Right Side: Image */}
            <div className="relative hidden py-5 md:block">
              <img 
                src="https://i.imgur.com/VmjeljH.png" 
                alt="Login Visual"
                className="object-cover w-80 h-80"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <style>{`
        @keyframes gradient {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        .bg-gradient {
          background: linear-gradient(-55deg,rgb(255, 255, 255),rgb(27, 26, 26),rgb(215, 181, 249),rgb(0, 0, 0));
          background-size: 400% 400%;
        }
        .animate-gradient {
          animation: gradient 5s;
        }
      `}</style>
    </div>
  );
}
