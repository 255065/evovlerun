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
        <Label htmlFor="name">Nøgle-navn</Label>
        <div className="flex gap-2">
          <Input id="name" name="name" placeholder="MacBook Claude Desktop" required maxLength={80} />
          <Button type="submit" disabled={pending}>
            {pending ? "Genererer…" : "Generér nøgle"}
          </Button>
        </div>
        <p className="text-xs text-neutral-500">
          Giv nøglen et navn så du kan kende den senere (fx hvilken enhed eller AI-app der bruger den).
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
            Nøgle oprettet — vi viser den ikke igen
          </p>
          <p className="text-xs text-emerald-800 dark:text-emerald-300">
            Hvis du vælger auto-install nedenfor er nøglen allerede indlejret. Ellers kopiér den manuelt.
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
          Manuel JSON
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
          <strong>Kør én kommando i Terminal.</strong> Scriptet patcher Claude Desktop&apos;s config-fil og genstarter
          appen. Ingen JSON-editing.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <DownloadButton
          filename={filename}
          content={result.install.macos_install_script}
          mimeType="application/x-sh"
          label="Download install-script"
        />
        <span className="text-xs text-neutral-500">…eller copy-paste hele scriptet nedenfor i Terminal.</span>
      </div>

      <CodeBlock content={result.install.macos_install_script} language="bash" />

      <div className="rounded-md bg-neutral-50 p-3 text-xs text-neutral-600 dark:bg-neutral-900/40 dark:text-neutral-400">
        <p className="font-medium text-neutral-700 dark:text-neutral-300">Sådan virker det:</p>
        <ol className="mt-1.5 list-decimal space-y-0.5 pl-4">
          <li>
            Verificerer at <code className="font-mono text-[11px]">{result.install.mcp_server_path}</code> findes
          </li>
          <li>
            Tilføjer <code className="font-mono text-[11px]">evolverun</code> til Claude&apos;s MCP-config (uden at røre
            andre servere)
          </li>
          <li>Genstarter Claude Desktop så den picker den nye config op</li>
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
          Åbn{" "}
          <code className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-xs dark:bg-neutral-800">
            {result.install.claude_config_file_path}
          </code>
        </li>
        <li>
          Indsæt indholdet nedenfor. Hvis filen allerede har <code className="font-mono text-xs">mcpServers</code>, så
          merge bare <code className="font-mono text-xs">evolverun</code> ind.
        </li>
        <li>Genstart Claude Desktop (Cmd+Q og åbn igen).</li>
      </ol>
      <CodeBlock content={result.install.claude_desktop_config_snippet} language="json" />
    </div>
  );
}

function ChatGPTPane({ apiKey }: { apiKey: string }) {
  return (
    <div className="space-y-3 text-sm">
      <p>ChatGPT understøtter ikke MCP direkte endnu. To muligheder:</p>
      <ol className="list-decimal space-y-2 pl-4">
        <li>
          <strong>Custom GPT med Actions</strong> — vi udstiller en HTTP-version af din MCP-server på et hosted endpoint
          (kommer snart). Indtil da: brug Claude Desktop.
        </li>
        <li>
          <strong>Kald API&apos;et direkte</strong> — bygger du dit eget integration, så send din nøgle som{" "}
          <code className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-xs dark:bg-neutral-800">
            Authorization: Bearer {apiKey.slice(0, 12)}…
          </code>{" "}
          mod backend&apos;ens REST-endpoints.
        </li>
      </ol>
      <div className="rounded-md bg-amber-50 p-3 text-xs text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
        <strong>Heads-up:</strong> ChatGPT-connector flowet kommer i næste sprint (HTTP MCP + Anthropic connector
        marketplace listing). Indtil da er Claude Desktop den primære chat-flade.
      </div>
    </div>
  );
}

function ExamplesCard() {
  const samples = [
    "Hvad var min sidste lange løbetur og hvad var min cardiac drift?",
    "Sammenlign min easy pace de sidste 3 måneder. Bliver jeg mere effektiv?",
    "Hvad er min nuværende limiter, og hvad anbefaler du jeg fokuserer på?",
    "Hvilken session har jeg planlagt i morgen, og hvorfor er den prescriberet?",
    "Vis mig min CTL-trend over 12 uger.",
  ];
  return (
    <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-800 dark:bg-neutral-900/40">
      <p className="text-sm font-medium">Prøv at spørge Claude:</p>
      <ul className="mt-2 space-y-1 text-sm text-neutral-700 dark:text-neutral-300">
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
      <span className="ml-1.5">{copied ? "Kopieret" : "Kopiér"}</span>
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
