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
  const [filteredReports, setFilteredReports] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5000/fetch_all_data/", {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          },
        });
  
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setReports(data.data);
        setFilteredReports(data.data); // Initialize filtered reports with all reports
      } catch (error) {
        console.error("Error fetching reports:", error);
        setReports(defaultReport);
        setFilteredReports(defaultReport);
      }
    };
  
    fetchReports();
  }, []);

  // Search function to filter reports
  const handleSearch = (term) => {
    setSearchTerm(term);
    if (!term.trim()) {
      setFilteredReports(reports);
      return;
    }

    const filtered = reports.filter(report => {
      // Search in company name (case insensitive)
      if (report.companyName?.toLowerCase().includes(term.toLowerCase())) {
        return true;
      }
      // Search in analysis date
      if (report.analysis_date?.toLowerCase().includes(term.toLowerCase())) {
        return true;
      }
      // Search in custom_id
      if (report.custom_id?.toString().includes(term)) {
        return true;
      }
      // Search in financial metrics (as strings)
      if (
        report.revenue?.toString().includes(term) ||
        report.ebitda?.toString().includes(term) ||
        report.netIncome?.toString().includes(term)
      ) {
        return true;
      }
      return false;
    });

    setFilteredReports(filtered.length > 0 ? filtered : []);
  };

  return (
    <div className="flex min-h-screen flex-col bg-blue-50">
      <header
        className="sticky top-0 z-50 border-b bg-blue-100 backdrop-blur"
        style={{ display: "flex", justifyContent: "center" }}
      >
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl">
            <a href="/" style={{ cursor: "pointer" }}>
              <span className="text-blue-600">FinAI</span>
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
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                />
              </div>
              <Button
                variant="outline"
                size="icon"
                className="border-blue-200 text-blue-600 hover:bg-blue-100"
                onClick={() => {
                  setSearchTerm("");
                  setFilteredReports(reports);
                }}
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
              {Array.isArray(filteredReports) ? (
                filteredReports.length > 0 ? (
                  filteredReports.map((report, index) => (
                    <Card key={index} className="border-blue-200">
                      <CardContent>
                        <ReportSummary
                          company={report.companyName}
                          date={report.analysis_date}
                          revenue={report.revenue}
                          ebitda={report.ebitda}
                          netIncome={report.netIncome}
                        />
                        <div className="flex justify-end mt-4">
                          <a href={`/analysis/${report?.custom_id}`}>
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
                  ))
                ) : (
                  <h1 style={{ textAlign: "center", marginTop: "20%" }}>
                    No reports match your search
                  </h1>
                )
              ) : (
                <h1 style={{ textAlign: "center", marginTop: "20%" }}>
                  No Reports Added
                </h1>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}