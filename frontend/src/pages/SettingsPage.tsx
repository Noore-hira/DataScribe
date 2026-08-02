import { Settings as SettingsIcon } from 'lucide-react';
import { Separator } from '@/components/ui/separator';
import { ApiKeyInput } from '@/components/settings/ApiKeyInput';
import { ModelSelector } from '@/components/settings/ModelSelector';
import { ThemeToggle } from '@/components/settings/ThemeToggle';

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-6 sm:px-6">
      <div className="mb-6 flex items-center gap-2">
        <SettingsIcon className="h-5 w-5 text-gold-400" />
        <h1 className="font-display text-xl font-bold">Settings</h1>
      </div>

      <div className="space-y-6">
        <section className="rounded-xl border border-border/60 bg-card/40 p-5">
          <h2 className="mb-4 text-sm font-semibold">AI configuration</h2>
          <div className="space-y-4">
            <ApiKeyInput />
            <ModelSelector />
            <ThemeToggle />
          </div>
        </section>

        <Separator />

        <section className="rounded-xl border border-border/60 bg-card/40 p-5">
          <h2 className="mb-2 text-sm font-semibold">About</h2>
          <p className="text-xs text-muted-foreground">
            DataScribe is a multi-agent data analysis platform. Six specialised agents — Supervisor, Planner, Programmer, Executor, Critic, and Reporter — collaborate to analyse your dataset and produce a report with charts. Every step streams live via Server-Sent Events.
          </p>
        </section>
      </div>
    </div>
  );
}