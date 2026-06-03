"use client";

import { useActionState, useState } from "react";
import { Copy, Check, Download, Terminal, FileJson, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createKeyAction, type CreateKeyState } from "./actions";

const initialState: CreateKeyState = { error: null, newKey: null };

export function KeyForm() {
  const [state, formAction, pending] = useActionState(createKeyAction, initialState);
  return (
    <div className="space-y-6">
      {!state.newKey ? <GenerateForm pending={pending} formAction={formAction} error={state.error} /> : null}
      {state.newKey ? <PostCreate result={state.newKey} /> : null}
    </div>
  );
}

function GenerateForm({
  pending,
  formAction,
  error,
}: {
  pending: boolean;
  formAction: (formData: FormData) => void;
  error: string | null;
}) {
  return (
    <form action={formAction} className="space-y-3">
      <div className="space-y-2">
        <Label htmlFor="name">Key name</Label>
        <div className="flex gap-2">
          <Input id="name" name="name" placeholder="MacBook Claude Desktop" required maxLength={80} />
          <Button type="submit" disabled={pending}>
            {pending ? "Generating…" : "Generate key"}
          </Button>
        </div>
        <p className="text-xs text-neutral-500">
          Give the key a name so you can recognize it later (e.g. which device or AI app uses it).
        </p>
      </div>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}

function PostCreate({ result }: { result: NonNullable<CreateKeyState["newKey"]> }) {
  return (
    <div className="space-y-6">
      <KeyRevealCard apiKey={result.key} />
      <InstallTabs result={result} />
      <ExamplesCard />
    </div>
  );
}

function KeyRevealCard({ apiKey }: { apiKey: string }) {
  return (
    <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/40">
      <div className="flex items-start gap-2">
        <Sparkles className="mt-0.5 h-4 w-4 text-emerald-700 dark:text-emerald-300" />
        <div className="flex-1 space-y-2">
          <p className="text-sm font-medium text-emerald-900 dark:text-emerald-200">
            Key created — we won&apos;t show it again
          </p>
          <p className="text-xs text-emerald-800 dark:text-emerald-300">
            If you choose auto-install below, the key is already embedded. Otherwise copy it manually.
          </p>
          <div className="flex items-center gap-2 pt-1">
            <code className="block flex-1 truncate rounded bg-white px-3 py-2 font-mono text-xs dark:bg-neutral-900">
              {apiKey}
            </code>
            <CopyButton text={apiKey} />
          </div>
        </div>
      </div>
    </div>
  );
}

function InstallTabs({ result }: { result: NonNullable<CreateKeyState["newKey"]> }) {
  const [tab, setTab] = useState<"auto" | "manual" | "chatgpt">("auto");

  return (
    <div className="rounded-lg border border-neutral-200 dark:border-neutral-800">
      <div className="flex border-b border-neutral-200 dark:border-neutral-800">
        <TabButton active={tab === "auto"} onClick={() => setTab("auto")} icon={<Terminal className="h-4 w-4" />}>
          Auto-install (macOS)
        </TabButton>
        <TabButton active={tab === "manual"} onClick={() => setTab("manual")} icon={<FileJson className="h-4 w-4" />}>
          Manual JSON
        </TabButton>
        <TabButton active={tab === "chatgpt"} onClick={() => setTab("chatgpt")} icon={<Sparkles className="h-4 w-4" />}>
          ChatGPT
        </TabButton>
      </div>
      <div className="p-4">
        {tab === "auto" && <AutoInstallPane result={result} />}
        {tab === "manual" && <ManualPane result={result} />}
        {tab === "chatgpt" && <ChatGPTPane apiKey={result.key} />}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  children,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
        active
          ? "border-emerald-600 text-emerald-700 dark:border-emerald-400 dark:text-emerald-300"
          : "border-transparent text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
      }`}
    >
      {icon}
      {children}
    </button>
  );
}

function AutoInstallPane({ result }: { result: NonNullable<CreateKeyState["newKey"]> }) {
  const filename = `install-evolverun-${result.id.slice(0, 8)}.sh`;
  return (
    <div className="space-y-4">
      <div className="space-y-2 text-sm">
        <p>
          <strong>Run one command in Terminal.</strong> The script patches Claude Desktop&apos;s config file and restarts
          the app. No JSON editing.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <DownloadButton
          filename={filename}
          content={result.install.macos_install_script}
          mimeType="application/x-sh"
          label="Download install script"
        />
        <span className="text-xs text-neutral-500">…or copy-paste the whole script below into Terminal.</span>
      </div>

      <CodeBlock content={result.install.macos_install_script} language="bash" />

      <div className="rounded-xl bg-neutral-100 p-3 text-xs text-neutral-600">
        <p className="font-medium text-neutral-700">How it works:</p>
        <ol className="mt-1.5 list-decimal space-y-0.5 pl-4">
          <li>
            Connects Claude Desktop to{" "}
            <code className="font-mono text-[11px]">{result.install.mcp_url}</code> via{" "}
            <code className="font-mono text-[11px]">mcp-remote</code> (needs Node.js — no repo to clone)
          </li>
          <li>
            Adds <code className="font-mono text-[11px]">evolverun</code> to Claude&apos;s MCP config (without touching
            other servers)
          </li>
          <li>Restarts Claude Desktop so it picks up the new config</li>
        </ol>
      </div>
    </div>
  );
}

function ManualPane({ result }: { result: NonNullable<CreateKeyState["newKey"]> }) {
  return (
    <div className="space-y-4 text-sm">
      <ol className="list-decimal space-y-2 pl-4">
        <li>
          Open{" "}
          <code className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-xs">
            {result.install.claude_config_file_path}
          </code>
        </li>
        <li>
          Paste the content below. If the file already has <code className="font-mono text-xs">mcpServers</code>, just
          merge <code className="font-mono text-xs">evolverun</code> in.
        </li>
        <li>Restart Claude Desktop (Cmd+Q and open again).</li>
      </ol>
      <CodeBlock content={result.install.claude_desktop_config_snippet} language="json" />
    </div>
  );
}

function ChatGPTPane({ apiKey }: { apiKey: string }) {
  return (
    <div className="space-y-3 text-sm">
      <p>ChatGPT doesn&apos;t support MCP directly yet. Two options:</p>
      <ol className="list-decimal space-y-2 pl-4">
        <li>
          <strong>Custom GPT with Actions</strong> — we expose an HTTP version of your MCP server on a hosted endpoint
          (coming soon). Until then: use Claude Desktop.
        </li>
        <li>
          <strong>Call the API directly</strong> — if you build your own integration, send your key as{" "}
          <code className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-xs">
            Authorization: Bearer {apiKey.slice(0, 12)}…
          </code>{" "}
          against the backend&apos;s REST endpoints.
        </li>
      </ol>
      <div className="rounded-xl bg-amber-50 p-3 text-xs text-amber-900">
        <strong>Heads-up:</strong> the ChatGPT connector flow is coming next sprint (HTTP MCP + Anthropic connector
        marketplace listing). Until then, Claude Desktop is the primary chat surface.
      </div>
    </div>
  );
}

function ExamplesCard() {
  const samples = [
    "What was my last long run and what was my cardiac drift?",
    "Compare my easy pace over the last 3 months. Am I getting more efficient?",
    "What's my current limiter, and what do you recommend I focus on?",
    "What session do I have planned tomorrow, and why is it prescribed?",
    "Show me my CTL trend over 12 weeks.",
  ];
  return (
    <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-4">
      <p className="text-sm font-medium">Try asking Claude:</p>
      <ul className="mt-2 space-y-1 text-sm text-neutral-700">
        {samples.map((s, i) => (
          <li key={i} className="flex gap-2">
            <span className="text-neutral-400">›</span>
            <span className="italic">{s}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ─── Reusable primitives ──────────────────────────────────────────

function CodeBlock({ content, language }: { content: string; language: string }) {
  return (
    <div className="relative">
      <pre className="overflow-x-auto rounded-md bg-neutral-950 p-4 pr-12 text-xs text-neutral-100">
        <code data-language={language}>{content}</code>
      </pre>
      <div className="absolute right-2 top-2">
        <CopyButton text={content} />
      </div>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1800);
      }}
    >
      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
      <span className="ml-1.5">{copied ? "Copied" : "Copy"}</span>
    </Button>
  );
}

function DownloadButton({
  filename,
  content,
  mimeType,
  label,
}: {
  filename: string;
  content: string;
  mimeType: string;
  label: string;
}) {
  return (
    <Button
      type="button"
      onClick={() => {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
      }}
    >
      <Download className="mr-1.5 h-4 w-4" />
      {label}
    </Button>
  );
}
