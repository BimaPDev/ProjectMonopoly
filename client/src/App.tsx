import { Routes, Route } from "react-router-dom";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { GoogleOAuthProvider } from "@react-oauth/google";

// Public Pages
import LandingPage from "@/app/landing/page";
import LoginPage from "@/app/login/page";
import RegisterPage from "@/app/register/page";

// Authenticated Dashboard Layout
import AuthenticatedLayout from "@/components/AuthenticatedLayout";
import { Dashboard } from "@/components/dashboard";
import Upload from "@/app/upload/page";
import Competitors from "@/app/competitors/page";
import LiveFeedPage from "@/app/competitors/live/page";
import Ai from "@/app/Ai/Ai";
import ProtectedRoute from "@/components/ProtectedRoute";
import Test from "@/app/test/page";

// Add your Google Client ID here
const googleClientId = "1054535744463-vofp68rffke3c3m9r1o4vaq6ss0iggt1.apps.googleusercontent.com"

function App() {
  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <NextThemesProvider attribute="class" defaultTheme="system" enableSystem>
        <Routes>
          {/* 🔹 Public Routes (No Authentication) */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* 🔒 Protected Dashboard Routes */}
          <Route element={<ProtectedRoute><AuthenticatedLayout /></ProtectedRoute>}>
            {/* 🔹 Dashboard Routes */}
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/dashboard/posts" element={<Upload />} />
            <Route path="/dashboard/competitors" element={<Competitors />} />
            <Route path="/dashboard/competitors/live" element={<LiveFeedPage />} />
            <Route path="/dashboard/ai" element={<Ai />} />
            <Route path="/dashboard/test" element={<Test />} />
          </Route>

          {/* 🔹 Catch-all Route for 404s */}
          <Route path="*" element={<div>404 Page Not Found</div>} />
        </Routes>
      </NextThemesProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
