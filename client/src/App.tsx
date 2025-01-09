import { Routes, Route } from "react-router-dom"
import Dashboard from "@/app/dashboard/page"
import { ThemeProvider } from "./components/theme-provider"

function App() {
  return (
    <ThemeProvider>
      <div className="min-h-screen h-full">
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </div>
    </ThemeProvider>
  )
}

export default App

