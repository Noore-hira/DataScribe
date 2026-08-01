import { useState } from 'react';
import { Server, Save, Check, RotateCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { ApiKeyInput } from '@/components/settings/ApiKeyInput';
import { ModelSelector } from '@/components/settings/ModelSelector';
import { ThemeToggle } from '@/components/settings/ThemeToggle';
import { ConnectionIndicator } from '@/components/common/ConnectionIndicator';
import { useSettings } from '@/contexts/SettingsContext';
import { useConnectionStatus } from '@/hooks/use-connection-status';
import { DEFAULT_BACKEND_URL } from '@/types';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { backendUrl, setBackendUrl } = useSettings();
  const [draftUrl, setDraftUrl] = useState(backendUrl);
  const [saved, setSaved] = useState(false);
  const health = useConnectionStatus(backendUrl);

  const save = () => {
    setBackendUrl(draftUrl);
    setSaved(true);
    toast.success('Backend URL saved');
    setTimeout(() => setSaved(false), 1500);
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 sm:px-6">
      <div className="mb-6 flex items-center gap-2">
        <Server className="h-5 w-5 text-gold-400" />
        <h1 className="font-display text-xl font-bold">Settings</h1>
      </div>

      <div className="space-y-6">
        <section className="rounded-xl border border-border/60 bg-card/40 p-5">
          <h2 className="mb-4 text-sm font-semibold">Backend connection</h2>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label className="text-xs text-muted-foreground">Base URL</Label>
              <div className="flex gap-2">
                <Input
                  value={draftUrl}
                  onChange={(e) => setDraftUrl(e.target.value)}
                  placeholder={DEFAULT_BACKEND_URL}
                  className="font-mono text-xs"
                />
                <Button onClick={save} className="shrink-0 bg-gradient-gold text-black hover:opacity-90">
                  {saved ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-[11px] text-muted-foreground">
                The Python FastAPI backend serving <code className="font-mono">/api/upload</code> and <code className="font-mono">/api/chat/stream</code>.
              </p>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/60 bg-background/40 px-3 py-2">
              <span className="text-xs text-muted-foreground">Status</span>
              <ConnectionIndicator health={health} checking={health.online === false} />
            </div>
          </div>
        </section>

        <Separator />

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
