import { cn } from "@/lib/utils";

type Tone = "neutral" | "success" | "warn" | "danger" | "info";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200",
  success: "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-200",
  warn:    "bg-amber-100   text-amber-900   dark:bg-amber-900/40   dark:text-amber-200",
  danger:  "bg-red-100     text-red-900     dark:bg-red-900/40     dark:text-red-200",
  info:    "bg-sky-100     text-sky-900     dark:bg-sky-900/40     dark:text-sky-200",
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
