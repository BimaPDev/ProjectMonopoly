"use client"

import * as React from "react"
import { useEffect, useState, useRef } from "react"
import { Bot, Send, User, Upload } from "lucide-react"
import { Typewriter, Cursor } from 'react-simple-typewriter'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const models = [
  { id: "DeepSeek", name: "DeepSeek" },
 
]

interface Message {
  role: "user" | "assistant"
  content: string
  attachments?: string[]
}

export function AIPage() {
  const [messages, setMessages] = React.useState<Message[]>([])
  const [input, setInput] = React.useState("")
  const [model, setModel] = React.useState("gpt-4")
  const [isLoading, setIsLoading] = React.useState(false)
  const [messageSent, setMessageSent] = useState(false)
  const [files, setFiles] = useState<File[]>([])
  const messagesEndRef = React.useRef<HTMLDivElement>(null)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  React.useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)
      setFiles(prevFiles => [...prevFiles, ...newFiles])
    }
  }
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
  
    if (!input.trim() && files.length === 0) return;
  
    const formData = new FormData();
    formData.append("prompt", input);
    files.forEach(file => {
      formData.append("files", file); // Make sure this matches the field name in your Go handler
    });
  
    setMessages(prev => [
      ...prev,
      { role: "user", content: input, attachments: files.map(file => file.name) }
    ]);
    setInput("");
    setFiles([]);
    setIsLoading(true);
  
    try {
      // Let fetch set the Content-Type header automatically for FormData
      const response = await fetch("http://localhost:8080/ai/deepseek", {
        method: "POST",
        body: formData,
        // Don't set Content-Type header manually for FormData
      });
  
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Server error:", errorText);
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }
  
      const data = await response.json();
  
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: data.response }
      ]);
    } catch (error) {
      console.error("Error communicating with AI API:", error);
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: "Something went wrong while communicating with the AI." }
      ]);
    } finally {
      setIsLoading(false);
    }
    console.log("FormData contents:");
    for (let pair of formData.entries()) {
    console.log(pair[0] + ': ' + pair[1]);
}
  };

  const removeFile = (fileToRemove: File) => {
    setFiles(files.filter(file => file !== fileToRemove))
  }

  return (
    <div className="flex-1 space-y-5 p-6 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">AI Chat</h2>
        <Select value={model} onValueChange={setModel}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select a model" />
          </SelectTrigger>
          <SelectContent>
            {models.map((model) => (
              <SelectItem key={model.id} value={model.id}>
                {model.name}
              </SelectItem>
            ))}
            <span>More Coming Soon!</span>
          </SelectContent>
        </Select>
      </div>

      <Card className="flex h-[calc(100vh-8rem)] flex-col">
        <CardHeader>
          <CardTitle>Chat Session</CardTitle>
          <CardDescription>
            You are chatting with {models.find((m) => m.id === model)?.name}
          </CardDescription>
        </CardHeader>
        {!input && !messageSent && (
          <div className="flex flex-1 items-center justify-center">
            <span className="text-4xl font-bold">
              <Typewriter
                words={['Welcome To', 'DogWood Gaming\'s', 'Ai Marketing Tool']}
                loop={true}
                cursor
                cursorStyle="|"
                typeSpeed={120}
                deleteSpeed={200}
                delaySpeed={500}
              />
            </span>
          </div>
        )}

        <CardContent className="flex-1 overflow-y-auto">
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex items-start gap-3 ${
                  message.role === 'assistant' ? 'flex-row' : 'flex-row-reverse'
                }`}
              >
                <div
                  className={`rounded-full p-2 ${
                    message.role === 'assistant'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  {message.role === 'assistant' ? (
                    <Bot className="h-4 w-4" />
                  ) : (
                    <User className="h-4 w-4" />
                  )}
                </div>
                <div
                  className={`rounded-lg px-3 py-2 ${
                    message.role === 'assistant'
                      ? 'bg-muted'
                      : 'bg-primary text-primary-foreground'
                  }`}
                >
                  {message.content}
                  {message.attachments && message.attachments.length > 0 && (
                    <div className="mt-2 text-sm">
                      <p className="font-semibold">Attached files:</p>
                      <ul className="list-disc pl-4">
                        {message.attachments.map((file, i) => (
                          <li key={i}>{file}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-primary p-2 text-primary-foreground">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="rounded-lg bg-muted px-3 py-2">Thinking...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </CardContent>
        <CardFooter>
          <form onSubmit={handleSubmit} className="flex w-full flex-col gap-2">
            <div className="flex gap-2">
              <Input
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isLoading}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
              >
                <Upload className="h-4 w-4" />
                <span className="sr-only">Upload files</span>
              </Button>
              <Button type="submit" disabled={isLoading}>
                <Send className="h-4 w-4" />
                <span className="sr-only">Send message</span>
              </Button>
            </div>
            <input
              type="file"
              multiple
              className="hidden"
              onChange={handleFileChange}
              ref={fileInputRef}
            />
            {files.length > 0 && (
              <div className="mt-2">
                <p className="text-sm font-medium">Selected files:</p>
                <div className="mt-1 flex flex-wrap gap-2">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-1 rounded-full bg-muted px-3 py-1 text-sm"
                    >
                      <span>{file.name}</span>
                      <button
                        type="button"
                        onClick={() => removeFile(file)}
                        className="ml-1 text-muted-foreground hover:text-foreground"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </form>
        </CardFooter>
      </Card>
    </div>
  )
}