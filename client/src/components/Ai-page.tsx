"use client";

import * as React from "react";
import { useEffect, useState, useRef } from "react";
import { Bot, Send, User, Upload, Loader2, Sparkles, X, FileText, Image } from "lucide-react";
import { Button } from "@/components/ui/button";
import { UploadContext } from "@/components/uploadContext"
import { useGroup } from "./groupContext";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";


const models = [
  { id: "DeepSeek", name: "DeepSeek", icon: "✨" },
  { id: "GPT-4", name: "GPT-4", icon: "🧠" },
  { id: "Claude", name: "Claude", icon: "🌟" },
];

const thinkingMessages = [
  "Analyzing your request...",
  "Consulting the AI minds...",
  "Processing data...",
  "Crafting a response...",
  "Gathering information...",
  "Formulating a plan...",
  "Thinking deeply...",
  "Please wait, the AI is working hard...",
  "Fetching relevant data...",
  "Generating insights...",
];

interface Message {
  role: "user" | "assistant";
  content: string;
  attachments?: string[];
  timestamp: Date;
}

export function AIPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [model, setModel] = useState("DeepSeek");
  const [isLoading, setIsLoading] = useState(false);
  const [messageSent, setMessageSent] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [thinkingMessage, setThinkingMessage] = useState("");
  const [inputFocused, setInputFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const [token, setToken] = useState(localStorage.getItem("token"))
  const { activeGroup } = useGroup()
  const [health, setHealth] = useState(true);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Set focus to input when page loads
    inputRef.current?.focus();
    fetchHealth();
  }, []);
  async function fetchHealth() {
    try {
      const res = await fetch('/health', {
        method: "GET"
      });
      if (!res.ok) {
        setHealth(false);
      }
    } catch (error) {
      console.log(error)
    }
  }
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setFiles((prevFiles) => [...prevFiles, ...newFiles]);
    }
  };

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension || '')) {
      return <Image className="w-4 h-4 mr-1" />;
    } else {
      return <FileText className="w-4 h-4 mr-1" />;
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() && files.length === 0) return;

    // Store the current input and files before clearing
    const currentInput = input;
    const currentFiles = [...files];

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: currentInput,
        attachments: currentFiles.map((file) => file.name),
        timestamp: new Date()
      },
    ]);
    setInput("");
    setFiles([]);
    setIsLoading(true);
    setMessageSent(true);
    setThinkingMessage(
      thinkingMessages[Math.floor(Math.random() * thinkingMessages.length)]
    );


    //         --header 'content-type: application/json' \
    //   --data '{
    //   "group_id": 1,
    //   "question": "Is Bubble Sort acceptable for small arrays in our pipeline? Recommend and justify.",
    //   "limit": 6,
    //   "model": "gemma3:latest",
    //   "mode": "opinion",
    //   "allow_outside": true,
    //   "output": "short memo",
    //   "tone": "neutral"
    // }'

    try {

      // Build conversation history from messages (last 3 exchanges)
      const conversationHistory = messages
        .slice(-6) // Last 6 messages (3 user + 3 assistant)
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }));

      const requestBody = {
        group_id: activeGroup?.ID || 0,
        question: currentInput,
        limit: 6,
        model: import.meta.env.VITE_OLLAMA_MODEL || "gemma3:latest",
        mode: "opinion",
        allow_outside: true,
        output: "concise answer",
        tone: "neutral",
        history: conversationHistory
      };

      const response = await fetch(`/api/workshop/ask`, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Server error:", errorText);
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          timestamp: new Date()
        },
      ]);
    } catch (error) {
      console.error("Error communicating with AI API:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Something went wrong while communicating with the AI. Please try again later.",
          timestamp: new Date()
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const removeFile = (fileToRemove: File) => {
    setFiles(files.filter((file) => file !== fileToRemove));
  };

  const clearChat = () => {
    setMessages([]);
    setMessageSent(false);
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-black">
      <div className="flex flex-col w-full h-full max-w-6xl p-4 mx-auto md:p-6">
        <div className="flex flex-col items-start justify-between gap-4 mb-4 md:flex-row md:items-center">
          <h2 className="flex items-center text-2xl font-bold tracking-tight md:text-3xl">
            <Sparkles className="w-6 h-6 mr-2 text-primary animate-pulse" />
            Dogwood AI Marketing Assistant
          </h2>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-3">
              <UploadContext
                token={token || ""}
                groupID={activeGroup?.ID || 0}

              />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={clearChat}
              className="text-sm"
              disabled={messages.length === 0}
            >
              <X className="w-4 h-4 mr-1" /> Clear Chat
            </Button>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                {models.map((m) => (
                  <SelectItem key={m.id} value={m.id}>
                    <div className="flex items-center">
                      <span className="mr-2">{m.icon}</span>
                      <div>
                        <div>{m.name}</div>

                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <Card className="flex flex-col flex-1 overflow-hidden border-2 shadow-xl bg-card/95 backdrop-blur-sm">
          <CardHeader className="py-3 border-b bg-primary/10">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center text-lg md:text-xl">
                  <Bot className="w-5 h-5 mr-2 text-primary" />
                  Chat with {models.find((m) => m.id === model)?.name} {models.find((m) => m.id === model)?.icon}
                </CardTitle>
              </div>
              <div className="hidden md:block">
                <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-100">
                      <span className={`mr-1 h-1.5 w-1.5 rounded-full ${health? "bg-green-500" : "bg-red-500"}`}></span>
                      {health === true ? "Online" : "Offline"}
                    </span>
              </div>
            </div>
          </CardHeader>

          {!messageSent && messages.length === 0 && (
            <div className="flex items-center justify-center flex-1 bg-dot-pattern bg-opacity-5">
              <div className="max-w-lg p-6 mx-auto text-center border rounded-lg shadow-lg md:p-8 bg-card/80 backdrop-blur-sm">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.5 }}
                >
                  <Sparkles className="w-12 h-12 mx-auto mb-4 text-primary" />
                  <h3 className="mb-2 text-2xl font-bold md:text-3xl">DogWood Gaming's AI Marketing Tool</h3>
                  <p className="mb-6 text-muted-foreground">
                    Your AI assistant for marketing strategy, content creation, and customer engagement
                  </p>
                  <div className="grid grid-cols-1 gap-3 text-left md:grid-cols-2">
                    <div className="p-3 border rounded-lg bg-secondary/10">
                      <p className="mb-1 font-medium">Try asking about:</p>
                      <ul className="space-y-1 text-sm text-muted-foreground">
                        <li>• Marketing strategy for a game launch</li>
                        <li>• Content calendar ideas for social media</li>
                        <li>• Audience targeting recommendations</li>
                      </ul>
                    </div>
                    <div className="p-3 border rounded-lg bg-secondary/10">
                      <p className="mb-1 font-medium">Upload files like:</p>
                      <ul className="space-y-1 text-sm text-muted-foreground">
                        <li>• Market research documents</li>
                        <li>• Campaign performance data</li>
                        <li>• Competitor analysis reports</li>
                      </ul>
                    </div>
                  </div>
                </motion.div>
              </div>
            </div>
          )}

          <CardContent className={cn(
            "flex-1 overflow-y-auto p-4 md:p-6 scrollbar-thin scrollbar-thumb-primary/20 scrollbar-track-transparent",
            (!messageSent && messages.length === 0) && "hidden"
          )}>
            <div className="space-y-6">
              <AnimatePresence>
                {messages.map((message, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className={`flex ${message.role === "assistant" ? "justify-start" : "justify-end"
                      }`}
                  >
                    <div className={`flex items-start gap-3 max-w-[85%] ${message.role === "assistant" ? "flex-row" : "flex-row-reverse"
                      }`}>
                      <div
                        className={`rounded-full p-2 ${message.role === "assistant"
                          ? "bg-primary text-primary-foreground"
                          : "bg-secondary"
                          }`}
                      >
                        {message.role === "assistant" ? (
                          <Bot className="w-4 h-4" />
                        ) : (
                          <User className="w-4 h-4" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center mb-1">
                          <span className={`text-xs font-medium ${message.role === "assistant" ? "text-primary" : "text-secondary"
                            }`}>
                            {message.role === "assistant" ? models.find(m => m.id === model)?.name : "You"}
                          </span>
                          <span className="mx-2 text-xs text-muted-foreground">
                            {formatTimestamp(message.timestamp)}
                          </span>
                        </div>
                        <div
                          className={`rounded-lg px-4 py-3 ${message.role === "assistant"
                            ? "bg-muted/80"
                            : "bg-primary text-primary-foreground"
                            }`}
                        >
                          <div className={`prose prose-sm max-w-none ${message.role === "user" ? "dark:prose-invert" : ""
                            }`}>
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {message.content}
                            </ReactMarkdown>
                          </div>
                          {message.attachments && message.attachments.length > 0 && (
                            <div className="pt-2 mt-3 text-sm border-t">
                              <p className="text-xs font-semibold uppercase">Attachments</p>
                              <div className="flex flex-wrap gap-2 mt-1">
                                {message.attachments.map((file, i) => (
                                  <div key={i} className="flex items-center px-2 py-1 text-xs rounded-md bg-background/50">
                                    {getFileIcon(file)}
                                    <span className="truncate max-w-[200px]">{file}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-full bg-primary text-primary-foreground">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center mb-1">
                        <span className="text-xs font-medium text-primary">
                          {models.find(m => m.id === model)?.name}
                        </span>
                        <span className="mx-2 text-xs text-muted-foreground">
                          {formatTimestamp(new Date())}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-muted/80">
                        <div className="flex items-center gap-2">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }}></div>
                          </div>
                          <span className="text-sm">{thinkingMessage}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </CardContent>

          <CardFooter className="p-3 border-t md:p-4">
            <form onSubmit={handleSubmit} className="flex flex-col w-full gap-3">
              <div className={cn(
                "flex gap-2 transition-all border-2 rounded-lg p-1",
                inputFocused ? "border-primary/50 ring-2 ring-primary/20" : "border-input"
              )}>
                <Input
                  placeholder="Type your message..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onFocus={() => setInputFocused(true)}
                  onBlur={() => setInputFocused(false)}
                  disabled={isLoading}
                  className="flex-1 border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
                  ref={inputRef}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isLoading}
                  className="h-9 w-9 shrink-0"
                >
                  <Upload className="w-4 h-4" />
                  <span className="sr-only">Upload files</span>
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading || (!input.trim() && files.length === 0)}
                  className="px-4 h-9 shrink-0"
                >
                  <Send className="w-4 h-4 mr-2" />
                  <span>Send</span>
                </Button>
              </div>
              <input
                type="file"
                multiple
                className="hidden"
                onChange={handleFileChange}
                ref={fileInputRef}
              />
              <AnimatePresence>
                {files.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="p-2 rounded-lg bg-muted/50">
                      <p className="mb-1 text-xs font-medium">Selected files</p>
                      <div className="flex flex-wrap gap-2">
                        {files.map((file, index) => (
                          <div
                            key={index}
                            className="flex items-center gap-1 px-2 py-1 text-xs rounded-md bg-background"
                          >
                            {getFileIcon(file.name)}
                            <span className="truncate max-w-[150px]">{file.name}</span>
                            <button
                              type="button"
                              onClick={() => removeFile(file)}
                              className="ml-1 text-muted-foreground hover:text-foreground rounded-full hover:bg-muted p-0.5"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </form>
          </CardFooter>
        </Card>
        <div className="flex items-center justify-between mt-2">
          <div className="text-xs font-medium text-muted-foreground">
            DogWood AI can make mistakes. Always verify important information.
          </div>
          <div className="text-xs text-muted-foreground">
            Powered by {model} {models.find(m => m.id === model)?.icon}
          </div>
        </div>
      </div>
    </div>
  );
}