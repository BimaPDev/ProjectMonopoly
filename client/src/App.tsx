/*
import { ThemeProvider as NextThemesProvider } from "next-themes";
//import { Routes, Route } from "react-router-dom";
//import ProtectedRoute from "./components/ProtectedRoute";

// Public Pages (No Dashboard UI)
//import LandingPage from "@/app/landing/page";
//import LoginPage from "./app/login/page";

// Dashboard Layout (Only for Logged-in Users)
//import AuthenticatedLayout from "./components/AuthenticatedLayout";
import { Dashboard } from "./components/dashboard";
import Ai from "./app/Ai/Ai";
import Competitors from "@/app/competitors/page";
import Upload from "@/app/upload/page";
import LiveFeedPage from "@/app/competitors/live/page";

function App() {
  return (
    <NextThemesProvider attribute="class" defaultTheme="system" enableSystem>
      <Routes>
        //{ 🔹 Public Routes (No Sidebar) }
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />

        //{ 🔹 Protected Routes (Authenticated Layout + Sidebar) }
        <Route
          path="/dashboard/*"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout />
            </ProtectedRoute>
          }
        />
      </Routes>
    </NextThemesProvider>
  );
}

export default App;
*/

import { Routes, Route } from "react-router-dom";
import { ThemeProvider as NextThemesProvider } from "next-themes";

// Public Pages
import LandingPage from "@/app/landing/page";
import LoginPage from "@/app/login/page";

// Authenticated Dashboard Layout
import AuthenticatedLayout from "@/components/AuthenticatedLayout";
import {Dashboard} from "@/components/dashboard";
import Upload from "@/app/upload/page";
import Competitors from "@/app/competitors/page";
import LiveFeedPage from "@/app/competitors/live/page";
import Ai from "@/app/Ai/Ai";
import ProtectedRoute from "@/components/ProtectedRoute";

function App() {
  return (
    <NextThemesProvider attribute="class" defaultTheme="system" enableSystem>
      <Routes>
        {/* 🔹 Public Routes (No Authentication) */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />

        {/* 🔒 Protected Dashboard Routes */}
        <Route element={<ProtectedRoute><AuthenticatedLayout /></ProtectedRoute>}>
          {/* 🔹 Dashboard Routes */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/posts" element={<Upload />} />
          <Route path="/dashboard/competitors" element={<Competitors />} />
          <Route path="/dashboard/competitors/live" element={<LiveFeedPage />} />
          <Route path="/dashboard/ai" element={<Ai />} />
        </Route>

        {/* 🔹 Catch-all Route for 404s */}
        <Route path="*" element={<div>404 Page Not Found</div>} />
      </Routes>
    </NextThemesProvider>
  );
}

export default App;