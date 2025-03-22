"use client";

import { Download, FileText, Filter, Search } from "lucide-react";
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

export default function ReportsPage() {
  const defaultReport = [
    {
      id: 1,
      custom_id: "0000000000000000000",
      title: "Sample Financial Report",
      description: "Default report shown when API fails",
      company: "Example Corp",
      date: "2023-01-01",
      revenue: 1000000,
      ebitda: 200000,
      netIncome: 150000,
    },
  ];

  const [reports, setReports] = useState([]);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await fetch("http://127.0.0.1/fetch_all_data");
        const data = await response.json();
        setReports(data);
      } catch (error) {
        console.error("Error fetching reports:", error);
        setReports(defaultReport);
      }
    };

    fetchReports();
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-blue-50">
      <header
        className="sticky top-0 z-50 border-b bg-blue-100 backdrop-blur"
        style={{ display: "flex", justifyContent: "center" }}
      >
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl">
            <a href="/" style={{ cursor: "pointer" }}>
              <span className="text-blue-600">Fin</span>
              <span className="text-blue-900">Analyzer</span>
            </a>
          </div>
          <nav className="flex items-center gap-6">
            <a
              href="/dashboard"
              className="text-sm font-medium text-blue-700 hover:text-blue-900"
            >
              Dashboard
            </a>
            <a href="/reports" className="text-sm font-medium text-blue-900">
              Reports
            </a>
            <a
              href="/settings"
              className="text-sm font-medium text-blue-700 hover:text-blue-900"
            >
              Settings
            </a>
            <a href="/upload">
              <Button
                size="sm"
                variant="outline"
                className="text-blue-600 border-blue-600 hover:bg-blue-100"
              >
                <FileText className="mr-2 h-4 w-4" />
                New Report
              </Button>
            </a>
          </nav>
        </div>
      </header>
      <main
        className="flex py-8"
        style={{ flexDirection: "column", alignItems: "center" }}
      >
        <div className="container">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold text-blue-900">
              Financial Reports
            </h1>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-blue-500" />
                <Input
                  type="search"
                  placeholder="Search reports..."
                  className="w-[200px] pl-8 md:w-[300px] border-blue-200 focus:border-blue-500"
                />
              </div>
              <Button
                variant="outline"
                size="icon"
                className="border-blue-200 text-blue-600 hover:bg-blue-100"
              >
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <Tabs defaultValue="all" className="mb-6">
            <TabsList className="bg-blue-100">
              <TabsTrigger
                value="all"
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              >
                All Reports
              </TabsTrigger>
            </TabsList>
            <TabsContent value="all" className="space-y-6">
              {reports.map((report, index) => (
                <Card key={index} className="border-blue-200">
                  <CardHeader>
                    <CardTitle className="text-blue-900">
                      {report.title}
                    </CardTitle>
                    <CardDescription className="text-blue-600">
                      {report.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ReportSummary
                      company={report.company}
                      date={report.date}
                      revenue={report.revenue}
                      ebitda={report.ebitda}
                      netIncome={report.netIncome}
                    />
                    <div className="flex justify-end mt-4">
                      <Button
                        variant="outline"
                        size="sm"
                        className="mr-2 border-blue-600 text-blue-600 hover:bg-blue-100"
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download
                      </Button>
                      <a href={`/analysis/${report.custom_id}`}>
                        <Button
                          size="sm"
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          View Full Report
                        </Button>
                      </a>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
