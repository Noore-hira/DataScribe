import { Moon, Sun } from 'lucide-react';
import { motion } from 'framer-motion';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useSettings } from '@/contexts/SettingsContext';

export function ThemeToggle() {
  const { theme, toggleTheme } = useSettings();
  const isDark = theme === 'dark';
  return (
    <div className="flex items-center justify-between">
      <Label className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        {isDark ? <Moon className="h-3.5 w-3.5 text-gold-400" /> : <Sun className="h-3.5 w-3.5 text-gold-400" />}
        {isDark ? 'Dark' : 'Light'} theme
      </Label>
      <Switch checked={isDark} onCheckedChange={toggleTheme} />
    </div>
  );
}

export function ThemeToggleAnimated() {
  const { theme, toggleTheme } = useSettings();
  const isDark = theme === 'dark';
  return (
    <button
      onClick={toggleTheme}
      className="relative flex h-9 w-16 items-center rounded-full border border-border bg-card/60 px-1 transition-colors"
      aria-label="Toggle theme"
    >
      <motion.span
        className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-gold text-black"
        animate={{ x: isDark ? 0 : 28 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      >
        {isDark ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
      </motion.span>
    </button>
  );
}
