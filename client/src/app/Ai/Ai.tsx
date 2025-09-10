import { AIPage } from "@/components/Ai-page"
import { useState } from "react"

export default function Page() {
  const [files, setFiles] = useState<File[]>([]);
  
  return (
    <div className="flex flex-col h-screen">
      
      <AIPage />
    </div>
  )
}