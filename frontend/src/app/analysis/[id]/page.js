"use client"; // Add this directive to make it a Client Component

import { useState, useEffect, use } from "react";
import { ArrowLeft, Download, FileText } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation"; // Use next/navigation instead of next/router
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

export default function AnalysisPage({ params }) {
  const router = useRouter(); // Access the router
  const { id } = use(params); // Unwrap params with React.use() before destructuring
  const [loading, setLoading] = useState(true);
  const [companyData, setCompanyData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCompanyData = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `http://127.0.0.1:5000/fetch_data?custom_id=${id}`,
        );

        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }

        const data = await response.json();
        setCompanyData(data);
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch company data:", err);
        setError(err.message);
        setLoading(false);
      }
    };

    if (id) {
      fetchCompanyData();
    }
  }, [id]);

  // Show loading state
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-lg text-blue-900">Loading analysis data...</p>
        </div>
      </div>
    );
  }

  // Show error state
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
              onClick={() => router.push("/dashboard")}
            >
              Return to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Format currency (in thousands)
  const formatCurrency = (value) => {
    if (!value) return "$0";
    return `$${(value / 1000).toFixed(1)}K`;
  };

  // Format percentage
  const formatPercentage = (value) => {
    if (value === undefined || value === null) return "0%";
    return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header
        className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur"
        style={{ display: "flex", justifyContent: "center" }}
      >
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl">
            <Link href="/" style={{ cursor: "pointer" }}>
              <span className="text-blue-500">Fin</span>
              <span>Analyzer</span>
            </Link>
          </div>
          <nav className="flex items-center gap-6">
            <Link
              href="/dashboard"
              className="text-sm font-medium text-muted-foreground hover:text-blue-500"
            >
              Dashboard
            </Link>
            <Link
              href="/reports"
              className="text-sm font-medium text-muted-foreground hover:text-blue-500"
            >
              Reports
            </Link>
            <Link
              href="/settings"
              className="text-sm font-medium text-muted-foreground hover:text-blue-500"
            >
              Settings
            </Link>
            <Button
              size="sm"
              variant="outline"
              className="text-blue-500 border-blue-500 hover:bg-blue-50"
            >
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </nav>
        </div>
      </header>
      <main
        className="flex py-8"
        style={{ flexDirection: "column", alignItems: "center" }}
      >
        <div className="container">
          <div className="mb-8">
            <Link
              href="/dashboard"
              className="inline-flex items-center text-sm text-blue-500 hover:text-blue-700 mb-4"
            >
              <ArrowLeft className="mr-1 h-4 w-4" />
              Back to Dashboard
            </Link>
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold text-blue-900">
                Sony Financial Analysis
              </h1>
              <Button className="bg-blue-500 hover:bg-blue-600">
                <FileText className="mr-2 h-4 w-4" />
                Generate Full Report
              </Button>
            </div>
            <p className="text-muted-foreground mt-2">
              Analysis completed on March 15, 2023
            </p>
          </div>

          <Tabs defaultValue="summary" className="mb-8">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger
                value="summary"
                className="data-[state=active]:bg-blue-500 data-[state=active]:text-white"
              >
                Summary
              </TabsTrigger>
              <TabsTrigger
                value="business"
                className="data-[state=active]:bg-blue-500 data-[state=active]:text-white"
              >
                Business Overview
              </TabsTrigger>
              <TabsTrigger
                value="income"
                className="data-[state=active]:bg-blue-500 data-[state=active]:text-white"
              >
                Income Statement
              </TabsTrigger>
              <TabsTrigger
                value="balance"
                className="data-[state=active]:bg-blue-500 data-[state=active]:text-white"
              >
                Balance Sheet
              </TabsTrigger>
              <TabsTrigger
                value="cashflow"
                className="data-[state=active]:bg-blue-500 data-[state=active]:text-white"
              >
                Cash Flow
              </TabsTrigger>
            </TabsList>
            <TabsContent value="summary">
              <div className="grid gap-6 md:grid-cols-2">
                <Card className="border-blue-100">
                  <CardHeader>
                    <CardTitle className="text-blue-900">
                      Key Financial Metrics
                    </CardTitle>
                    <CardDescription>
                      Performance overview for the fiscal year
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground">
                            Revenue
                          </p>
                          <p className="text-2xl font-bold text-blue-900">
                            {formatCurrency(companyData?.revenue)}
                          </p>
                          <p className="text-xs text-blue-500">
                            {formatPercentage(companyData?.revenueGrowth)} YoY
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">
                            EBITDA
                          </p>
                          <p className="text-2xl font-bold text-blue-900">
                            {formatCurrency(companyData?.ebitda)}
                          </p>
                          <p className="text-xs text-blue-500">
                            {formatPercentage(companyData?.ebitdaGrowth)} YoY
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">
                            Net Income
                          </p>
                          <p className="text-2xl font-bold text-blue-900">
                            {formatCurrency(companyData?.netIncome)}
                          </p>
                          <p className="text-xs text-blue-500">
                            {formatPercentage(companyData?.netIncomeGrowth)} YoY
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">
                            Free Cash Flow
                          </p>
                          <p className="text-2xl font-bold text-blue-900">
                            {formatCurrency(companyData?.freeCashFlow)}
                          </p>
                          <p className="text-xs text-blue-500">
                            {formatPercentage(companyData?.freeCashFlowGrowth)}{" "}
                            YoY
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card className="border-blue-100">
                  <CardHeader>
                    <CardTitle className="text-blue-900">
                      Financial Health Assessment
                    </CardTitle>
                    <CardDescription>
                      Overall financial health and risk analysis
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">
                            Overall Financial Health
                          </span>
                          <span className="text-sm font-medium">
                            {companyData?.overallFinancialHealth || "N/A"}
                          </span>
                        </div>
                        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[75%]"></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">Liquidity</span>
                          <span className="text-sm font-medium">
                            {companyData?.liquidity || "N/A"}
                          </span>
                        </div>
                        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[60%]"></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">Solvency</span>
                          <span className="text-sm font-medium">
                            {companyData?.solvency || "N/A"}
                          </span>
                        </div>
                        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[65%]"></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">
                            Profitability
                          </span>
                          <span className="text-sm font-medium">
                            {companyData?.profitability || "N/A"}
                          </span>
                        </div>
                        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[75%]"></div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            <TabsContent value="business">
              <Card className="border-blue-100">
                <CardHeader>
                  <CardTitle className="text-blue-900">
                    Business Overview
                  </CardTitle>
                  <CardDescription>
                    AI-generated summary of business performance and outlook
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-medium mb-2 text-blue-900">
                        Company Profile
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {companyData?.companyProfile ||
                          "Company profile not available."}
                      </p>
                    </div>
                    <div>
                      <h3 className="text-lg font-medium mb-2 text-blue-900">
                        Key Findings
                      </h3>
                      <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-2">
                        {companyData?.keyFindings?.map((finding, index) => (
                          <li key={index}>
                            <strong className="text-blue-700">
                              {finding.split(":")[0]}:
                            </strong>
                            {finding.includes(":")
                              ? finding.split(":")[1]
                              : finding}
                          </li>
                        )) || <li>No key findings available.</li>}
                      </ul>
                    </div>
                    <div>
                      <h3 className="text-lg font-medium mb-2 text-blue-900">
                        Financial Due Diligence
                      </h3>
                      <p className="text-sm text-muted-foreground mb-2">
                        Our financial due diligence reveals a company with
                        distinct strengths and areas of concern. Key areas
                        include:
                      </p>
                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <h4 className="text-sm font-medium mb-1 text-blue-700">
                            Strengths
                          </h4>
                          <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                            {companyData?.strengths?.map((strength, index) => (
                              <li key={index}>{strength}</li>
                            )) || <li>No strengths data available.</li>}
                          </ul>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium mb-1 text-blue-700">
                            Areas of Concern
                          </h4>
                          <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                            {companyData?.areasOfConcern?.map(
                              (concern, index) => (
                                <li key={index}>{concern}</li>
                              ),
                            ) || <li>No concerns data available.</li>}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="income">
              <Card className="border-blue-100">
                <CardHeader>
                  <CardTitle className="text-blue-900">
                    Income Statement Breakdown
                  </CardTitle>
                  <CardDescription>
                    Revenue and expense allocation by category
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-medium mb-2 text-blue-900">
                        Revenue Breakdown
                      </h3>
                      <div className="grid gap-4 grid-cols-2">
                        {companyData?.incomeStatementRevenueBreakdown?.map(
                          (item, index) => (
                            <div key={index}>
                              <p className="text-sm text-muted-foreground">
                                {item.category}
                              </p>
                              <p className="text-xl font-bold text-blue-900">
                                {formatCurrency(item.amount)}
                              </p>
                            </div>
                          ),
                        )}
                      </div>
                    </div>
                    <div>
                      <h3 className="text-lg font-medium mb-2 text-blue-900">
                        Expense Allocation
                      </h3>
                      <div className="grid gap-4 grid-cols-2">
                        {companyData?.incomeStatementExpenseAllocation?.map(
                          (item, index) => (
                            <div key={index}>
                              <p className="text-sm text-muted-foreground">
                                {item.category}
                              </p>
                              <p className="text-xl font-bold text-blue-900">
                                {formatCurrency(item.amount)}
                              </p>
                            </div>
                          ),
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="balance">
              <Card className="border-blue-100">
                <CardHeader>
                  <CardTitle className="text-blue-900">
                    Balance Sheet Overview
                  </CardTitle>
                  <CardDescription>
                    Assets and liabilities composition
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-medium mb-2 text-blue-900">
                        Assets Composition
                      </h3>
                      <div className="grid gap-4 grid-cols-2">
                        {companyData?.balanceSheetAssetsComposition?.map(
                          (item, index) => (
                            <div key={index}>
                              <p className="text-sm text-muted-foreground">
                                {item.category}
                              </p>
                              <p className="text-xl font-bold text-blue-900">
                                {formatCurrency(item.amount)}
                              </p>
                            </div>
                          ),
                        )}
                      </div>
                    </div>
                    <div>
                      <h3 className="text-lg font-medium mb-2 text-blue-900">
                        Liabilities & Equity
                      </h3>
                      <div className="grid gap-4 grid-cols-2">
                        {companyData?.balanceSheetLiabilitiesEquity?.map(
                          (item, index) => (
                            <div key={index}>
                              <p className="text-sm text-muted-foreground">
                                {item.category}
                              </p>
                              <p className="text-xl font-bold text-blue-900">
                                {formatCurrency(item.amount)}
                              </p>
                            </div>
                          ),
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="cashflow">
              <Card className="border-blue-100">
                <CardHeader>
                  <CardTitle className="text-blue-900">
                    Cash Flow Analysis
                  </CardTitle>
                  <CardDescription>
                    Operating, investing and financing activities
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="grid gap-4 grid-cols-3">
                      <div>
                        <h3 className="text-lg font-medium mb-2 text-blue-900">
                          Operating Activities
                        </h3>
                        <p className="text-2xl font-bold text-blue-900">
                          {formatCurrency(companyData?.cashFlowOperations)}
                        </p>
                      </div>
                      <div>
                        <h3 className="text-lg font-medium mb-2 text-blue-900">
                          Investing Activities
                        </h3>
                        <p className="text-2xl font-bold text-blue-900">
                          {formatCurrency(companyData?.cashFlowInvesting)}
                        </p>
                      </div>
                      <div>
                        <h3 className="text-lg font-medium mb-2 text-blue-900">
                          Financing Activities
                        </h3>
                        <p className="text-2xl font-bold text-blue-900">
                          {formatCurrency(companyData?.cashFlowFinancing)}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <div className="grid gap-6 md:grid-cols-2 mb-8">
            <Card className="md:col-span-2 border-blue-100">
              <CardHeader>
                <CardTitle className="text-blue-900">
                  Financial Performance Trends
                </CardTitle>
                <CardDescription>
                  Key financial metrics over the last years
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[350px]">
                <FinancialMetricsChart
                  data={companyData?.financialMetricsChartData}
                />
              </CardContent>
            </Card>

            <Card className="border-blue-100">
              <CardHeader>
                <CardTitle className="text-blue-900">
                  Key Financial Ratios
                </CardTitle>
                <CardDescription>
                  Profitability, liquidity, and solvency metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FinancialRatiosTable data={companyData?.financialRatios} />
              </CardContent>
            </Card>

            <Card className="border-blue-100">
              <CardHeader>
                <CardTitle className="text-blue-900">
                  AI-Generated Insights
                </CardTitle>
                <CardDescription>
                  Key observations and recommendations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium mb-1 text-blue-700">
                      Key Observations
                    </h3>
                    <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                      {companyData?.keyObservations?.map(
                        (observation, index) => (
                          <li key={index}>{observation}</li>
                        ),
                      ) || <li>No observations available.</li>}
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium mb-1 text-blue-700">
                      Recommendations
                    </h3>
                    <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                      {companyData?.recommendations?.map(
                        (recommendation, index) => (
                          <li key={index}>{recommendation}</li>
                        ),
                      ) || <li>No recommendations available.</li>}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="border-blue-100">
            <CardHeader>
              <CardTitle className="text-blue-900">Executive Summary</CardTitle>
              <CardDescription>
                Comprehensive analysis and key takeaways
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {companyData?.executiveSummary ||
                  "Executive summary not available."}
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
