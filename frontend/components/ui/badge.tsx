import { cn } from "@/lib/utils";

type Tone = "neutral" | "success" | "warn" | "danger" | "info";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-[#1a1612]/8 text-[#5f564d]",
  success: "bg-emerald-100 text-emerald-900",
  warn:    "bg-amber-100   text-amber-900",
  danger:  "bg-[#dc6b3f]/15 text-[#9e4728]",
  info:    "bg-sky-100     text-sky-900",
};

type Props = React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone };

export function Badge({ tone = "neutral", className, ...props }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        toneClasses[tone],
        className,
      )}
      {...props}
    />
  );
}
