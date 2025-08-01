"use client";

import * as React from "react";
import { CalendarIcon, Loader2, Upload, X, Info } from "lucide-react";
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
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import { socialPlatforms } from "@/components/socialPlatforms";
// Updated schema to include group selection
const formSchema = z.object({
  title: z.string().optional(),
  hashtags: z.string().optional(),
  platform: z.array(z.string()).min(1, "Platform is required"),
  groupId: z.number().min(1, "Group is required"),
  scheduledDate: z.date().optional(),
});


export default function UploadPage() {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [step, setStep] = useState(1);
  const [progress, setProgress] = useState(33);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileRef = React.useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [groups, setGroups] = React.useState<Group[]>([]);
  const [groupsLoading, setGroupsLoading] = React.useState(false);
  const [groupEmptyErr, setGroupEmptyErr] = useState(false);
  
  interface Group {
    ID: number;    
    name: string;  
    description: string; 
  }
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: "",
      hashtags: "",
      platform: [],
      scheduledDate: undefined,
      groupId: 0,
    },
  });

  // Fetch user ID first, then fetch groups once we have the ID
  React.useEffect(() => {
    async function fetchGroups() {
      const storedUserID = localStorage.getItem("userID");
      if (!storedUserID) {
        return;
      }
      
      const userID = Number(storedUserID);
      setGroupsLoading(true);
      
      try {
        const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/groups?userID=${userID}`, {
          method: "GET",
          headers: { "Content-Type": "application/json" }
        });
        
        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(errorText || `Failed to fetch groups: ${res.status}`);
        }
        
        const data = await res.json();
        
        if (!Array.isArray(data)) {
          console.error("Expected array response, got:", typeof data);
          throw new Error("Invalid response format from server");
        }
        
        setGroups(data);
        if (data.length == 0) {
          setGroupEmptyErr(true);
        }
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
  }, []);

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setLoading(true);
    console.log("Form values:", values);
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
      formData.append("user_id", localStorage.getItem("userID") || "");
      formData.append("platform", values.platform.join(","));
      formData.append(
        "scheduled_date",
        values.scheduledDate
          ? values.scheduledDate.toISOString()
          : new Date().toLocaleString()
      );
      formData.append("group_id", values.groupId.toString());
      
      if (values.title) {
        formData.append("title", values.title);
      }
      
      if (values.hashtags) {
        formData.append("hashtags", values.hashtags);
      }
      
      // Send request to backend
      const response = await fetch(`${import.meta.env.VITE_API_CALL}/api/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.message || `Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Set upload success state first
      setUploadSuccess(true);
      
      // Show success toast
      toast({
        title: "Success",
        description: "Your content has been uploaded successfully.",
      });
      
      // Wait longer for the toast to be visible before resetting
      await new Promise((resolve) => setTimeout(resolve, 2000));
      
      // Reset everything after successful upload
      resetForm();
      
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

  function resetForm() {
    form.reset();
    setSelectedFile(null);
    setPreview("");
    setStep(1);
    setProgress(33);
    setUploadSuccess(false);
    // Reset file input
    if (fileRef.current) {
      fileRef.current.value = "";
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
        setUploadSuccess(false); // Reset success state when new file is selected
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
      <div className="container py-10 mx-auto">
        <div className="space-y-8">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">Create New Post</h1>
            <p className="text-muted-foreground">
              Upload and schedule your content across multiple platforms. Visit <span className="text-blue-500 underline"><a href="/dashboard/settings">settings</a></span> to add login info before upload.
            </p>
          </div>

          <Progress value={progress} className="w-full" />

          {/* Success Message */}
          {uploadSuccess && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 border border-green-200 rounded-lg bg-green-50"
            >
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800">
                    Upload successful! Your content has been uploaded and scheduled.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

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
                            className="absolute object-cover w-full h-full rounded-lg"
                          />
                        ) : (
                          <div className="flex flex-col items-center justify-center p-4 space-y-4 text-center">
                            <div className="p-4 rounded-full bg-primary/10">
                              <Upload className="w-8 h-8 text-primary" />
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
                            className="absolute z-10 right-2 top-2"
                            onClick={() => {
                              setSelectedFile(null);
                              setPreview("");
                              setStep(1);
                              setProgress(33);
                              setUploadSuccess(false);
                              if (fileRef.current) {
                                fileRef.current.value = "";
                              }
                            }}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                          <img
                            src={preview}
                            alt="Preview"
                            className="object-cover w-full rounded-lg aspect-square"
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
                                      <Info className="w-4 h-4 text-muted-foreground" />
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
                        <FormField
                          control={form.control}
                          name="groupId"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Group</FormLabel>
                              <div className="pl-4 space-y-2">
                                {groups.map((g) => (
                                  <div key={g.ID} className="flex items-center">
                                    <input
                                      type="radio"
                                      id={`group-${g.ID}`}
                                      className="mr-2"
                                      value={g.ID}
                                      checked={field.value === g.ID}
                                      onChange={() => field.onChange(g.ID)}
                                      disabled={groupsLoading}
                                    />
                                    <span>{g.name || "No Groups"}</span>
                                    <span className="block pl-2 text-xs text-zinc-500 dark:text-zinc-400"> ({g.description || "No description"})</span>
                                  </div>
                                ))}
                              </div>
                              {groupEmptyErr && (
                                <p className="mt-1 text-sm text-red-500">
                                  No groups found. Please create a group in the settings.
                                </p>
                              )}
                              
                              {groupsLoading && (
                                <p className="mt-1 text-sm text-gray-500">Loading your groups…</p>
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
                                      <Info className="w-4 h-4 text-muted-foreground" />
                                    </span>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>Choose the social media platforms where you want to publish this content</p>
                                  </TooltipContent>
                                </Tooltip>
                              </div>
                              <div className="space-y-2">
                                {socialPlatforms.map((platform) => (
                                  <div key={platform.id} className="flex items-center space-x-2">
                                    <input
                                      type="checkbox"
                                      id={`platform-${platform.id}`}
                                      className="mr-2"
                                      value={platform.id}
                                      checked={field.value?.includes(platform.id) || false}
                                      onChange={(e) => {
                                        const currentValues = field.value || [];
                                        let newValues;
                                        
                                        if (e.target.checked) {
                                          // Add the platform if checked
                                          newValues = [...currentValues, platform.id];
                                        } else {
                                          // Remove the platform if unchecked
                                          newValues = currentValues.filter(id => id !== platform.id);
                                        }
                                        
                                        field.onChange(newValues);
                                        setProgress(66); // Update progress when platform changes
                                      }}
                                    />
                                    <label 
                                      htmlFor={`platform-${platform.id}`} 
                                      className="flex items-center space-x-2 cursor-pointer"
                                    >
                                      <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full ${platform.color}`}>
                                        <platform.icon className="w-4 h-4 text-white" />
                                      </span>
                                      <span>{platform.id}</span>
                                    </label>
                                  </div>
                                ))}
                              </div>
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
                                      <Info className="w-4 h-4 text-muted-foreground" />
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
                                      <CalendarIcon className="w-4 h-4 mr-2" />
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

                    <div className="flex justify-end space-x-4">
                      {(step === 2 || selectedFile) && (
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => {
                            const confirmReset = window.confirm("Are you sure you want to start over? This will clear all your current progress.");
                            if (confirmReset) {
                              resetForm();
                            }
                          }}
                          disabled={loading}
                        >
                          Start Over
                        </Button>
                      )}
                      <Button type="submit" disabled={loading || !selectedFile} size="lg">
                        {loading && (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
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