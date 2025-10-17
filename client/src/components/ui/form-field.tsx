import * as React from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

interface FormProps {
    label: string;
    placeholder?: string;
    value?: string;
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
    id?: string;
    required?: boolean;
    className?: string;
}

export default function FormField({ label, placeholder, value, onChange, id, required, className }: FormProps) {
    return (
        <div className={cn("flex flex-col", className)}>
            <Label htmlFor={id}>
                {label}
                {required && <span className="text-red-500"> *</span>}
            </Label>
            <Input
                id={id}
                placeholder={placeholder}
                value={value}
                onChange={onChange}
                className="mt-1"
            />
        </div>
    );
}