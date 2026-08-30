"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Building2, Play, Upload } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";

function DashboardContent() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api
      .get("/api/dashboard")
      .then(setData)
      .catch((err) =>
        setError(
          err instanceof ApiError ? err.message : "Unable to load companies."
        )
      );
  }, []);
  if (!data && !error)
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    );
  if (error)
    return (
      <div className="mx-auto max-w-lg py-16">
        <Card>
          <CardContent className="py-8 text-red-700">{error}</CardContent>
        </Card>
      </div>
    );
  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8">
      <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wide text-blue-950">
            Company Intelligence
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Choose a company to review its validated reports, evidence, and
            verified financial intelligence.
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/demo">
            <Button variant="outline">
              <Play className="mr-2 h-4 w-4" />
              View demo
            </Button>
          </Link>
          <Link href="/upload">
            <Button>
              <Upload className="mr-2 h-4 w-4" />
              Upload report
            </Button>
          </Link>
        </div>
      </div>
      {data?.empty ? (
        <Card className="max-w-xl border-blue-200">
          <CardHeader>
            <CardTitle>
              Welcome to FinAI Analyzer
              {user?.name ? `, ${user.name.split(" ")[0]}` : ""}
            </CardTitle>
            <CardDescription>
              Upload a report to create its source-verified company dashboard.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/upload">
              <Button>
                <Upload className="mr-2 h-4 w-4" />
                Upload financial report
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {data?.companies?.map((company) => (
            <Link key={company.id} href={`/company/${company.id}`}>
              <Card className="h-full border-blue-100 transition hover:border-blue-300 hover:shadow-md">
                <CardHeader>
                  <Building2 className="mb-2 h-5 w-5 text-blue-700" />
                  <CardTitle className="break-words">{company.name}</CardTitle>
                  <CardDescription>
                    {company.report_count} validated report
                    {company.report_count === 1 ? "" : "s"} · Dashboard v
                    {company.dashboard_version || 1}
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-sm font-medium text-blue-700">
                  Open intelligence dashboard →
                </CardContent>
              </Card>
            </Link>
          ))}
        </section>
      )}
    </main>
  );
}

export default function Dashboard() {
  return (
    <AppShell>
      <DashboardContent />
    </AppShell>
  );
}
