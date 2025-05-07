"use client";

import * as React from "react";
import { CalendarIcon, ImageIcon, Loader2, Upload, X, Info } from "lucide-react";
import { Facebook, Instagram, Linkedin, Twitter } from "lucide-react";
import { format } from "date-fns";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";

// Updated schema to include group selection
const formSchema = z.object({
  title: z.string().optional(),
  hashtags: z.string().optional(),
  platform: z.string().min(1, "Platform is required"),
  groupId: z.string().min(1, "Group is required"),
  scheduledDate: z.date().optional(),
});

const socialPlatforms = [
  {
    id: "instagram",
    label: "Instagram",
    icon: Instagram,
    color: "bg-gradient-to-br from-purple-600 to-pink-500",
  },
  {
    id: "facebook",
    label: "Facebook",
    icon: Facebook,
    color: "bg-blue-600",
  },
  {
    id: "twitter",
    label: "Twitter",
    icon: Twitter,
    color: "bg-sky-500",
  },
  {
    id: "linkedin",
    label: "LinkedIn",
    icon: Linkedin,
    color: "bg-blue-700",
  },
];

export default function UploadPage() {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [step, setStep] = useState(1);
  const [progress, setProgress] = useState(33);
  const fileRef = React.useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [groups, setGroups] = React.useState<{ id: string; name: string }[]>([]);
  const [groupsLoading, setGroupsLoading] = React.useState(false);
  const [userID, setUserID] = React.useState(0);
  const [groupEmptyErr, setGroupEmptyErr] = useState(false);
  
  interface Group {
    id: number;
    name: string;
    description: string;
  }
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: "",
      hashtags: "",
      platform: "",
      groupId: "",
    },
  });
// Fetch user ID first, then fetch groups once we have the ID
React.useEffect(() => {
  async function fetchGroups() {
    const userID = Number(localStorage.getItem("userID"));
    if (!userID) {
      console.log("Cannot fetch groups: userID is undefined");
      return;
    }else
    
    setGroupsLoading(true);
    try {
      console.log(`Fetching groups for user ${userID}...`);
      const res = await fetch(`http://localhost:8080/api/groups?userID=${userID}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" }
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || "Failed to fetch groups");
      }
      
      const data = await res.json();
     
      
      if (!Array.isArray(data)) {
        console.error("Expected array response, got:", typeof data);
        throw new Error("Invalid response format from server");
      }
      
      setGroups(data);
    } catch (error) {
      console.error("Error fetching groups:", error);
      toast({
        title: "Error",
        description: "Failed to load your groups. Please try again.",
        variant: "destructive",
      });
    } finally {
      setGroupsLoading(false);
    }
  }
  fetchGroups();
}, []); // No dependency on userID anymore
  async function onSubmit(values: z.infer<typeof formSchema>) {
    setLoading(true);
    
    try {
      // Check if file exists
      if (!selectedFile) {
        toast({
          title: "Error",
          description: "Please select a file to upload",
          variant: "destructive",
        });
        setLoading(false);
        return;
      }

      // Create FormData to match the expected format in your Go handler
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("user_id", parseInt(values.platform, 10).toString());
      formData.append("platform", values.platform);
      formData.append("group_id", values.groupId);
      
      if (values.title) {
        formData.append("title", values.title);
      }
      
      if (values.hashtags) {
        formData.append("hashtags", values.hashtags);
      }
      
      // Send request to backend
      const response = await fetch("http://localhost:8080/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.message || `Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      toast({
        title: "Success",
        description: "Your content has been uploaded successfully.",
      });
      
      //Reset the form on success if desired
      form.reset();
      setPreview(undefined);
      setSelectedFile(null);
      setStep(1);
      setProgress(33);
      
    } catch (error) {
      console.error("Upload error:", error);
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Something went wrong",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }

  function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    handleFile(file);
  }

  function handleFile(file: File | undefined) {
    if (file) {
      // Save the file
      setSelectedFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
        setStep(2);
        setProgress(66);
      };
      reader.readAsDataURL(file);
    }
  }

  
  function handleDrag(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }

  return (
    <TooltipProvider>
      <div className="container mx-auto py-10">
        <div className="space-y-8">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">Create New Post</h1>
            <p className="text-muted-foreground">
              Upload and schedule your content across multiple platforms. Visit <span className="text-blue-500 underline"><a href="/dashboard/settings">settings</a></span> to add login info before upload.
            </p>
          </div>

          <Progress value={progress} className="w-full" />

          <div className="grid gap-8 lg:grid-cols-2">
            <AnimatePresence mode="sync">
              {step === 1 && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                  className="flex flex-col gap-6"
                >
                  <Card>
                    <CardContent className="p-6">
                      <div
                        className={cn(
                          "relative flex min-h-[400px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors",
                          dragActive
                            ? "border-primary bg-primary/10"
                            : "border-muted-foreground/25 hover:border-primary hover:bg-primary/5",
                          preview && "border-none"
                        )}
                        onClick={() => fileRef.current?.click()}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                      >
                        <Input
                          ref={fileRef}
                          type="file"
                          accept="image/*,video/*"
                          className="hidden"
                          onChange={onFileChange}
                        />
                        {preview ? (
                          <img
                            src={preview}
                            alt="Preview"
                            className="absolute h-full w-full rounded-lg object-cover"
                          />
                        ) : (
                          <div className="flex flex-col items-center justify-center space-y-4 p-4 text-center">
                            <div className="rounded-full bg-primary/10 p-4">
                              <Upload className="h-8 w-8 text-primary" />
                            </div>
                            <div className="space-y-2">
                              <p className="text-lg font-medium">
                                Drop your image here, or click to browse
                              </p>
                              <p className="text-sm text-muted-foreground">
                                Supports JPG, PNG, MP4 or MOV (max. 50MB)
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              {step === 2 && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <Card className="relative">
                    <CardContent className="p-6">
                      {preview && (
                        <>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="absolute right-2 top-2 z-10"
                            onClick={() => {
                              setPreview(undefined);
                              setSelectedFile(null);
                              setStep(1);
                              setProgress(33);
                            }}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                          <img
                            src={preview}
                            alt="Preview"
                            className="aspect-square w-full rounded-lg object-cover"
                          />
                        </>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              <motion.div
                key="form"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-6"
              >
                <Form {...form}>
                  <form
                    onSubmit={form.handleSubmit(onSubmit)}
                    className="space-y-6"
                  >
                    <Card>
                      <CardContent className="p-6 space-y-6">
                        <FormField
                          control={form.control}
                        
                          name="title"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Title</FormLabel>
                              <FormControl>
                                <Input
                                  placeholder="Enter a title for your post"
                                  {...field}
                                />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        <FormField
                          control={form.control}
                      
                          name="hashtags"
                          render={({ field }) => (
                            <FormItem>
                              <div className="flex items-center space-x-2">
                                <FormLabel>Hashtags</FormLabel>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <span className="cursor-help">
                                      <Info className="h-4 w-4 text-muted-foreground" />
                                    </span>
                                  </TooltipTrigger>
                                  <TooltipContent className="max-w-xs">
                                    <p>Add hashtags to increase the visibility of your post. Separate hashtags with spaces (e.g. #trending #viral)</p>
                                  </TooltipContent>
                                </Tooltip>
                              </div>
                              <FormControl>
                                <Textarea
                                  placeholder="Add hashtags separated by spaces (e.g. #trending #viral)"
                                  className="min-h-[100px] resize-none"
                                  {...field}
                                />
                              </FormControl>
                              <FormDescription>
                                Add hashtags to increase visibility of your post
                              </FormDescription>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-6 space-y-6">
                        {/* Group selection with tooltip */}
                        <FormField
                          control={form.control}
                          name="groupId"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Group</FormLabel>
                              <div className="space-y-2 pl-4">
                                {groups.map((g) => (
                                  <label key={g.id} className="flex items-center">
                                    <input
                                      type="radio"
                                      className="mr-2"
                                      value={String(g.id)}
                                      checked={field.value === String(g.id)}
                                      onChange={() => field.onChange(String(g.id))}
                                      disabled={groupsLoading}
                                    />
                                    <span>{g.name}</span>
                                  </label>
                                ))}
                              </div>
                            
                              {groupsLoading && (
                                <p className="text-sm text-gray-500 mt-1">Loading your groups…</p>
                              )}

                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="platform"
                          render={({ field }) => (
                            <FormItem>
                              <div className="flex items-center space-x-2">
                                <FormLabel>Platform</FormLabel>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <span className="cursor-help">
                                      <Info className="h-4 w-4 text-muted-foreground" />
                                    </span>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>Choose the social media platform where you want to publish this content</p>
                                  </TooltipContent>
                                </Tooltip>
                              </div>
                              <Select 
                                onValueChange={field.onChange} 
                                defaultValue={field.value}
                              >
                                <FormControl>
                                  <SelectTrigger>
                                    <SelectValue placeholder="Select a platform" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {socialPlatforms.map((platform) => (
                                    <SelectItem 
                                      key={platform.id} 
                                      value={platform.id}
                                    >
                                      <div className="flex items-center gap-2">
                                        <div
                                          className={cn(
                                            "flex h-6 w-6 items-center justify-center rounded-full text-white",
                                            platform.color
                                          )}
                                        >
                                          <platform.icon className="h-3 w-3" />
                                        </div>
                                        {platform.label}
                                      </div>
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="scheduledDate"
                          render={({ field }) => (
                            <FormItem className="flex flex-col">
                              <div className="flex items-center space-x-2">
                                <FormLabel>Schedule (Optional)</FormLabel>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <span className="cursor-help">
                                      <Info className="h-4 w-4 text-muted-foreground" />
                                    </span>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>Choose a future date to schedule your post automatically</p>
                                  </TooltipContent>
                                </Tooltip>
                              </div>
                              <Popover>
                                <PopoverTrigger asChild>
                                  <FormControl>
                                    <Button
                                      variant={"outline"}
                                      className={cn(
                                        "w-full pl-3 text-left font-normal",
                                        !field.value && "text-muted-foreground"
                                      )}
                                    >
                                      <CalendarIcon className="mr-2 h-4 w-4" />
                                      {field.value
                                        ? format(field.value, "PPP")
                                        : "Pick a date (optional)"}
                                    </Button>
                                  </FormControl>
                                </PopoverTrigger>
                                <PopoverContent
                                  className="w-auto p-0"
                                  align="start"
                                >
                                  <Calendar
                                    mode="single"
                                    selected={field.value}
                                    onSelect={(date) => {
                                      field.onChange(date);
                                      setProgress(100);
                                    }}
                                    initialFocus
                                  />
                                </PopoverContent>
                              </Popover>
                              <FormDescription>
                                Schedule your post for a future date (optional)
                              </FormDescription>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </CardContent>
                    </Card>

                    <div className="flex justify-end">
                      <Button type="submit" disabled={loading} size="lg">
                        {loading && (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        )}
                        {loading ? "Uploading..." : "Upload Post"}
                      </Button>
                    </div>
                  </form>
                </Form>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
