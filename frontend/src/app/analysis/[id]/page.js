"use client"; // Add this directive to make it a Client Component

import { ArrowLeft, Download, FileText } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation"; // Use next/navigation instead of next/router
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FinancialMetricsChart } from "@/components/financial-metrics-chart";
import { FinancialRatiosTable } from "@/components/financial-ratios-table";

export default function AnalysisPage({ params }) {
  const router = useRouter(); // Access the router
  const { id } = params; // Access the dynamic route parameter `id`
    console.log(id);
  return (
    <div className="flex min-h-screen flex-col" >
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur" style={{"display":"flex","justifyContent":"center"}}>
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl">
          <a href="/" style={{"cursor":"pointer"}}>
            <span className="text-primary">Fin</span>
            <span>Analyzer</span>
            </a>
          </div>
          <nav className="flex items-center gap-6">
            <Link href="/dashboard" className="text-sm font-medium text-muted-foreground">
              Dashboard
            </Link>
            <Link href="/reports" className="text-sm font-medium text-muted-foreground">
              Reports
            </Link>
            <Link href="/settings" className="text-sm font-medium text-muted-foreground">
              Settings
            </Link>
            <Button size="sm" variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </nav>
        </div>
      </header>
      <main className="flex py-8"  style={{"flexDirection":"column","alignItems":"center"}}>
        <div className="container">
          <div className="mb-8">
            <Link
              href="/dashboard"
              className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
            >
              <ArrowLeft className="mr-1 h-4 w-4" />
              Back to Dashboard
            </Link>
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold">Amazon Financial Analysis</h1>
              <Button>
                <FileText className="mr-2 h-4 w-4" />
                Generate Full Report
              </Button>
            </div>
            <p className="text-muted-foreground mt-2">Analysis completed on March 15, 2023</p>
          </div>

          <Tabs defaultValue="summary" className="mb-8">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="business">Business Overview</TabsTrigger>
              <TabsTrigger value="income">Income Statement</TabsTrigger>
              <TabsTrigger value="balance">Balance Sheet</TabsTrigger>
              <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
            </TabsList>
            <TabsContent value="summary">
              <div className="grid gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Key Financial Metrics</CardTitle>
                    <CardDescription>Performance overview for the fiscal year</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground">Revenue</p>
                          <p className="text-2xl font-bold">$514.2B</p>
                          <p className="text-xs text-green-500">+14.2% YoY</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">EBITDA</p>
                          <p className="text-2xl font-bold">$98.7B</p>
                          <p className="text-xs text-green-500">+8.7% YoY</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Net Income</p>
                          <p className="text-2xl font-bold">$30.4B</p>
                          <p className="text-xs text-green-500">+12.3% YoY</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Free Cash Flow</p>
                          <p className="text-2xl font-bold">$25.9B</p>
                          <p className="text-xs text-green-500">+5.8% YoY</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Financial Health Assessment</CardTitle>
                    <CardDescription>Overall financial health and risk analysis</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">Overall Financial Health</span>
                          <span className="text-sm font-medium">Strong</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-green-500 w-[85%]"></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">Liquidity</span>
                          <span className="text-sm font-medium">Excellent</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-green-500 w-[90%]"></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">Solvency</span>
                          <span className="text-sm font-medium">Good</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-green-500 w-[75%]"></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">Profitability</span>
                          <span className="text-sm font-medium">Good</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-green-500 w-[80%]"></div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            <TabsContent value="business">
              <Card>
                <CardHeader>
                  <CardTitle>Business Overview</CardTitle>
                  <CardDescription>AI-generated summary of business performance and outlook</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-medium mb-2">Company Profile</h3>
                      <p className="text-sm text-muted-foreground">
                        Amazon.com, Inc. is an American multinational technology company focusing on e-commerce, cloud
                        computing, digital streaming, and artificial intelligence. It has been referred to as "one of
                        the most influential economic and cultural forces in the world" and is one of the world's most
                        valuable brands.
                      </p>
                    </div>
                    <div>
                      <h3 className="text-lg font-medium mb-2">Key Findings</h3>
                      <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-2">
                        <li>
                          <strong>Strong Revenue Growth:</strong> Amazon continues to demonstrate robust revenue growth
                          across all major business segments, with AWS showing particularly strong performance at 29%
                          YoY growth.
                        </li>
                        <li>
                          <strong>Improving Operating Margins:</strong> Operating margins have improved to 6.1%, up from
                          5.3% in the previous year, indicating enhanced operational efficiency.
                        </li>
                        <li>
                          <strong>Significant R&D Investment:</strong> The company maintains substantial investment in
                          research and development, representing 12.7% of total revenue, focused on AI, robotics, and
                          logistics optimization.
                        </li>
                        <li>
                          <strong>Strong Cash Position:</strong> Amazon maintains a healthy cash position with $76.2B in
                          cash and short-term investments, providing significant flexibility for strategic initiatives.
                        </li>
                      </ul>
                    </div>
                    <div>
                      <h3 className="text-lg font-medium mb-2">Financial Due Diligence</h3>
                      <p className="text-sm text-muted-foreground mb-2">
                        Our financial due diligence reveals a company with strong fundamentals and well-positioned for
                        continued growth. Key areas of strength and potential concern include:
                      </p>
                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <h4 className="text-sm font-medium mb-1">Strengths</h4>
                          <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                            <li>Diversified revenue streams across retail, cloud, and digital services</li>
                            <li>Strong cash flow generation and liquidity position</li>
                            <li>Continued market share gains in e-commerce and cloud computing</li>
                            <li>Robust logistics infrastructure providing competitive advantage</li>
                          </ul>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium mb-1">Areas of Concern</h4>
                          <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                            <li>Increasing competitive pressure in cloud services</li>
                            <li>Regulatory scrutiny and potential antitrust concerns</li>
                            <li>Rising labor costs and unionization efforts</li>
                            <li>Significant capital expenditure requirements</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <div className="grid gap-6 md:grid-cols-2 mb-8">
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Financial Performance Trends</CardTitle>
                <CardDescription>Key financial metrics over the last 3 years</CardDescription>
              </CardHeader>
              <CardContent className="h-[350px]">
                <FinancialMetricsChart />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Key Financial Ratios</CardTitle>
                <CardDescription>Profitability, liquidity, and solvency metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <FinancialRatiosTable />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>AI-Generated Insights</CardTitle>
                <CardDescription>Key observations and recommendations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium mb-1">Key Observations</h3>
                    <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                      <li>Strong revenue growth across all business segments</li>
                      <li>Improving operating margins indicate enhanced efficiency</li>
                      <li>AWS continues to be the primary profit driver</li>
                      <li>International segment showing improved profitability</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium mb-1">Recommendations</h3>
                    <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                      <li>Continue investment in high-growth segments like AWS and advertising</li>
                      <li>Monitor and optimize logistics costs to further improve margins</li>
                      <li>Consider strategic acquisitions in emerging technologies</li>
                      <li>Develop strategies to address regulatory challenges</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Executive Summary</CardTitle>
              <CardDescription>Comprehensive analysis and key takeaways</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Amazon continues to demonstrate strong financial performance with robust revenue growth and improving
                profitability metrics. The company's diversified business model, spanning e-commerce, cloud computing,
                digital advertising, and subscription services, provides multiple growth vectors and resilience against
                market fluctuations.
              </p>
              <p className="text-sm text-muted-foreground mb-4">
                AWS remains the primary profit driver, contributing approximately 74% of operating income despite
                representing only 16% of total revenue. The North American retail segment has shown significant margin
                improvement, while the International segment continues to progress toward profitability.
              </p>
              <p className="text-sm text-muted-foreground">
                The company maintains a strong balance sheet with substantial cash reserves and manageable debt levels.
                Capital expenditures remain elevated as Amazon continues to invest in logistics infrastructure, data
                centers, and technology development. These investments position the company well for sustained long-term
                growth, though they may pressure near-term free cash flow.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}