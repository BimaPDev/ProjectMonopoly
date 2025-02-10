import { ThemeProvider as NextThemesProvider } from "next-themes";
import { AppSidebar } from "./components/app-sidebar";
import { Dashboard } from "./components/dashboard";
import Ai from "./app/Ai/Ai";
import Competitors from "@/app/competitors/page"; // Example of another page
import Upload from "@/app/upload/page"; // Example of another page
import LiveFeedPage from "@/app/competitors/live/page"; // Example of another page
import LoginPage from "./app/login/page";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "./components/ui/breadcrumb";
import { Separator } from "./components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "./components/ui/sidebar";
import { Routes, Route } from "react-router-dom";

function App() {
  return (
    <NextThemesProvider attribute="class" defaultTheme="system" enableSystem>
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
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/posts" element={<Upload />} />
                <Route path="/competitors" element={<Competitors />} />
                <Route path="/competitors/live" element={<LiveFeedPage />} />
                <Route path="/Ai" element={<Ai/>}/>
                <Route path="/login" element={<LoginPage/>}/>
              </Routes>
            </div>
          </SidebarInset>
        </SidebarProvider>
      </div>
    </NextThemesProvider>
  );
}

export default App;
