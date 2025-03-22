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

export default function ReportsPage() {
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
              <TabsTrigger
                value="income"
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              >
                Income Statement
              </TabsTrigger>
              <TabsTrigger
                value="balance"
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              >
                Balance Sheet
              </TabsTrigger>
              <TabsTrigger
                value="cashflow"
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              >
                Cash Flow
              </TabsTrigger>
              <TabsTrigger
                value="custom"
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              >
                Custom Reports
              </TabsTrigger>
            </TabsList>
            <TabsContent value="all" className="space-y-6">
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle className="text-blue-900">
                    Amazon Financial Analysis
                  </CardTitle>
                  <CardDescription className="text-blue-600">
                    Comprehensive analysis of Amazon's 2023 financial statements
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ReportSummary
                    company="Amazon"
                    date="March 15, 2023"
                    revenue="$514.2B"
                    ebitda="$98.7B"
                    netIncome="$30.4B"
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
                    <a href="/analysis/1">
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

              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle className="text-blue-900">
                    Tesla Q2 Financial Analysis
                  </CardTitle>
                  <CardDescription className="text-blue-600">
                    Quarterly financial performance analysis for Tesla
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ReportSummary
                    company="Tesla"
                    date="July 22, 2023"
                    revenue="$24.9B"
                    ebitda="$4.5B"
                    netIncome="$2.7B"
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
                    <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                      View Full Report
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle className="text-blue-900">
                    Microsoft Annual Report Analysis
                  </CardTitle>
                  <CardDescription className="text-blue-600">
                    Comprehensive analysis of Microsoft's annual financial
                    statements
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ReportSummary
                    company="Microsoft"
                    date="October 10, 2023"
                    revenue="$211.9B"
                    ebitda="$99.3B"
                    netIncome="$72.4B"
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
                    <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                      View Full Report
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="income">
              <div className="grid gap-6 md:grid-cols-2">
                <Card className="border-blue-200">
                  <CardHeader>
                    <CardTitle className="text-blue-900">
                      Revenue Analysis Report
                    </CardTitle>
                    <CardDescription className="text-blue-600">
                      Detailed breakdown of revenue streams and growth trends
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-blue-600 mb-4">
                      This report provides a comprehensive analysis of revenue
                      sources, growth patterns, and market segment performance.
                    </p>
                    <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                      View Report
                    </Button>
                  </CardContent>
                </Card>
                <Card className="border-blue-200">
                  <CardHeader>
                    <CardTitle className="text-blue-900">
                      Expense Analysis Report
                    </CardTitle>
                    <CardDescription className="text-blue-600">
                      Detailed breakdown of expense categories and optimization
                      opportunities
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-blue-600 mb-4">
                      This report analyzes expense patterns, identifies cost
                      drivers, and provides recommendations for expense
                      optimization.
                    </p>
                    <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                      View Report
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
