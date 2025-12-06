import React, { use, useState } from "react";
import { Button } from "./ui/button";
import { X, Upload, Image, FileText, Trash, TriangleAlert } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Input } from "@/components/ui/input";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { useGroup } from "./groupContext";
import { Document, Page, pdfjs } from 'react-pdf';
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;
interface uploadContextProps {
  token: string;
  groupID: number;
}

export function UploadContext({ token, groupID }: uploadContextProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [open, setOpen] = useState(false);
  const fileRef = React.useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [inputToggle, setInputToggle] = useState(false)
  const { activeGroup } = useGroup();
  function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    handleFile(file);
  }
  function toggleInput() {
    setInputToggle(!inputToggle)
  }
  async function handleSubmit() {
    try {
      const formData = new FormData();

      // Add all files to form data
      files.forEach((file) => {
        formData.append('file', file);
      });

      // Add group_id
      formData.append('group_id', groupID.toString());

      const res = await fetch(`/api/workshop/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!res.ok) {
        throw new Error(`Upload failed: ${res.status} ${res.statusText}`);
      }

      const result = await res.json();
      console.log('Upload successful:', formData);

    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error(error.message);
      } else {
        console.error("An unknown error occurred");
      }
    } finally {
      resetForm();
      setFiles([]);
    }
  }
  const handleDelete = (fileName: string) => {
    setFiles(prev => prev.filter(file => file.name != fileName))
    resetForm()
    setInputToggle(false)
  }
  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    if (['pdf', 'txt', 'doc', 'docx'].includes(extension || '')) {
      return <Image className="w-4 h-4 mr-1" />;
    } else {
      return <FileText className="w-4 h-4 mr-1" />;
    }
  };
  function resetForm() {
    setSelectedFile(null);
    setPreview("");
    // Reset file input
    if (fileRef.current) {
      fileRef.current.value = "";
    }
  }
  function handleFile(file: File | undefined) {
    if (file) {
      setSelectedFile(file);
      setFiles(prev => [...prev, file]);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
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

    <>
      <Button onClick={() => setOpen(true)}>Upload Context</Button>

      {open && (
        <div className="fixed inset-0 z-40 flex items-center justify-center">
          {/*blurred background */}
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setOpen(false)}>
          </div>
          {/*upload part actual */}
          <div className="relative justify-center w-full max-w-md p-6 mx-4 bg-black rounded-lg">
            <div className="flex items-center justify-center ">
              <h1 className="text-xl font-semibold text-white"> Upload Context</h1>

            </div>
            <p className="mt-3 mb-3 text-sm text-white"> Upload any relevant information you want the AI to know</p>
            {!activeGroup &&
              <div className="flex gap-2 p-2 border border-red-500 border-dashed">
                <div className=" w-[30px] h-[30px] flex justify-center items-center rounded-lg">

                  <TriangleAlert className="text-yellow-400"></TriangleAlert>
                </div>
                <h1 className="font-semibold">Please select a group to continue </h1>
              </div>
            }
            {activeGroup &&
              <div
                className={cn(
                  "relative flex min-h-[400px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors",
                  dragActive
                    ? "border-primary bg-primary/10"
                    : "border-muted-foreground/25 hover:border-primary hover:bg-primary/5",
                  preview && "border-dashed"
                )}
                onClick={() => fileRef.current?.click()}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                {files ?
                  <Input
                    ref={fileRef}
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    onChange={onFileChange}
                  />
                  : ""
                }

                {inputToggle ? (
                  <div className="absolute inset-0 overflow-hidden rounded-lg">
                    {selectedFile?.name.endsWith('.pdf') ? (
                      <iframe
                        src={preview}
                        className="w-full h-full bg-black"
                        title="PDF Preview"
                      />
                    ) : (
                      <div className="h-full p-4 overflow-y-auto bg-gray-50 dark:bg-gray-800">
                        <div className="flex items-center mb-2">
                          <FileText className="w-4 h-4 mr-2" />
                          <span className="text-sm font-medium">{selectedFile?.name}</span>
                        </div>
                        <pre className="text-xs text-gray-600 whitespace-pre-wrap dark:text-gray-300">
                          {preview}
                        </pre>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center p-4 space-y-4 text-center">
                    <div className="p-4 rounded-full bg-primary/10">
                      <Upload className="w-8 h-8 text-primary" />
                    </div>
                    <div className="space-y-2">
                      <p className="text-lg font-medium">
                        Drop your file here, or click to browse
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Supports PDF ONLY (max. 50MB)
                      </p>
                    </div>
                  </div>
                )}
              </div>



            }


            <p className="mt-5 text-sm text-slate-500">Note: If your PDF isn’t properly tagged or contains only images, the extracted information may be incomplete. Running it through OCR or an accessibility tool can help.</p>

            {files && files.length > 0 && (
              <div>
                <div className="pt-2 mt-3 text-sm border-t">
                  <p className="text-xs font-semibold uppercase">Attachments</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {files.map((file, i) => (
                      <div key={i} className="flex items-baseline justify-start w-full px-2 py-1 text-xs rounded-md bg-background/50">

                        <span className="flex gap-3 truncate ">{getFileIcon(file.name)} {file.name} <button className="bg-black" onClick={() => handleDelete(file.name)}>
                          <span><Trash className="w-4 h-4"></Trash></span>
                        </button></span>

                      </div>

                    ))}

                  </div>
                </div>

                <div className="flex justify-end pt-4 mt-6 border-t border-gray-700">
                  <div className="flex gap-3">

                    <Button
                      variant="outline"
                      onClick={() => setOpen(false)}
                    >
                      Cancel
                    </Button>

                    <Button className="w-[110px]" onClick={() => toggleInput()}> {inputToggle ? "Hide Preview" : "Show Preview"}</Button>
                    <Button
                      onClick={() => {
                        handleSubmit()
                        setOpen(false);
                      }}
                      disabled={files.length === 0}
                    >
                      Upload Context
                    </Button>
                  </div>
                </div>


              </div>

            )}




          </div>

        </div>

      )}
      <div>

      </div>
    </>


  )
};