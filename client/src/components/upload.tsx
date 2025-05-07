"use client";

import * as React from "react";
import { CalendarIcon, Loader2, Upload as UploadIcon, X, Info } from "lucide-react";
import { Facebook, Instagram, Linkedin, Twitter } from "lucide-react";
import { format } from "date-fns";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent } from "@/components/ui/card";
import {
  Form,
  FormControl,
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

// Form schema
const formSchema = z.object({
  title: z.string().optional(),
  hashtags: z.string().optional(),
  platform: z.string().min(1, "Platform is required"),
  groupId: z.string().min(1, "Group is required"),
  scheduledDate: z.date().optional(),
});

// Static list of platforms
const socialPlatforms = [
  { id: "instagram", label: "Instagram", icon: Instagram, color: "bg-gradient-to-br from-purple-600 to-pink-500" },
  { id: "facebook",  label: "Facebook",  icon: Facebook,  color: "bg-blue-600" },
  { id: "twitter",   label: "Twitter",   icon: Twitter,   color: "bg-sky-500" },
  { id: "linkedin",  label: "LinkedIn",  icon: Linkedin,  color: "bg-blue-700" },
];

// Shape of a group from your API
interface Group {
  id: number;
  name: string;
  description: string;
}

export default function UploadPage() {
  // UI state
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<string>();
  const [dragActive, setDragActive] = useState(false);
  const [step, setStep] = useState(1);
  const [progress, setProgress] = useState(33);
  const fileRef = React.useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Groups state
  const [groups, setGroups] = useState<Group[]>([]);
  const [groupsLoading, setGroupsLoading] = useState(false);

  // Form setup
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { title: "", hashtags: "", platform: "", groupId: "" },
  });

  // Fetch groups on mount
  React.useEffect(() => {
    async function fetchGroups() {
      const userID = Number(localStorage.getItem("userID"));
      if (!userID) return;

      setGroupsLoading(true);
      try {
        const res = await fetch(`http://localhost:8080/api/groups?userID=${userID}`);
        if (!res.ok) throw new Error(await res.text() || "Failed to fetch groups");
        const data = (await res.json()) as Group[];
        if (!Array.isArray(data)) throw new Error("Invalid response format");
        setGroups(data);
      } catch (err: any) {
        toast({ title: "Error", description: err.message, variant: "destructive" });
      } finally {
        setGroupsLoading(false);
      }
    }
    fetchGroups();
  }, []);

  // File selection helpers
  function handleFile(file?: File) {
    if (!file) return;
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
      setStep(2);
      setProgress(66);
    };
    reader.readAsDataURL(file);
  }
  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    handleFile(e.target.files?.[0]);
  }

  // Submit handler
  async function onSubmit(values: z.infer<typeof formSchema>) {
    setLoading(true);
    if (!selectedFile) {
      toast({ title: "Error", description: "Please select a file", variant: "destructive" });
      setLoading(false);
      return;
    }
    try {
      const userID = localStorage.getItem("userID") || "0";
      const fd = new FormData();
      fd.append("file", selectedFile);
      fd.append("user_id", userID);
      fd.append("group_id", values.groupId);
      fd.append("platform", values.platform);
      if (values.title)    fd.append("title", values.title);
      if (values.hashtags) fd.append("hashtags", values.hashtags);

      const res = await fetch("http://localhost:8080/api/upload", { method: "POST", body: fd });
      if (!res.ok) throw new Error((await res.json().catch(() => null))?.message || res.statusText);
      toast({ title: "Success", description: "Uploaded successfully" });
      form.reset();
      setPreview(undefined);
      setSelectedFile(null);
      setStep(1);
      setProgress(33);
    } catch (err: any) {
      toast({ title: "Upload Failed", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <TooltipProvider>
      <div className="container mx-auto py-10">
        <h1 className="text-3xl font-bold mb-4">Create New Post</h1>
        <Progress value={progress} className="w-full mb-6" />

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Step 1 & 2 omitted for brevity… */}

            {/* Metadata & grouping */}
            <Card>
              <CardContent className="space-y-6">
                {/* Title & Hashtags fields omitted… */}

                {/* Group Picker as radio list */}
                <FormField
                  control={form.control}
                  name="groupId"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Group</FormLabel>
                      <div className="space-y-2 pl-4">
                        {groups.length > 0 ? (
                          groups.map((g) => (
                            <label key={`group-${g.id}`} className="flex items-center">
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
                          ))
                        ) : (
                          <p className="text-sm text-gray-500">No groups to show</p>
                        )}
                      </div>
                      {groupsLoading && (
                        <p className="text-sm text-gray-500 mt-1">Loading your groups…</p>
                      )}
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Platform Picker (dropdown) */}
                <FormField
                  control={form.control}
                  name="platform"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Platform</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a platform" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {socialPlatforms.map((p) => (
                            <SelectItem key={`platform-${p.id}`} value={p.id}>
                              <div className="flex items-center gap-2">
                                <div
                                  className={cn(
                                    "flex h-6 w-6 items-center justify-center rounded-full text-white",
                                    p.color
                                  )}
                                >
                                  <p.icon className="h-3 w-3" />
                                </div>
                                {p.label}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Scheduled Date Picker omitted… */}
              </CardContent>
            </Card>

            <div className="flex justify-end">
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <Loader2 className="animate-spin mr-2 h-4 w-4" />
                ) : (
                  <UploadIcon className="mr-2 h-4 w-4" />
                )}
                {loading ? "Uploading…" : "Upload Post"}
              </Button>
            </div>
          </form>
        </Form>
      </div>
    </TooltipProvider>
  );
}
