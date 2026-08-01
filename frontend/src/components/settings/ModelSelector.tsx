import { Cpu } from 'lucide-react';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { GROQ_MODELS, type GroqModel } from '@/types';
import { useSettings } from '@/contexts/SettingsContext';

export function ModelSelector() {
  const { model, setModel } = useSettings();
  return (
    <div className="space-y-2">
      <Label className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <Cpu className="h-3.5 w-3.5 text-gold-400" />
        Model
      </Label>
      <Select value={model} onValueChange={(v) => setModel(v as GroqModel)}>
        <SelectTrigger className="bg-background/60 font-mono text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {GROQ_MODELS.map((m) => (
            <SelectItem key={m.value} value={m.value} className="font-mono text-xs">
              {m.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
