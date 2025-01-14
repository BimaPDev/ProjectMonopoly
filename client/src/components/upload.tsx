"use client";

import * as React from "react";
import { CalendarIcon, ImageIcon, Loader2, Upload, X } from "lucide-react";
import { Facebook, Instagram, Linkedin, Twitter } from "lucide-react";
import { format } from "date-fns";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion, AnimatePresence } from "framer-motion";

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
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";

const formSchema = z.object({
  title: z.string().min(1, "Title is required"),
  description: z.string(),
  platforms: z.array(z.string()).min(1, "Select at least one platform"),
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
    id: "tiktok",
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
  const [loading, setLoading] = React.useState(false);
  const [preview, setPreview] = React.useState<string>();
  const [dragActive, setDragActive] = React.useState(false);
  const [step, setStep] = React.useState(1);
  const [progress, setProgress] = React.useState(33);
  const fileRef = React.useRef<HTMLInputElement>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: "",
      description: "",
      platforms: [],
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    console.log(values);
    setLoading(false);
    toast({
      title: "Success",
      description: "Your content has been scheduled for posting.",
    });
  }

  function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    handleFile(file);
  }

  function handleFile(file: File | undefined) {
    if (file) {
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
    <div className="container mx-auto py-10">
      <div className="space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Create New Post</h1>
          <p className="text-muted-foreground">
            Upload and schedule your content across multiple platforms
          </p>
        </div>

        <Progress value={progress} className="w-full" />

        <div className="grid gap-8 lg:grid-cols-2">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
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
                              Supports JPG, PNG, MP4 or MOV (max. 100MB)
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
                        name="description"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Description</FormLabel>
                            <FormControl>
                              <Textarea
                                placeholder="Write a detailed description..."
                                className="min-h-[100px] resize-none"
                                {...field}
                              />
                            </FormControl>
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
                        name="platforms"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Platforms</FormLabel>
                            <div className="grid grid-cols-2 gap-4">
                              {socialPlatforms.map((platform) => (
                                <div
                                  key={`platform-${platform.id}`}
                                  className={cn(
                                    "flex cursor-pointer items-center gap-3 rounded-lg border p-4 transition-colors hover:bg-accent",
                                    field.value?.includes(platform.id) &&
                                      "border-primary bg-primary/5"
                                  )}
                                  onClick={() => {
                                    const newValue = field.value?.includes(
                                      platform.id
                                    )
                                      ? field.value.filter(
                                          (id) => id !== platform.id
                                        )
                                      : [...(field.value || []), platform.id];
                                    field.onChange(newValue);
                                  }}
                                >
                                  <div
                                    className={cn(
                                      "flex h-10 w-10 items-center justify-center rounded-full text-white",
                                      platform.color
                                    )}
                                  >
                                    <platform.icon className="h-5 w-5" />
                                  </div>
                                  <span className="font-medium">
                                    {platform.label}
                                  </span>
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
                            <FormLabel>Schedule</FormLabel>
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
                                      : "Pick a date"}
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
                      {loading ? "Scheduling..." : "Schedule Post"}
                    </Button>
                  </div>
                </form>
              </Form>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
