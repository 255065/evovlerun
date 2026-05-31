import * as React from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          "flex h-10 w-full rounded-xl border border-[#1a1612]/12 bg-white/70 px-3.5 py-2 text-sm text-[#1a1612] placeholder:text-[#9a9189] focus-visible:outline-none focus-visible:border-[#dc6b3f] focus-visible:ring-2 focus-visible:ring-[#dc6b3f]/30 focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";

export { Input };
