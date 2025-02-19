import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function LoginForm({ className, ...props }: React.ComponentProps<"div">) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate(); // ✅ Initialize React Router Navigation

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:8080/api/login", {
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
                {error && <p className="text-red-500 text-sm">{error}</p>}
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-gray-300">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="email@example.com"
                    className="bg-gray-900 text-white border border-gray-700 focus:ring-gray-500 focus:border-white"
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
                    className="bg-gray-900 text-white border border-gray-700 focus:ring-gray-500 focus:border-white"
                    required
                  />
                </div>
                <Button type="submit" className="w-full bg-white text-black font-semibold hover:bg-gray-200">
                  Login
                </Button>
              </div>
            </form>

            {/* Right Side: Image */}
            <div className="hidden md:block relative">
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
        @keyframes gradient {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        .bg-gradient {
          background: linear-gradient(-55deg,rgb(255, 255, 255),rgb(27, 26, 26),rgb(35, 35, 35),rgb(0, 0, 0));
          background-size: 400% 400%;
        }
        .animate-gradient {
          animation: gradient 5s ease;
        }
      `}</style>
    </div>

  );
}
