"use client";

import { useState, useEffect } from "react";
import {
  BarChart3,
  Download,
  FileText,
  TrendingUp,
  Upload,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FinancialMetricsChart } from "@/components/financial-metrics-chart";
import { FinancialRatiosTable } from "@/components/financial-ratios-table";
import { RecentDocuments } from "@/components/recent-documents";

export default function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5000/api/dashboard");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setDashboardData(data);
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-lg text-blue-900">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error Loading Data</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{error}</p>
            <Button
              className="mt-4 bg-blue-500 hover:bg-blue-600"
              onClick={() => window.location.reload()}
            >
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Format currency (in thousands)
  const formatCurrency = (value) => {
    if (typeof value !== 'number' || isNaN(value)) return "$0";
    return `$${(value / 1000).toFixed(1)}K`;
  };

  // Format percentage
  const formatPercentage = (value) => {
    if (typeof value !== 'number' || isNaN(value)) return "0%";
    return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
  };

  // Function to convert health ratings to width percentages
  const getHealthWidth = (value) => {
    switch(value?.toLowerCase()) {
      case 'fair': return 40;
      case 'good': return 60;
      case 'strong': return 80;
      case 'excellent': return 100;
      default: return 0;
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-blue-50">
      <header className="sticky top-0 z-50 border-b bg-blue-100/95 backdrop-blur" style={{"display":"flex","justifyContent":"center"}}>
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl">
            <Link href="/">
              <span className="text-blue-600">FinAI</span>
              <span className="text-blue-900">Analyzer</span>
            </Link>
          </div>
          <nav className="flex items-center gap-6">
            <Link href="/dashboard" className="text-sm font-medium text-blue-800 hover:text-blue-600">
              Dashboard
            </Link>
            <Link href="/reports" className="text-sm font-medium text-blue-800 hover:text-blue-600">
              Reports
            </Link>
            {/* <Link href="/settings" className="text-sm font-medium text-blue-800 hover:text-blue-600">
              Settings
            </Link> */}
            <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </Button>
          </nav>
        </div>
      </header>

      <main className="flex py-8 flex-col items-center">
        <div className="container">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold text-blue-900">
              Financial Dashboard
            </h1>
            <div className="flex items-center gap-2">
              {/* <Button variant="outline" size="sm" className="hover:text-blue-500 hover:border-blue-500">
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
              <Button size="sm" className="bg-blue-500 hover:bg-blue-600">
                <FileText className="mr-2 h-4 w-4" />
                Generate Report
              </Button> */}
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-3 mb-6">
            <Card className="border-blue-200">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Revenue</CardTitle>
                <TrendingUp className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-500">
                  {formatCurrency(dashboardData?.revenue)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {formatPercentage(dashboardData?.revenueGrowth)} from previous year
                </p>
              </CardContent>
            </Card>
            <Card className="border-blue-200">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">EBITDA</CardTitle>
                <BarChart3 className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-500">
                  {formatCurrency(dashboardData?.ebitda)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {formatPercentage(dashboardData?.ebitdaGrowth)} from previous year
                </p>
              </CardContent>
            </Card>
            <Card className="border-blue-200">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Net Income</CardTitle>
                <svg className="h-4 w-4 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-500">
                  {formatCurrency(dashboardData?.netIncome)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {formatPercentage(dashboardData?.netIncomeGrowth)} from previous year
                </p>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="overview" className="mb-6">
            <TabsList className="bg-blue-50">
              <TabsTrigger value="overview" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white">
                Overview
              </TabsTrigger>
              <TabsTrigger value="income" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white">
                Income Statement
              </TabsTrigger>
              <TabsTrigger value="balance" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white">
                Balance Sheet
              </TabsTrigger>
              <TabsTrigger value="cashflow" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white">
                Cash Flow
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle>Financial Performance</CardTitle>
                  <CardDescription>
                    Key financial metrics over time
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[300px]">
                  <FinancialMetricsChart data={dashboardData?.financialMetricsChartData} />
                </CardContent>
              </Card>

              <div className="grid gap-6 md:grid-cols-2">
                <Card className="border-blue-200">
                  <CardHeader>
                    <CardTitle>Key Financial Ratios</CardTitle>
                    <CardDescription>
                      Profitability, liquidity, and solvency metrics
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <FinancialRatiosTable data={dashboardData?.financialRatios} />
                  </CardContent>
                </Card>
                <Card className="border-blue-200">
                  <CardHeader>
                    <CardTitle>Financial Health Assessment</CardTitle>
                    <CardDescription>
                      Overall financial health and risk analysis
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {['overallFinancialHealth', 'liquidity', 'solvency', 'profitability'].map((key) => (
                        <div key={key}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium capitalize">
                              {key.replace(/([A-Z])/g, ' $1').trim()}
                            </span>
                            <span className="text-sm font-medium">
                              {dashboardData?.[key] || "N/A"}
                            </span>
                          </div>
                          <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-blue-500" 
                              style={{ width: `${getHealthWidth(dashboardData?.[key])}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="income">
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle>Income Statement Overview</CardTitle>
                  <CardDescription>
                    Revenue, expenses, and profit analysis
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    {dashboardData?.businessOverviewSummary}
                  </p>
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium mb-1">Revenue Breakdown</h3>
                      <div className="grid gap-4 grid-cols-2">
                        {dashboardData?.incomeStatementRevenueBreakdown?.map((item, index) => (
                          <div key={index}>
                            <p className="text-sm text-muted-foreground">{item.category}</p>
                            <p className="text-xl font-bold text-blue-900">
                              {formatCurrency(item.amount)}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium mb-1">Expense Allocation</h3>
                      <div className="grid gap-4 grid-cols-2">
                        {dashboardData?.incomeStatementExpenseAllocation?.map((item, index) => (
                          <div key={index}>
                            <p className="text-sm text-muted-foreground">{item.category}</p>
                            <p className="text-xl font-bold text-blue-900">
                              {formatCurrency(item.amount)}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="balance">
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle>Balance Sheet Overview</CardTitle>
                  <CardDescription>
                    Assets, liabilities, and equity analysis
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    {dashboardData?.companyProfile}
                  </p>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <h3 className="text-sm font-medium mb-2">Assets Composition</h3>
                      {dashboardData?.balanceSheetAssetsComposition?.map((item, index) => (
                        <div key={index} className="mb-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs">{item.category}</span>
                            <span className="text-xs font-medium">
                              {formatCurrency(item.amount)}
                            </span>
                          </div>
                          <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-blue-500" 
                              style={{ width: `${(item.amount / dashboardData?.totalAssets * 100).toFixed(0)}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div>
                      <h3 className="text-sm font-medium mb-2">Liabilities & Equity</h3>
                      {dashboardData?.balanceSheetLiabilitiesEquity?.map((item, index) => (
                        <div key={index} className="mb-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs">{item.category}</span>
                            <span className="text-xs font-medium">
                              {formatCurrency(item.amount)}
                            </span>
                          </div>
                          <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-blue-500" 
                              style={{ width: `${(item.amount / dashboardData?.totalLiabilitiesEquity * 100).toFixed(0)}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="cashflow">
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle>Cash Flow Overview</CardTitle>
                  <CardDescription>
                    Operating, investing, and financing activities
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 grid-cols-3">
                    <div>
                      <h3 className="text-sm font-medium mb-2">Operating Activities</h3>
                      <p className="text-2xl font-bold text-blue-900">
                        {formatCurrency(dashboardData?.cashFlowOperations)}
                      </p>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium mb-2">Investing Activities</h3>
                      <p className="text-2xl font-bold text-blue-900">
                        {formatCurrency(dashboardData?.cashFlowInvesting)}
                      </p>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium mb-2">Financing Activities</h3>
                      <p className="text-2xl font-bold text-blue-900">
                        {formatCurrency(dashboardData?.cashFlowFinancing)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <div className="grid gap-6 md:grid-cols-2">
            <Card className="border-blue-200">
              <CardHeader>
                <CardTitle>Business Overview</CardTitle>
                <CardDescription>
                  AI-generated summary of business performance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  {dashboardData?.executiveSummary}
                </p>
                <div className="mt-4 space-y-2">
                  <h3 className="text-sm font-medium">Key Strengths</h3>
                  <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                    {dashboardData?.strengths?.map((strength, index) => (
                      <li key={index}>{strength}</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
            <Card className="border-blue-200">
              <CardHeader>
                <CardTitle>Financial Due Diligence</CardTitle>
                <CardDescription>
                  Key findings and recommendations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium mb-1">Risk Assessment</h3>
                    <div className="flex items-center space-x-2">
                      <div className="h-2 w-full bg-blue-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500" 
                          style={{ width: `${dashboardData?.riskAssessment === 'Medium-High' ? '65%' : '35%'}` }}
                        ></div>
                      </div>
                      <span className="text-xs font-medium">{dashboardData?.riskAssessment}</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">Recommendations</h3>
                    <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                      {dashboardData?.recommendations?.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}