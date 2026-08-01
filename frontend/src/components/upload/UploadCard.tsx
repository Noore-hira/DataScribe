import { useCallback, useRef, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  X,
  RotateCw,
  Loader2,
  Rows3,
  Columns3,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { uploadDataset } from '@/services/api';
import { ApiError } from '@/services/api';
import { useSession } from '@/contexts/SessionContext';
import { useSettings } from '@/contexts/SettingsContext';
import type { DatasetMeta } from '@/types';

const ACCEPTED = ['.csv', '.xlsx', '.xls'];
const MAX_BYTES = 25 * 1024 * 1024;

interface UploadCardProps {
  compact?: boolean;
  onUploaded?: (d: DatasetMeta) => void;
}

export function UploadCard({ compact, onUploaded }: UploadCardProps) {
  const { dataset, setDataset, setThreadId } = useSession();
  const { backendUrl } = useSettings();
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      const ext = '.' + (file.name.split('.').pop()?.toLowerCase() ?? '');
      if (!ACCEPTED.includes(ext)) {
        toast.error('Unsupported file type', {
          description: 'Please upload a .csv, .xlsx, or .xls file.',
        });
        return;
      }
      if (file.size > MAX_BYTES) {
        toast.error('File too large', { description: 'Maximum size is 25 MB.' });
        return;
      }

      setUploading(true);
      setProgress(0);
      try {
        const meta = await uploadDataset(file, backendUrl, (p) => setProgress(p));
        setDataset(meta);
        setThreadId(meta.threadId);
        onUploaded?.(meta);
        toast.success('Dataset uploaded', {
          description: `${meta.filename} · ${meta.rows} rows × ${meta.columns} columns`,
        });
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : 'Upload failed. Is the backend running?';
        toast.error('Upload failed', { description: msg });
      } finally {
        setUploading(false);
      }
    },
    [backendUrl, setDataset, setThreadId, onUploaded]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const clearDataset = useCallback(() => {
    setDataset(null);
    setThreadId(uuidv4());
    setProgress(0);
  }, [setDataset, setThreadId]);

  if (dataset) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          'relative overflow-hidden rounded-xl border border-success/30 bg-success/5 p-4',
          compact && 'p-3'
        )}
      >
        <div className="flex items-center gap-3">
          <motion.div
            initial={{ scale: 0.6, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 400, damping: 15 }}
            className="grid h-10 w-10 place-items-center rounded-lg bg-success/15 text-success"
          >
            <CheckCircle2 className="h-5 w-5" />
          </motion.div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <FileSpreadsheet className="h-4 w-4 text-gold-400" />
              <span className="truncate">{dataset.filename}</span>
            </div>
            <div className="mt-1 flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Rows3 className="h-3 w-3" />
                {dataset.rows.toLocaleString()} rows
              </span>
              <span className="flex items-center gap-1">
                <Columns3 className="h-3 w-3" />
                {dataset.columns} columns
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
            onClick={clearDataset}
            aria-label="Remove dataset"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </motion.div>
    );
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click();
      }}
      className={cn(
        'group relative cursor-pointer overflow-hidden rounded-xl border-2 border-dashed p-6 text-center transition-all',
        dragging
          ? 'border-gold-400 bg-gold-500/10 glow-soft'
          : 'border-border bg-card/40 hover:border-gold-500/40 hover:bg-card/60'
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(',')}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handleFile(f);
          e.target.value = '';
        }}
      />

      <AnimatePresence mode="wait">
        {uploading ? (
          <motion.div
            key="uploading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-3 py-2"
          >
            <Loader2 className="h-8 w-8 animate-spin text-gold-400" />
            <div className="text-sm font-medium">Uploading… {progress}%</div>
            <div className="h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-secondary">
              <motion.div
                className="h-full bg-gradient-gold"
                animate={{ width: `${progress}%` }}
                transition={{ ease: 'easeOut' }}
              />
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-2"
          >
            <motion.div
              animate={dragging ? { y: -4 } : { y: 0 }}
              className="grid h-12 w-12 place-items-center rounded-xl bg-gradient-gold/10 text-gold-400 transition-transform group-hover:scale-110"
            >
              <UploadCloud className="h-6 w-6" />
            </motion.div>
            <div className="text-sm font-semibold">
              {dragging ? 'Drop to upload' : 'Drag & drop your dataset'}
            </div>
            <div className="text-xs text-muted-foreground">
              CSV, Excel (.xlsx, .xls) · up to 25 MB
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {uploading && progress > 0 && progress < 100 && (
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-2 top-2"
          onClick={(e) => {
            e.stopPropagation();
            toast.info('Retry available after failure');
          }}
        >
          <RotateCw className="h-3.5 w-3.5" />
        </Button>
      )}
    </div>
  );
}
