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
    error?: string;
}

export default function FormField({ label, placeholder, value, onChange, id, required, className, error }: FormProps) {
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
                className={cn("mt-1", error && "!border-red-500 focus-visible:ring-red-500")}
            />
            {error &&
                <p className="mt-1 text-sm text-red-500">{error}</p>
            }
        </div>
    );
}