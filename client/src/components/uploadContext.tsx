import React, { useState } from "react";
import { Button } from "./ui/button";
import { X, Upload,Image, FileText,Trash} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Input } from "@/components/ui/input";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";


interface uploadContextProps{
    token: string;
    groupID: number;
}

export function UploadContext({token, groupID} : uploadContextProps){
    const [files, setFiles] = useState<File[]>([]);
    const [open, setOpen] = useState(false);
    const fileRef = React.useRef<HTMLInputElement>(null);
    const [preview, setPreview] = useState("");
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
    
    
    function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];
        handleFile(file);
    }

    async function handleSubmit(){
        try{
            const formData = new FormData();
            
            // Add all files to form data
            files.forEach((file) => {
                formData.append('file', file);
            });
            
            // Add group_id
            formData.append('group_id', groupID.toString());

            // const res = await fetch(`${import.meta.env.VITE_API_CALL}/api/workshop/upload`,{
            //     method: 'POST',
            //     headers: {
            //         'Authorization': `Bearer ${token}`
            //     },
            //     body: formData
            // });

            // if (!res.ok) {
            //     throw new Error(`Upload failed: ${res.status} ${res.statusText}`);
            // }

            // const result = await res.json();
            console.log('Upload successful:', formData);

        }catch(error: unknown){
            if (error instanceof Error) {
                console.error(error.message);
            } else {
                console.error("An unknown error occurred");
            }
        }finally{
            resetForm();
            setFiles([]);
        }
    }
    const handleDelete = () =>{
        setFiles([])
        resetForm()
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
      // Save the file
      setSelectedFile(file);
      setFiles(prev => [...prev, file]);
      
      // Create preview based on file type
      const reader = new FileReader();
      const extension = file.name.split('.').pop()?.toLowerCase();
      
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      
      // Check if it's an image
      if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension || '')) {
        reader.readAsDataURL(file);
      } 
      // Check if it's a text file
      else if (['txt', 'md', 'js', 'css', 'html', 'json'].includes(extension || '')) {
        reader.readAsText(file);
      }
      // For other files like PDF, DOC - no preview
      else {
        setPreview(`File: ${file.name}\nType: ${file.type}\nSize: ${(file.size / 1024 / 1024).toFixed(2)} MB`);
      }
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
    return(
        <>
            <Button onClick={() => setOpen(true)}>Upload Context</Button>
            
            {open && (
                <div className="fixed z-40 flex items-center justify-center inset-0">
                    {/*blurred background */}
                    <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setOpen(false)}>
                    </div>
                        {/*upload part actual */}
                        <div className="relative p-6 justify-center max-w-md w-full mx-4 bg-black rounded-lg">
                            <div className="flex items-center justify-center ">
                                <h1 className="text-xl text-white font-semibold"> Upload Context</h1>
                                
                            </div>
                            <p className="text-white text-sm mb-3 mt-3"> Upload any relevant information you want the AI to know</p>
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
                        {files && files.length ==0 ?
                        <Input
                          ref={fileRef}
                          type="file"
                          accept=".pdf,.txt,.doc,.docx"
                          className="hidden"
                          onChange={onFileChange}
                        />
                        : ""
                        }
                        
                        {preview ? (
                          <div className="absolute inset-0 rounded-lg overflow-hidden">
                            {selectedFile && ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(
                              selectedFile.name.split('.').pop()?.toLowerCase() || ''
                            ) ? (
                              <img
                                src={preview}
                                alt="Preview"
                                className="object-cover w-full h-full rounded-lg"
                              />
                            ) : (
                              <div className="p-4 bg-gray-50 dark:bg-gray-800 h-full overflow-y-auto">
                                <div className="flex items-center mb-2">
                                  <FileText className="w-4 h-4 mr-2" />
                                  <span className="text-sm font-medium">{selectedFile?.name}</span>
                                </div>
                                <pre className="text-xs text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
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
                                Supports PDF, TXT, DOC, DOCX, PNG, JPG (max. 50MB)
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                      <p className="text-slate-500 text-sm mt-5">Note: If your PDF isn’t properly tagged or contains only images, the extracted information may be incomplete. Running it through OCR or an accessibility tool can help.</p>

                      {files && files.length > 0 && (
                            <div className="pt-2 mt-3 text-sm border-t">
                              <p className="text-xs font-semibold uppercase">Attachments</p>
                              <div className="flex flex-wrap gap-2 mt-1">
                                {files.map((file, i) => (
                                  <div key={i} className="flex w-full items-baseline justify-start px-2 py-1 text-xs rounded-md bg-background/50">
                                    
                                    <span className="flex  gap-3 truncate ">{getFileIcon(file.name)} {file.name} <button className="bg-black" onClick={()=>handleDelete()}>
                                        <span><Trash className="w-4 h-4"></Trash></span>
                                    </button></span>
                                    
                                  </div>
                                  
                                ))}
                                
                              </div>
                            </div>
                          )}
                          
                          {/* Submit Button */}
                          <div className="flex justify-end mt-6 pt-4 border-t border-gray-700">
                            <div className="flex gap-3">
                                
                              <Button 
                                variant="outline" 
                                onClick={() => setOpen(false)}
                              >
                                Cancel
                              </Button>
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
                    
                </div>
                
                )}
        </>
    )
};