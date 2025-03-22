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

// Remove components that use super expressions incorrectly
// import { FinancialMetricsChart } from "@/components/financial-metrics-chart";
// import { FinancialRatiosTable } from "@/components/financial-ratios-table";
// import { RecentDocuments } from "@/components/recent-documents";

export default function Dashboard() {
  return (
    <div className="flex min-h-screen flex-col bg-blue-50">
      <header
        className="sticky top-0 z-50 border-b bg-blue-100/95 backdrop-blur"
        style={{ display: "flex", justifyContent: "center" }}
      >
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl">
            <Link href="/" style={{ cursor: "pointer" }}>
              <span className="text-blue-600">Fin</span>
              <span className="text-blue-900">Analyzer</span>
            </Link>
          </div>
          <nav className="flex items-center gap-6">
            <Link
              href="/dashboard"
              className="text-sm font-medium text-blue-800 hover:text-blue-600"
            >
              Dashboard
            </Link>
            <Link
              href="/reports"
              className="text-sm font-medium text-blue-800 hover:text-blue-600"
            >
              Reports
            </Link>
            <Link
              href="/settings"
              className="text-sm font-medium text-blue-800 hover:text-blue-600"
            >
              Settings
            </Link>
            <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </Button>
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
              Financial Dashboard
            </h1>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="hover:text-blue-500 hover:border-blue-500"
              >
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
              <Button size="sm" className="bg-blue-500 hover:bg-blue-600">
                <FileText className="mr-2 h-4 w-4" />
                Generate Report
              </Button>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-3 mb-6">
            <Card className="border-blue-200">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Revenue</CardTitle>
                <TrendingUp className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-500">$4.2M</div>
                <p className="text-xs text-muted-foreground">
                  +12.5% from previous year
                </p>
              </CardContent>
            </Card>
            <Card className="border-blue-200">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">EBITDA</CardTitle>
                <BarChart3 className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-500">$1.8M</div>
                <p className="text-xs text-muted-foreground">
                  +8.3% from previous year
                </p>
              </CardContent>
            </Card>
            <Card className="border-blue-200">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  Working Capital
                </CardTitle>
                <svg
                  className="h-4 w-4 text-blue-500"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-500">$2.4M</div>
                <p className="text-xs text-muted-foreground">
                  +5.2% from previous year
                </p>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="overview" className="mb-6">
            <TabsList className="bg-blue-50">
              <TabsTrigger
                value="overview"
                className="data-[state=active]:bg-blue-500 data-[state=active]:text-white"
              >
                Overview
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
            <TabsContent value="overview" className="space-y-6">
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle>Financial Performance</CardTitle>
                  <CardDescription>
                    Key financial metrics over the last 3 years
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[300px]">
                  {/* Removed FinancialMetricsChart component */}
                  <div className="flex items-center justify-center h-full">
                    <p className="text-muted-foreground">Chart loading...</p>
                  </div>
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
                    {/* Removed FinancialRatiosTable component */}
                    <div className="text-center text-muted-foreground">
                      Loading ratios...
                    </div>
                  </CardContent>
                </Card>
                <Card className="border-blue-200">
                  <CardHeader>
                    <CardTitle>Recent Documents</CardTitle>
                    <CardDescription>
                      Recently analyzed financial statements
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {/* Removed RecentDocuments component */}
                    <div className="text-center text-muted-foreground">
                      Loading documents...
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
                    The company has shown consistent revenue growth over the
                    past 3 years, with a CAGR of 15.2%. Operating expenses have
                    been well-managed, resulting in improved profit margins.
                  </p>
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium mb-1">
                        Revenue Breakdown
                      </h3>
                      <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 w-[65%]"></div>
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>Product Sales (65%)</span>
                        <span>Services (35%)</span>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium mb-1">
                        Expense Allocation
                      </h3>
                      <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 w-[40%]"></div>
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>COGS (40%)</span>
                        <span>Operating Expenses (35%)</span>
                        <span>Other (25%)</span>
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
                    The company maintains a strong balance sheet with a healthy
                    asset-to-liability ratio of 2.3:1. Current assets provide
                    adequate coverage for short-term obligations.
                  </p>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <h3 className="text-sm font-medium mb-2">
                        Assets Composition
                      </h3>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs">Current Assets</span>
                          <span className="text-xs font-medium">45%</span>
                        </div>
                        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[45%]"></div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs">Fixed Assets</span>
                          <span className="text-xs font-medium">35%</span>
                        </div>
                        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[35%]"></div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs">Other Assets</span>
                          <span className="text-xs font-medium">20%</span>
                        </div>
                        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[20%]"></div>
                        </div>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium mb-2">
                        Liabilities & Equity
                      </h3>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs">Current Liabilities</span>
                          <span className="text-xs font-medium">25%</span>
                        </div>
                        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[25%]"></div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs">Long-term Liabilities</span>
                          <span className="text-xs font-medium">30%</span>
                        </div>
                        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[30%]"></div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs">Equity</span>
                          <span className="text-xs font-medium">45%</span>
                        </div>
                        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 w-[45%]"></div>
                        </div>
                      </div>
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
                  <p className="text-sm text-muted-foreground mb-4">
                    The company generated strong operating cash flows of $3.2M,
                    representing a 18% increase from the previous year. Capital
                    expenditures were focused on technology infrastructure and
                    capacity expansion.
                  </p>
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium mb-1">
                        Cash Flow from Operations
                      </h3>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs">$3.2M</span>
                        <span className="text-xs text-blue-500">+18% YoY</span>
                      </div>
                      <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 w-[80%]"></div>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium mb-1">
                        Cash Flow from Investing
                      </h3>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs">-$1.8M</span>
                        <span className="text-xs text-blue-500">+25% YoY</span>
                      </div>
                      <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 w-[45%]"></div>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium mb-1">
                        Cash Flow from Financing
                      </h3>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs">-$0.5M</span>
                        <span className="text-xs text-blue-500">-10% YoY</span>
                      </div>
                      <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 w-[12%]"></div>
                      </div>
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
                  The company demonstrates strong financial health with
                  consistent revenue growth and improving profitability metrics.
                  Key strengths include efficient working capital management and
                  healthy cash flow generation. Areas for potential improvement
                  include reducing the debt-to-equity ratio and optimizing
                  inventory turnover.
                </p>
                <div className="mt-4 space-y-2">
                  <h3 className="text-sm font-medium">Key Strengths</h3>
                  <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                    <li>Strong revenue growth (15.2% CAGR)</li>
                    <li>Improving EBITDA margins (42.8%)</li>
                    <li>Healthy cash flow generation</li>
                    <li>Efficient working capital management</li>
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
                    <h3 className="text-sm font-medium mb-1">
                      Risk Assessment
                    </h3>
                    <div className="flex items-center space-x-2">
                      <div className="h-2 w-full bg-blue-100 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 w-[35%]"></div>
                      </div>
                      <span className="text-xs font-medium">Low-Medium</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">Recommendations</h3>
                    <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                      <li>
                        Reduce debt-to-equity ratio to improve financial
                        stability
                      </li>
                      <li>
                        Optimize inventory management to improve turnover ratio
                      </li>
                      <li>
                        Consider diversifying revenue streams to reduce
                        concentration risk
                      </li>
                      <li>
                        Implement cost control measures to further improve
                        EBITDA margins
                      </li>
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
