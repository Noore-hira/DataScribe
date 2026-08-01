import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Download,
  X,
  Maximize2,
  Image as ImageIcon,
  CheckCircle2,
  BarChart3,
  Globe
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MarkdownContent } from '@/components/chat/ChatMessage';
import { useSettings } from '@/contexts/SettingsContext';
import type { WorkflowReport } from '@/types';

// @ts-ignore
import html2pdf from 'html2pdf.js';

interface ReportViewerProps {
  report: WorkflowReport;
  durationMs?: number;
}

const resolveGlobalChartUrl = (src: string, base: string) => {
  if (src.startsWith('http')) return src;
  const baseUrl = base || "https://da-5f4c85c6edef485aae966f71f553a8f0.ecs.us-east-1.on.aws";
  const cleanName = src.replace(/^(\/?charts\/)+/, '').replace(/^\/+/, '');
  return `${baseUrl}/charts/${cleanName}`;
};

export function ReportViewer({ report, durationMs }: ReportViewerProps) {
  const [copied, setCopied] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const { backendUrl } = useSettings();
  const base = backendUrl?.endsWith('/') ? backendUrl.slice(0, -1) : (backendUrl ?? '');

  const uniqueContainerId = `report-pdf-content-${report.generatedAt}`;

  const extractedCharts = (() => {
    const validCharts: string[] = [];
    
    if (Array.isArray((report as any).charts)) validCharts.push(...(report as any).charts);
    if (Array.isArray((report as any).chart_files)) validCharts.push(...(report as any).chart_files);

    if (validCharts.length === 0) {
      const matches = report.report?.match(/(?:charts\/)?([\w.-]+\.(?:png|html))/gi);
      if (matches) {
        validCharts.push(...matches.map((m) => m.replace(/^.*?charts\//, "")));
      }
    }

    const normalizedCharts = [...new Set(validCharts)]
      .filter(Boolean)
      .map((filename) => {
        const clean = filename.split("/").pop()!.replace(/[^a-zA-Z0-9_.-]/g, "");
        return `charts/${clean}`;
      });

    const nicelyNamedCharts = normalizedCharts.filter(
      (c) => !/(^|\/)chart_\d+\.(png|html)$/i.test(c)
    );

    return nicelyNamedCharts.length > 0 ? nicelyNamedCharts : normalizedCharts;
  })();

  const imageCharts = extractedCharts.filter(c => c.endsWith('.png'));
  const htmlCharts = extractedCharts.filter(c => c.endsWith('.html'));

  const isRealReport = extractedCharts.length > 0 || /^#/.test(report.report) || report.report.length > 1200;

  const processedReportText = report.report
    .replace(/!\[[^\]]*\]\([^)]+\.(png|html)\)/gi, "")
    .replace(/[\w./-]+\.(png|html)/gi, "")
    .replace(/src="charts\//g, `src="${base}/charts/`)
    .replace(/src="\/charts\//g, `src="${base}/charts/`)
    .replace(/src='charts\//g, `src='${base}/charts/`)
    .replace(/src='\/charts\//g, `src='${base}/charts/`)
    .trim();

  // ==========================================================
  // EXPORT FUNCTIONS
  // ==========================================================
  
  const downloadPDF = async () => {
    setIsExporting(true);
    await new Promise((resolve) => setTimeout(resolve, 150));

    const element = document.getElementById(uniqueContainerId);
    if (!element) {
      setIsExporting(false);
      return;
    }

    const opt: any = {
      margin:       0.5,
      filename:     `datascribe-report-${new Date(report.generatedAt).toISOString().slice(0, 10)}.pdf`,
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2, useCORS: true },
      jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' },
      pagebreak:    { mode: 'avoid-all' } 
    };

    // @ts-ignore
    await html2pdf().set(opt).from(element).save();
    setIsExporting(false);
  };

  // 🛠️ UPDATED: Fetches interactive chart text and injects via srcdoc to bypass CORS completely
  const downloadHTML = async () => {
    setIsExporting(true); 

    try {
      // 1. Fetch interactive charts and embed their raw markup using srcdoc
      const iframesHtmlPromises = htmlCharts.map(async (src) => {
        const absoluteUrl = resolveGlobalChartUrl(src, base);
        try {
          const response = await fetch(absoluteUrl);
          const htmlText = await response.text();
          
          // Escape quotes safely so it can sit inside the srcdoc attribute
          const escapedHtml = htmlText
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');

          return `<div class="chart-box"><iframe srcdoc="${escapedHtml}" sandbox="allow-scripts allow-same-origin allow-popups"></iframe></div>`;
        } catch (err) {
          console.error("Failed to fetch interactive chart:", err);
          return `<div class="chart-box"><iframe src="${absoluteUrl}" sandbox="allow-scripts allow-same-origin allow-popups"></iframe></div>`;
        }
      });
      const iframesHtmlArray = await Promise.all(iframesHtmlPromises);
      const iframesHtml = iframesHtmlArray.join('\n');

      // 2. Fetch static images and convert them to Base64 data URIs
      const imagesHtmlPromises = imageCharts.map(async (src) => {
        const absoluteUrl = resolveGlobalChartUrl(src, base);
        try {
          const response = await fetch(absoluteUrl);
          const blob = await response.blob();
          return new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => {
              resolve(`<div class="chart-box"><img src="${reader.result}" alt="Static Chart" /></div>`);
            };
            reader.readAsDataURL(blob);
          });
        } catch (err) {
          console.error("Failed to fetch static chart:", err);
          return `<div class="chart-box"><img src="${absoluteUrl}" alt="Static Chart" /></div>`;
        }
      });
      const imagesHtmlArray = await Promise.all(imagesHtmlPromises);
      const imagesHtml = imagesHtmlArray.join('\n');

      // 3. Build the fully self-contained HTML page
      const htmlTemplate = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Data Analysis Report</title>
          <style>
            body { 
              font-family: system-ui, -apple-system, sans-serif; 
              line-height: 1.6; 
              color: #111827; 
              background: #f3f4f6;
              margin: 0;
              padding: 40px 20px;
            }
            .container { 
              max-width: 900px; 
              margin: 0 auto; 
              background: white; 
              padding: 40px; 
              border-radius: 12px; 
              box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); 
            }
            h1 { border-bottom: 1px solid #e5e7eb; padding-bottom: 10px; margin-top: 0; }
            .meta { color: #6b7280; font-size: 0.875rem; margin-bottom: 30px; }
            .content { white-space: pre-wrap; font-family: inherit; font-size: 1rem; color: #374151; }
            .section-title { margin-top: 40px; margin-bottom: 20px; color: #111827; }
            .chart-box {
              margin-bottom: 24px;
              border: 1px solid #e5e7eb;
              border-radius: 8px;
              overflow: hidden;
              background: white;
              box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            iframe { width: 100%; height: 500px; border: none; display: block; }
            img { width: 100%; height: auto; display: block; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>Final Analysis Report</h1>
            <div class="meta">Generated on ${new Date(report.generatedAt).toLocaleString()}</div>
            
            <div class="content">${processedReportText}</div>
            
            ${htmlCharts.length > 0 ? `
              <h2 class="section-title">Interactive Charts</h2>
              ${iframesHtml}
            ` : ''}

            ${imageCharts.length > 0 ? `
              <h2 class="section-title">Static Charts</h2>
              ${imagesHtml}
            ` : ''}
          </div>
        </body>
        </html>
      `;

      // 4. Trigger download
      const blob = new Blob([htmlTemplate], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `datascribe-interactive-report-${new Date(report.generatedAt).toISOString().slice(0, 10)}.html`;
      a.click();
      URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error("Error generating HTML report:", error);
    } finally {
      setIsExporting(false);
    }
  };

  const copyReport = () => {
    navigator.clipboard.writeText(report.report);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  if (!isRealReport) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="px-2 py-2">
        <div className="rounded-2xl bg-transparent p-2">
          <div className="prose prose-invert max-w-none text-white">
            <MarkdownContent content={processedReportText} base={base} />
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="overflow-hidden rounded-2xl border border-gold-500/35 bg-gradient-to-b from-gold-500/5 to-transparent"
    >
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gold-500/20 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-gold text-black">
            <FileText className="h-4 w-4" />
          </div>
          <div>
            <h3 className="font-display text-base font-bold">Final Report</h3>
            <p className="text-xs text-muted-foreground">
              Generated {new Date(report.generatedAt).toLocaleTimeString()}
              {durationMs != null && ` · ${(durationMs / 1000).toFixed(1)}s`}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 flex-wrap">
          <Button variant="ghost" size="sm" onClick={copyReport} className="gap-1.5">
            {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-success" /> : <Download className="h-3.5 w-3.5" />}
            {copied ? 'Copied' : 'Copy'}
          </Button>
          
          <Button variant="outline" size="sm" onClick={downloadPDF} className="gap-1.5 hover:bg-gold-500/10 hover:text-gold-400">
            <Download className="h-3.5 w-3.5" />
            PDF
          </Button>

          <Button size="sm" onClick={downloadHTML} className="gap-1.5 bg-gradient-gold text-black hover:opacity-90" disabled={isExporting}>
            <Globe className="h-3.5 w-3.5" />
            {isExporting ? 'Exporting...' : 'Export HTML'}
          </Button>
        </div>
      </div>

      <div className="max-h-[70vh] overflow-y-auto scrollbar-thin pb-4">
        <div id={uniqueContainerId} className={isExporting ? "bg-white text-black pb-8 p-4" : "bg-background/50 pb-8"}>
          
          <div className="px-5 py-4">
            <div className={isExporting ? "prose max-w-none text-black" : "prose prose-invert max-w-none text-white"}>
              <MarkdownContent content={processedReportText} base={base} />
            </div>
          </div>

          {htmlCharts.length > 0 && (
            <div className="border-t border-gold-500/20 px-5 py-4 break-inside-avoid">
              {isExporting ? (
                <div className="rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm font-medium text-gray-500">
                  <BarChart3 className="mx-auto mb-2 h-6 w-6 text-gray-400" />
                  Interactive charts ({htmlCharts.length}) cannot be rendered in PDFs. <br/>
                  Please use the <b>Export HTML</b> button to download an interactive version.
                </div>
              ) : (
                <InteractiveCharts charts={htmlCharts} base={base} />
              )}
            </div>
          )}

          {imageCharts.length > 0 && (
            <div className="border-t border-gold-500/20 px-5 py-4">
              <ChartGallery charts={imageCharts} base={base} isExporting={isExporting} />
            </div>
          )}

        </div>
      </div>
    </motion.div>
  );
}

// ==========================================================
// INTERACTIVE CHARTS COMPONENT (IFRAME)
// ==========================================================
function InteractiveCharts({ charts, base }: { charts: string[], base: string }) {
  return (
    <div className="space-y-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <BarChart3 className="h-4 w-4 text-gold-400" />
        Interactive Charts
        <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] text-muted-foreground">
          {charts.length}
        </span>
      </div>
      
      <div className="flex flex-col gap-6">
        {charts.map((src, i) => (
          <div key={src + i} className="overflow-hidden rounded-xl border border-border/60 bg-white shadow-sm break-inside-avoid">
            <iframe
              src={resolveGlobalChartUrl(src, base)}
              className="h-[500px] w-full border-0 bg-white"
              title={`Interactive Chart ${i + 1}`}
              sandbox="allow-scripts allow-same-origin allow-popups"
            />
          </div>
        ))}
      </div>
    </div>
  );
}

// ==========================================================
// STATIC CHARTS COMPONENT (IMAGES)
// ==========================================================
function ChartGallery({ charts, base, isExporting = false }: { charts: string[], base: string, isExporting?: boolean }) {
  const [fullscreen, setFullscreen] = useState<string | null>(null);

  const downloadImage = async (src: string) => {
    const absoluteUrl = resolveGlobalChartUrl(src, base);
    const filename = src.split('/').pop() ?? 'chart.png';

    try {
      const response = await fetch(absoluteUrl);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a); 
      a.click();
      
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Failed to fetch image for download:", error);
      const a = document.createElement('a');
      a.href = absoluteUrl;
      a.download = filename;
      a.target = '_blank';
      a.click();
    }
  };

  return (
    <>
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <ImageIcon className="h-4 w-4 text-gold-400" />
        Static Charts
        <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] text-muted-foreground">
          {charts.length}
        </span>
      </div>
      <div className={`grid gap-6 ${isExporting ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'}`}>
        {charts.map((src, i) => {
          const absoluteSrc = resolveGlobalChartUrl(src, base);
          return (
            <motion.div
              key={src + i}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.08 }}
              className={`group relative overflow-hidden rounded-lg border border-border/60 ${isExporting ? 'bg-transparent' : 'bg-card/40'} break-inside-avoid page-break-inside-avoid`}
            >
              <img
                src={absoluteSrc}
                alt={`Chart ${i + 1}`}
                crossOrigin="anonymous"
                className="w-full cursor-pointer object-contain transition-transform group-hover:scale-105"
                onClick={() => setFullscreen(absoluteSrc)}
              />
              {!isExporting && (
                <div className="absolute inset-0 flex items-end justify-end gap-2 bg-gradient-to-t from-black/60 to-transparent p-2 opacity-0 transition-opacity group-hover:opacity-100">
                  <button
                    onClick={() => setFullscreen(absoluteSrc)}
                    className="rounded-md bg-background/80 p-1.5 text-foreground backdrop-blur"
                    aria-label="Open fullscreen"
                  >
                    <Maximize2 className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => downloadImage(src)}
                    className="rounded-md bg-background/80 p-1.5 text-foreground backdrop-blur"
                    aria-label="Download chart"
                  >
                    <Download className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      <AnimatePresence>
        {fullscreen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6 backdrop-blur"
            onClick={() => setFullscreen(null)}
          >
            <button
              className="absolute right-4 top-4 grid h-10 w-10 place-items-center rounded-full bg-background/80 text-foreground"
              onClick={() => setFullscreen(null)}
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
            <img
              src={fullscreen}
              alt="Chart fullscreen"
              className="max-h-[85vh] max-w-[90vw] h-auto w-auto rounded-lg object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              className="absolute bottom-6 right-6 flex items-center gap-2 rounded-lg bg-gradient-gold px-4 py-2 text-sm font-semibold text-black"
              onClick={(e) => {
                e.stopPropagation();
                downloadImage(fullscreen);
              }}
            >
              <Download className="h-4 w-4" />
              Download
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}