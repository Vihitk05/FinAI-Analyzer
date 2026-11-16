"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { Download, FileText } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { CuratedDashboard } from "@/components/curated-dashboard";
import { ChatBot } from "@/components/Chatbot";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, API_URL, ApiError } from "@/lib/api";

const EXPORT_STAGE_LABEL = {
  pptx: "Preparing presentation…",
  pdf: "Preparing PDF (this can take a few extra seconds)…",
};

function CompanyDashboardContent({ id }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(null); // "pptx" | "pdf" | null
  const [exportError, setExportError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    api
      .get(`/api/companies/${id}/dashboard`)
      .then((value) => {
        if (active) {
          setData(value);
          setError("");
        }
      })
      .catch((err) => {
        if (active)
          setError(
            err instanceof ApiError
              ? err.message
              : "Unable to load the company dashboard."
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id]);

  // Exports are synchronous (fast, no LLM call in the path) but still fully
  // validated server-side before the response is sent - a failed
  // validation returns a JSON error, never a corrupt file, so this fetches
  // and checks success/failure explicitly rather than navigating a new tab
  // straight at the URL (which would leave a failure as a blank/error tab
  // with no explanation).
  const download = async (format) => {
    setExportError("");
    setExporting(format);
    try {
      const response = await fetch(
        `${API_URL}/api/companies/${id}/presentation?format=${format}`,
        { credentials: "include" }
      );
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.error || "Export failed. Please try again.");
      }
      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename="?([^"]+)"?/);
      const filename = match
        ? match[1]
        : `company-financial-intelligence.${format}`;
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
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
  if (loading)
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    );
  if (error)
    return (
      <Card className="mx-auto mt-12 max-w-lg">
        <CardContent className="py-8">
          <p className="text-red-700">{error}</p>
          <Link href="/dashboard">
            <Button className="mt-4">Back to companies</Button>
          </Link>
        </CardContent>
      </Card>
    );
  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8">
      <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div className="min-w-0">
          <Link
            href="/dashboard"
            className="text-sm text-blue-700 hover:underline"
          >
            ← All companies
          </Link>
          <h1 className="mt-2 break-words text-3xl font-bold uppercase tracking-wide text-blue-950">
            {data?.company?.name}
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Curated from {data?.sourceReports?.length || 0} validated report
            {data?.sourceReports?.length === 1 ? "" : "s"}. Version{" "}
            {data?.dashboardVersion || "current"}.
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            variant="outline"
            disabled={!!exporting}
            onClick={() => download("pptx")}
          >
            <FileText className="mr-2 h-4 w-4" />
            {exporting === "pptx" ? "Preparing…" : "Download PPT"}
          </Button>
          <Button
            variant="outline"
            disabled={!!exporting}
            onClick={() => download("pdf")}
          >
            <Download className="mr-2 h-4 w-4" />
            {exporting === "pdf" ? "Preparing…" : "Download PDF"}
          </Button>
        </div>
      </div>
      {exporting && (
        <p className="mb-4 text-sm text-slate-600">
          {EXPORT_STAGE_LABEL[exporting]}
        </p>
      )}
      {exportError && (
        <div
          role="alert"
          className="mb-4 break-words rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {exportError}
        </div>
      )}
      <CuratedDashboard data={data} />
      <div className="mt-8">
        <ChatBot companyId={id} />
      </div>
    </main>
  );
}

export default function CompanyDashboardPage({ params }) {
  const { id } = use(params);
  return (
    <AppShell>
      <CompanyDashboardContent id={id} />
    </AppShell>
  );
}
