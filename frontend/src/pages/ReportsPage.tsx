import { motion } from 'framer-motion';
import { FileText, Sparkles } from 'lucide-react';
import { ReportViewer } from '@/components/report/ReportViewer';
import { useWorkflow } from '@/contexts/WorkflowContext';

export default function ReportsPage() {
  const { reports, timeline } = useWorkflow();

  if (!reports || reports.length === 0) {
    return (
      <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center gap-3 px-6 text-center">
        <div className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-gold/10 text-gold-400">
          <FileText className="h-7 w-7" />
        </div>
        <h2 className="font-display text-lg font-bold">No reports yet</h2>
        <p className="max-w-sm text-sm text-muted-foreground">
          Run an analysis from the Chat tab. When the reporter agent finishes, the full report and generated charts will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full w-full overflow-y-auto">
      <div className="mx-auto max-w-3xl px-4 py-6 pb-32 sm:px-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex items-center gap-2"
        >
          <Sparkles className="h-5 w-5 text-gold-400" />
          <h1 className="font-display text-xl font-bold">Session Reports</h1>
        </motion.div>
        
        <div className="space-y-10">
          {reports.map((report, index) => (
            <motion.div 
              key={report.generatedAt || index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex flex-col"
            >
              <div className="mb-4 flex items-center justify-between border-b border-border/40 pb-2">
                <h3 className="font-display text-sm font-semibold text-muted-foreground">
                  Analysis #{index + 1}
                </h3>
                <span className="text-xs text-muted-foreground/60">
                  {new Date(report.generatedAt).toLocaleTimeString()}
                </span>
              </div>
              
              <ReportViewer report={report} />
            </motion.div>
          ))}
        </div>

        {timeline.length > 0 && (
          <p className="mt-8 border-t border-border/40 pt-4 text-center text-xs text-muted-foreground">
            Generated across {timeline.length} streamed workflow events.
          </p>
        )}
      </div>
    </div>
  );
}