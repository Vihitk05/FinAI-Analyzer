import { Download, FileText, Filter, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ReportSummary } from "@/components/report-summary";

export default function ReportsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur" style={{"display":"flex","justifyContent":"center"}}>
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl">
          <a href="/" style={{"cursor":"pointer"}}>
            <span className="text-primary">Fin</span>
            <span>Analyzer</span>
            </a>
          </div>
          <nav className="flex items-center gap-6">
            <a href="/dashboard" className="text-sm font-medium text-muted-foreground">
              Dashboard
            </a>
            <a href="/reports" className="text-sm font-medium">
              Reports
            </a>
            <a href="/settings" className="text-sm font-medium text-muted-foreground">
              Settings
            </a>
            <a href="/upload">
            <Button size="sm" variant="outline">
              <FileText className="mr-2 h-4 w-4" />
              New Report
            </Button>
            </a>
          </nav>
        </div>
      </header>
      <main className="flex py-8"  style={{"flexDirection":"column","alignItems":"center"}}>
        <div className="container">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold">Financial Reports</h1>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input type="search" placeholder="Search reports..." className="w-[200px] pl-8 md:w-[300px]" />
              </div>
              <Button variant="outline" size="icon">
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <Tabs defaultValue="all" className="mb-6">
            <TabsList>
              <TabsTrigger value="all">All Reports</TabsTrigger>
              <TabsTrigger value="income">Income Statement</TabsTrigger>
              <TabsTrigger value="balance">Balance Sheet</TabsTrigger>
              <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
              <TabsTrigger value="custom">Custom Reports</TabsTrigger>
            </TabsList>
            <TabsContent value="all" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Amazon Financial Analysis</CardTitle>
                  <CardDescription>Comprehensive analysis of Amazon's 2023 financial statements</CardDescription>
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
                    <Button variant="outline" size="sm" className="mr-2">
                      <Download className="mr-2 h-4 w-4" />
                      Download
                    </Button>
                    <a href="/analysis/1">
                    <Button size="sm">View Full Report</Button>
                    </a>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Tesla Q2 Financial Analysis</CardTitle>
                  <CardDescription>Quarterly financial performance analysis for Tesla</CardDescription>
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
                    <Button variant="outline" size="sm" className="mr-2">
                      <Download className="mr-2 h-4 w-4" />
                      Download
                    </Button>
                    <Button size="sm">View Full Report</Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Microsoft Annual Report Analysis</CardTitle>
                  <CardDescription>Comprehensive analysis of Microsoft's annual financial statements</CardDescription>
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
                    <Button variant="outline" size="sm" className="mr-2">
                      <Download className="mr-2 h-4 w-4" />
                      Download
                    </Button>
                    <Button size="sm">View Full Report</Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="income">
              <div className="grid gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Revenue Analysis Report</CardTitle>
                    <CardDescription>Detailed breakdown of revenue streams and growth trends</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      This report provides a comprehensive analysis of revenue sources, growth patterns, and market
                      segment performance.
                    </p>
                    <Button size="sm">View Report</Button>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Expense Analysis Report</CardTitle>
                    <CardDescription>
                      Detailed breakdown of expense categories and optimization opportunities
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      This report analyzes expense patterns, identifies cost drivers, and provides recommendations for
                      expense optimization.
                    </p>
                    <Button size="sm">View Report</Button>
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