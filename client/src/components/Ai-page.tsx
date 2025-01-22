"use client"

import * as React from "react"
import { useEffect, useState, useRef } from "react";
import { Bot, Send, User } from "lucide-react"
import {Typewriter, Cursor} from 'react-simple-typewriter'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import styled from 'styled-components';
import Pattern from "@/components/ui/Pattern"
const models = [
  { id: "gpt-4", name: "GPT-4" },
  { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo" },
  { id: "claude-2", name: "Claude 2" },
  { id: "palm-2", name: "PaLM 2" },
]

interface Message {
  role: "user" | "assistant"
  content: string
}

export function AIPage() {
  const [input2, setInput2] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [messages, setMessages] = React.useState<Message[]>([])
  const [input, setInput] = React.useState("")
  const [model, setModel] = React.useState("gpt-4")
  const [isLoading, setIsLoading] = React.useState(false)
  const [messageSent, setMessageSent] = useState(false)
  const messagesEndRef = React.useRef<HTMLDivElement>(null)
  
  const handleInputChange = (e) => {
    const value = e.target.value;
    setInput(value); // Update the input value
    setIsTyping(value.length > 0); // Detect typing if the input is not empty
  };
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  React.useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
  
    if (!input.trim()) return;
  
    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setMessageSent(true);
    setIsLoading(true);
  
    try {
      
      const response = await fetch("http://localhost:8080/ai/deepseek", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: input }),
      });
  
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }
  
      const data = await response.json();
  
      
      const aiMessage: Message = {
        role: "assistant",
        content: data.response, 
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error communicating with AI API:", error);
      const errorMessage: Message = {
        role: "assistant",
        content: "Something went wrong while communicating with the AI.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }

    // // Simulate AI response
    // setTimeout(() => {
    //   const aiMessage: Message = {
    //     role: "assistant",
    //     content:
    //       "This is a simulated response. In a real implementation, this would be replaced with an actual API call to the selected AI model.",
    //   }
    //   setMessages((prev) => [...prev, aiMessage])
    //   setIsLoading(false)
      
    // }, 1000)
  };
  
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
          </SelectContent>
        </Select>
      </div>

      <Card className="flex h-[calc(100vh-8rem)] flex-col"
      style={{boxShadow: '0 4px 20px rgba(255, 255, 255, 0.5)'}}>
        <CardHeader>
          <CardTitle>Chat Session</CardTitle>
          <CardDescription>
            You are chatting with {models.find((m) => m.id === model)?.name}
          </CardDescription>
        </CardHeader>
        {!input && !messageSent && (
          <div className="flex flex-1 items-center justify-center">
            <span
              style={{
                fontSize: 35,
                fontWeight: 'bold',
              }}
            >
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

        <CardContent className="flex-1 overflow-y-auto ">
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
          <form onSubmit={handleSubmit} className="flex w-full gap-2">
            <Input
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <Button type="submit" disabled={isLoading}>
              <Send className="h-4 w-4" />
              <span className="sr-only">Send message</span>
            </Button>
          </form>
        </CardFooter>
      </Card>
    </div>
  

  )
}

