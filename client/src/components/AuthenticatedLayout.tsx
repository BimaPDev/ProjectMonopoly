import { Outlet, useLocation } from "react-router-dom";
import { AppSidebar } from "./app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbLink,
  BreadcrumbSeparator,
} from "./ui/breadcrumb";
import { Separator } from "./ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "./ui/sidebar";

export default function AuthenticatedLayout() {
  const location = useLocation();

  // Generate breadcrumbs based on current path
  const getBreadcrumbs = () => {
    const pathSegments = location.pathname.split('/').filter(segment => segment !== '');

    const breadcrumbMap: { [key: string]: string } = {
      dashboard: 'Dashboard',
      posts: 'Posts',
      competitors: 'Competitors',
      live: 'Live Feed',
      ai: 'AI Assistant',
      settings: 'Settings',
      gamecontext: 'Game Context',
      marketing: 'Marketing Generator'
    };

    const breadcrumbs: React.ReactElement[] = [];
    let currentPath = '';

    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const isLast = index === pathSegments.length - 1;
      const displayName = breadcrumbMap[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);

      if (isLast) {
        breadcrumbs.push(
          <BreadcrumbItem key={segment}>
            <BreadcrumbPage>{displayName}</BreadcrumbPage>
          </BreadcrumbItem>
        );
      } else {
        breadcrumbs.push(
          <BreadcrumbItem key={segment}>
            <BreadcrumbLink href={currentPath}>{displayName}</BreadcrumbLink>
          </BreadcrumbItem>
        );
        if (index < pathSegments.length - 1) {
          breadcrumbs.push(<BreadcrumbSeparator key={`sep-${segment}`} />);
        }
      }
    });

    return breadcrumbs;
  };

  return (
    <div className="flex min-h-screen">
      <SidebarProvider>
        <AppSidebar />
        <div className="flex-1">
          <SidebarInset>
            <header className="flex items-center h-16 gap-2 px-4 border-b shrink-0">
              <SidebarTrigger className="-ml-1" />
              <Separator orientation="vertical" className="h-4 mr-2" />
              <Breadcrumb>
                <BreadcrumbList>
                  {getBreadcrumbs()}
                </BreadcrumbList>
              </Breadcrumb>
            </header>
            <div className="p-6">
              {/* 🔹 This is where the current page will be rendered */}
              <Outlet />
            </div>
          </SidebarInset>
        </div>
      </SidebarProvider>
    </div>
  );
}
