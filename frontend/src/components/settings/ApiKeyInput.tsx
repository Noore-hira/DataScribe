import { useState } from 'react';
import { Eye, EyeOff, KeyRound, Save, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { useSettings } from '@/contexts/SettingsContext';

export function ApiKeyInput() {
  const { apiKey, setApiKey } = useSettings();
  const [draft, setDraft] = useState(apiKey);
  const [show, setShow] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setApiKey(draft);
    setSaved(true);
    toast.success('Groq API key saved', {
      description: 'Stored locally in your browser only.',
    });
    setTimeout(() => setSaved(false), 1800);
  };

  return (
    <div className="space-y-2">
      <Label className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <KeyRound className="h-3.5 w-3.5 text-gold-400" />
        Groq API Key
      </Label>
      <div className="relative">
        <Input
          type={show ? 'text' : 'password'}
          placeholder="gsk_..."
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="bg-background/60 pr-9 font-mono text-xs"
        />
        <button
          type="button"
          onClick={() => setShow((s) => !s)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
          aria-label={show ? 'Hide API key' : 'Show API key'}
        >
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
      <Button
        size="sm"
        onClick={handleSave}
        disabled={draft === apiKey && !saved}
        className="w-full bg-gradient-gold font-semibold text-black hover:opacity-90"
      >
        {saved ? <Check className="mr-1.5 h-3.5 w-3.5" /> : <Save className="mr-1.5 h-3.5 w-3.5" />}
        {saved ? 'Saved' : 'Save key'}
      </Button>
    </div>
  );
}
