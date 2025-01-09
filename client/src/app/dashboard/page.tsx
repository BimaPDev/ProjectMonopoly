import { AppSidebar } from "../../components/app-sidebar"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { Line, LineChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer, BarChart, Bar } from "recharts"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Facebook, Twitter, Instagram, ArrowUp, ArrowDown, TrendingUp } from 'lucide-react'
import { ThemeToggle } from "@/components/theme-toggle"

export default function Page() {
  return (
    <SidebarProvider className="h-full">
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
          <div className="flex items-center gap-2 px-4 flex-1">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem className="hidden md:block">
                  <BreadcrumbLink href="#">Dashboard</BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator className="hidden md:block" />
                <BreadcrumbItem>
                  <BreadcrumbPage>Social Media Analytics</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
            <div className="ml-auto">
              <ThemeToggle />
            </div>
          </div>
        </header>
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
          <div className="grid auto-rows-min gap-4 md:grid-cols-3">
            <Card className="col-span-2">
              <CardHeader>
                <CardTitle>Engagement Overview</CardTitle>
                <CardDescription>Total engagement across all platforms</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer
                  config={{
                    likes: {
                      label: "Likes",
                      color: "hsl(var(--chart-1))",
                    },
                    shares: {
                      label: "Shares",
                      color: "hsl(var(--chart-2))",
                    },
                  }}
                  className="aspect-[16/9]"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={[
                        { date: "Mon", likes: 2400, shares: 1500 },
                        { date: "Tue", likes: 3000, shares: 2200 },
                        { date: "Wed", likes: 4500, shares: 3800 },
                        { date: "Thu", likes: 5000, shares: 4200 },
                        { date: "Fri", likes: 6500, shares: 5500 },
                        { date: "Sat", likes: 8000, shares: 6800 },
                        { date: "Sun", likes: 8500, shares: 7200 },
                      ]}
                    >
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="date" className="text-sm" />
                      <YAxis className="text-sm" />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Line
                        type="monotone"
                        dataKey="likes"
                        stroke="var(--color-likes)"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="shares"
                        stroke="var(--color-shares)"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Platform Stats</CardTitle>
                <CardDescription>Current follower count</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4">
                <div className="flex items-center gap-4 rounded-lg border p-4">
                  <div className="rounded-lg bg-blue-100 p-2 dark:bg-blue-900">
                    <Facebook className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">Facebook</p>
                    <p className="text-2xl font-bold">8.5K</p>
                  </div>
                  <div className="flex items-center gap-1 text-green-600">
                    <ArrowUp className="h-4 w-4" />
                    <span className="text-sm">4.2%</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 rounded-lg border p-4">
                  <div className="rounded-lg bg-sky-100 p-2 dark:bg-sky-900">
                    <Twitter className="h-5 w-5 text-sky-600 dark:text-sky-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">Twitter</p>
                    <p className="text-2xl font-bold">12.8K</p>
                  </div>
                  <div className="flex items-center gap-1 text-green-600">
                    <ArrowUp className="h-4 w-4" />
                    <span className="text-sm">6.8%</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 rounded-lg border p-4">
                  <div className="rounded-lg bg-pink-100 p-2 dark:bg-pink-900">
                    <Instagram className="h-5 w-5 text-pink-600 dark:text-pink-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">Instagram</p>
                    <p className="text-2xl font-bold">15.3K</p>
                  </div>
                  <div className="flex items-center gap-1 text-red-600">
                    <ArrowDown className="h-4 w-4" />
                    <span className="text-sm">2.1%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Posts</CardTitle>
              <CardDescription>Posts with highest engagement this week</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Platform</TableHead>
                    <TableHead>Post Content</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Likes</TableHead>
                    <TableHead>Shares</TableHead>
                    <TableHead>Engagement Rate</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Instagram className="h-4 w-4 text-pink-600" />
                        <span>Instagram</span>
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate">New product launch: The future of...</TableCell>
                    <TableCell>2024-01-08</TableCell>
                    <TableCell>3.2K</TableCell>
                    <TableCell>1.8K</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-green-600">
                        <TrendingUp className="h-4 w-4" />
                        8.5%
                      </div>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Twitter className="h-4 w-4 text-sky-600" />
                        <span>Twitter</span>
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate">Breaking: Industry news about...</TableCell>
                    <TableCell>2024-01-07</TableCell>
                    <TableCell>2.8K</TableCell>
                    <TableCell>2.1K</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-green-600">
                        <TrendingUp className="h-4 w-4" />
                        7.2%
                      </div>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Facebook className="h-4 w-4 text-blue-600" />
                        <span>Facebook</span>
                      </div>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate">Customer success story: How we...</TableCell>
                    <TableCell>2024-01-06</TableCell>
                    <TableCell>1.5K</TableCell>
                    <TableCell>985</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-green-600">
                        <TrendingUp className="h-4 w-4" />
                        5.9%
                      </div>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

