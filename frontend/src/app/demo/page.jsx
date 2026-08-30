"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { CuratedDashboard } from "@/components/curated-dashboard";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function DemoPage() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/api/demo/dashboard").then(setData).catch(() => setData({})); }, []);
  return <AppShell><main className="mx-auto w-full max-w-7xl px-4 py-8"><div className="mb-6 flex items-start justify-between"><div><h1 className="text-3xl font-bold uppercase tracking-wide text-blue-950">Dashboard Demo</h1><p className="mt-2 text-sm text-slate-600">A clearly designated sample of company and report intelligence, citations, and download controls.</p></div><Link href="/upload"><Button>Upload a real report</Button></Link></div>{data ? <CuratedDashboard data={data} /> : <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />}</main></AppShell>;
}
