"use client";

import { use, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Download, FileText } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { CuratedDashboard } from "@/components/curated-dashboard";
import { ChatBot } from "@/components/Chatbot";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, API_URL, ApiError, getArrayBuffer } from "@/lib/api";

// Export failures return JSON, so fetch explicitly instead of opening the URL.
function useExport(basePath) {
  const [exporting, setExporting] = useState(null);
  const [exportError, setExportError] = useState("");
  const download = async (format) => {
    setExportError("");
    setExporting(format);
    try {
      const response = await fetch(`${API_URL}${basePath}?format=${format}`, { credentials: "include" });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.error || "Export failed. Please try again.");
      }
      const blob = await response.blob();
      const match = (response.headers.get("Content-Disposition") || "").match(/filename="?([^"]+)"?/);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = match ? match[1] : `financial-intelligence.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setExportError(err.message || "Export failed. Please try again.");
    } finally {
      setExporting(null);
    }
  };
  return { exporting, exportError, download };
}

const POLL_MS = 2500;

function ReportDashboard({ id }) {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState(null);
  const [ocr, setOcr] = useState(null); // { phase: "running"|"failed", done, total, message }
  const [error, setError] = useState("");
  const { exporting, exportError, download } = useExport(`/api/reports/${id}/presentation`);
  const ocrRunningFor = useRef(null); // job_id currently being OCR'd, so we don't start twice

  // Runs Puter.js/Mistral OCR in the browser for a job the backend parked
  // because the PDF had no text layer, then posts the page-mapped result
  // back so the async pipeline resumes.
  const runClientOcr = useCallback(async (job) => {
    if (ocrRunningFor.current === job.job_id) return;
    ocrRunningFor.current = job.job_id;
    setOcr({ phase: "running", done: 0, total: 0 });
    try {
      const { runMistralOcr } = await import("@/lib/ocr-puter");
      const pdf = await getArrayBuffer(`/jobs/${job.job_id}/ocr-document`);
      const pages = await runMistralOcr(pdf, {
        onProgress: ({ done, total }) => setOcr({ phase: "running", done, total }),
      });
      await api.post(`/jobs/${job.job_id}/ocr-result`, { status: "completed", pages });
      setOcr(null);
    } catch (err) {
      const message =
        err?.name === "AbortError"
          ? "OCR was cancelled."
          : err instanceof ApiError
          ? err.message
          : err?.message || "OCR failed.";
      setOcr({ phase: "failed", message });
      // Tell the backend so the job fails cleanly rather than hanging.
      try {
        await api.post(`/jobs/${job.job_id}/ocr-result`, { status: "failed", error: message });
      } catch {
        /* best effort */
      }
    } finally {
      ocrRunningFor.current = null;
    }
  }, []);

  useEffect(() => {
    let active = true;
    let timer;

    const poll = async () => {
      // Check the job first so we can drive the browser-OCR step and surface
      // a failed analysis. A report with no job row (older uploads) just
      // skips straight to loading the dashboard.
      try {
        const job = await api.get(`/jobs/by-report/${id}/status`);
        if (!active) return;
        setStatus(job);
        if (job.status === "awaiting_ocr") {
          runClientOcr(job);
          timer = setTimeout(poll, POLL_MS);
          return;
        }
        if (job.status === "failed") {
          setError(job.error || "Analysis failed for this document.");
          return;
        }
      } catch (err) {
        if (!(err instanceof ApiError && err.status === 404)) {
          if (active) setError(err instanceof ApiError ? err.message : "Unable to load this report.");
          return;
        }
        // 404 -> no job for this report; fall through to the dashboard.
      }

      try {
        const next = await api.get(`/api/reports/${id}/dashboard`);
        if (active) setData(next);
      } catch (err) {
        if (!active) return;
        if (err instanceof ApiError && err.status === 409) {
          timer = setTimeout(poll, POLL_MS); // report exists but is still processing
          return;
        }
        setError(err instanceof ApiError ? err.message : "Unable to load this report.");
      }
    };

    poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [id, runClientOcr]);

  if (error) {
    return (
      <Card className="mx-auto mt-12 max-w-lg">
        <CardContent className="py-8 text-red-700">{error}</CardContent>
      </Card>
    );
  }

  if (!data) {
    let label = "Loading report dashboard…";
    if (ocr?.phase === "running") {
      label = ocr.total
        ? `Reading scanned pages with OCR… ${ocr.done}/${ocr.total}`
        : "Reading this scanned document with OCR…";
    } else if (ocr?.phase === "failed") {
      label = ocr.message;
    } else if (status?.status === "awaiting_ocr") {
      label = "Preparing OCR for this scanned document…";
    } else if (status) {
      label = `Report ${status.stage || "analysis"} in progress…`;
    }
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
        <p className="mt-4 max-w-md text-center text-sm text-slate-600">{label}</p>
        {ocr?.phase === "running" ? (
          <p className="mt-2 max-w-md text-center text-xs text-slate-400">
            OCR runs in your browser and may prompt you to authorise it the first time.
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div className="min-w-0">
          <Link href="/reports" className="inline-flex items-center text-sm text-blue-700 hover:underline">
            <ArrowLeft className="mr-1 h-4 w-4" />
            Back to reports
          </Link>
          <h1 className="mt-4 break-words text-3xl font-bold uppercase tracking-wide text-blue-950">
            {data.company?.name || "Report Intelligence"}
          </h1>
          <p className="mt-1 text-sm text-slate-600">Single-report scope · source-verified facts only</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button variant="outline" disabled={!!exporting} onClick={() => download("pptx")}>
            <FileText className="mr-2 h-4 w-4" />
            {exporting === "pptx" ? "Preparing…" : "Download PPT"}
          </Button>
          <Button variant="outline" disabled={!!exporting} onClick={() => download("pdf")}>
            <Download className="mr-2 h-4 w-4" />
            {exporting === "pdf" ? "Preparing…" : "Download PDF"}
          </Button>
        </div>
      </div>
      {exporting ? <p className="mt-3 text-sm text-slate-600">Preparing… building slides · validating structure · {exporting === "pdf" ? "converting · checking" : "checking"}</p> : null}
      {exportError ? <div role="alert" className="mt-3 break-words rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{exportError}</div> : null}
      <div className="mt-7">
        <CuratedDashboard data={data} />
      </div>
      <div className="mt-8">
        <ChatBot customId={id} />
      </div>
    </main>
  );
}

export default function ReportDashboardPage({ params }) {
  const { id } = use(params);
  return (
    <AppShell>
      <ReportDashboard id={id} />
    </AppShell>
  );
}
