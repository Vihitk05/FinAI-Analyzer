"use client";

import { FileText, Filter, Search, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ReportSummary } from "@/components/report-summary";
import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { api, ApiError } from "@/lib/api";

const PAGE_SIZE = 20;

const STATUS_LABEL = {
  queued: "Queued",
  processing: "Analysing",
  completed: "Completed",
  failed: "Failed",
};

function ReportsPageContent() {
  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const data = await api.get(`/fetch_all_data/?limit=${PAGE_SIZE}&offset=0`);
      setReports(data.data || []);
      setTotal(data.total ?? (data.data || []).length);
      setError("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load reports.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleDelete = async (customId) => {
    if (!window.confirm("Delete this report? This cannot be undone.")) return;
    setDeletingId(customId);
    try {
      await api.del(`/fetch_data/${customId}`);
      setReports((prev) => prev.filter((r) => r.custom_id !== customId));
      setTotal((prev) => prev - 1);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete this report.");
    } finally {
      setDeletingId(null);
    }
  };

  const filteredReports = reports.filter((report) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      report.companyName?.toLowerCase().includes(term) ||
      report.analysis_date?.toLowerCase().includes(term) ||
      report.custom_id?.toString().includes(term)
    );
  });

  return (
    <div className="flex flex-col items-center py-8">
      <div className="container px-4">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold uppercase tracking-wide text-blue-900">Financial Reports</h1>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-blue-500" />
              <Input
                type="search"
                placeholder="Search reports..."
                className="w-[200px] pl-8 md:w-[300px] border-blue-200 focus:border-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button
              variant="outline"
              size="icon"
              className="border-blue-200 text-blue-600 hover:bg-blue-100"
              onClick={() => setSearchTerm("")}
              aria-label="Clear search"
            >
              <Filter className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {error && (
          <div role="alert" className="mb-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <Tabs defaultValue="all" className="mb-6">
          <TabsList className="bg-blue-100">
            <TabsTrigger value="all" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white">
              All Reports {total ? `(${total})` : ""}
            </TabsTrigger>
          </TabsList>
          <TabsContent value="all" className="space-y-6">
            {loading ? (
              <div className="flex justify-center py-20">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
              </div>
            ) : filteredReports.length === 0 ? (
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle className="text-blue-900">
                    {reports.length === 0 ? "No reports yet" : "No reports match your search"}
                  </CardTitle>
                  <CardDescription>
                    {reports.length === 0
                      ? "Upload your first annual report to see it here."
                      : "Try a different search term."}
                  </CardDescription>
                </CardHeader>
                {reports.length === 0 && (
                  <CardContent>
                    <Link href="/upload">
                      <Button className="bg-blue-600 hover:bg-blue-700">
                        <FileText className="mr-2 h-4 w-4" />
                        Upload a report
                      </Button>
                    </Link>
                  </CardContent>
                )}
              </Card>
            ) : (
              filteredReports.map((report) => {
                const status = report.status || "completed";
                const isProcessing = status === "queued" || status === "processing";
                return (
                  <Card key={report.custom_id} className="border-blue-200">
                    <CardContent>
                      <div className="mb-2 flex items-center justify-between">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                            status === "completed"
                              ? "bg-green-100 text-green-700"
                              : status === "failed"
                                ? "bg-red-100 text-red-700"
                                : "bg-amber-100 text-amber-700"
                          }`}
                        >
                          {STATUS_LABEL[status] || status}
                        </span>
                        <button
                          onClick={() => handleDelete(report.custom_id)}
                          disabled={deletingId === report.custom_id}
                          aria-label={`Delete report for ${report.companyName || "this document"}`}
                          className="text-muted-foreground hover:text-red-600 disabled:opacity-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                      {isProcessing ? (
                        <div className="py-4">
                          <p className="font-medium text-blue-900">Report #{report.custom_id}</p>
                          <p className="text-sm text-muted-foreground">Analysis in progress&hellip;</p>
                        </div>
                      ) : (
                        <ReportSummary
                          company={report.companyName}
                          date={report.analysis_date}
                          revenue={report.revenue}
                          netIncome={report.netIncome}
                          currency={report.currency}
                        />
                      )}
                      <div className="mt-4 flex justify-end">
                        <Link href={`/report/${report.custom_id}`}>
                          <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                            {status === "failed" ? "View details" : isProcessing ? "View progress" : "View Full Report"}
                          </Button>
                        </Link>
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <AppShell>
      <ReportsPageContent />
    </AppShell>
  );
}
