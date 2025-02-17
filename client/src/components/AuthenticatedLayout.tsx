import { Outlet, Routes, Route } from "react-router-dom";
import { AppSidebar } from "./app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "./ui/breadcrumb";
import { Separator } from "./ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "./ui/sidebar";

// Dashboard Pages
import { Dashboard } from "@/components/dashboard";
import Ai from "@/app/Ai/Ai";
import Competitors from "@/app/competitors/page";
import Upload from "@/app/upload/page";
import LiveFeedPage from "@/app/competitors/live/page";

export default function AuthenticatedLayout() {
  return (
    <div className="min-h-screen">
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbPage>Dashboard</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </header>
          <div className="flex-1 min-h-screen w-full space-y-4 p-4 pt-6 bg-background">
            {/* 🔹 Define Dashboard Routes Inside the Authenticated Layout */}
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/posts" element={<Upload />} />
              <Route path="/competitors" element={<Competitors />} />
              <Route path="/competitors/live" element={<LiveFeedPage />} />
              <Route path="/Ai" element={<Ai />} />
            </Routes>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </div>
  );
}
