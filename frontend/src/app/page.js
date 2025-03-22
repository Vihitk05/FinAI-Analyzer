import { Upload } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
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
            <Link href="/" className="text-sm font-medium">
              Dashboard
            </Link>
            <Link href="/reports" className="text-sm font-medium text-muted-foreground">
              Reports
            </Link>
            <Link href="/settings" className="text-sm font-medium text-muted-foreground">
              Settings
            </Link>
            <Button size="sm">Get Started</Button>
          </nav>
        </div>
      </header>
      <main className="flex" style={{"flexDirection":"column","alignItems":"center"}}>
        <section className="container py-12">
          <div className="grid gap-6 lg:grid-cols-1">
            <div className="space-y-4">
              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
                AI-Powered Financial Statement Analysis
              </h1>
              <p className="text-muted-foreground md:text-xl">
                Automate the extraction and analysis of financial statements with advanced AI. Get real-time insights
                and actionable recommendations.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Button size="lg">Upload Documents</Button>
                <Button size="lg" variant="outline">
                  View Demo
                </Button>
              </div>
            </div>
            {/* <div className="flex items-center justify-center">
              <img
                src="/home.jpeg?height=400&width=500"
                alt="Financial Analysis Dashboard"
                className="rounded-lg shadow-lg"
              />
            </div> */}
          </div>
        </section>

        <section className="container py-12 border-t">
          <h2 className="text-2xl font-bold tracking-tight mb-8">How It Works</h2>
          <div className="grid gap-6 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Upload Financial Documents</CardTitle>
                <CardDescription>Upload PDFs, spreadsheets, or scanned financial statements.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-center">
                  <Upload className="h-16 w-16 text-primary" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>AI-Powered Analysis</CardTitle>
                <CardDescription>Our AI extracts and analyzes key financial data.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-center">
                  <svg
                    className="h-16 w-16 text-primary"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6"></path>
                    <line x1="2" y1="20" x2="2" y2="20"></line>
                  </svg>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Comprehensive Reports</CardTitle>
                <CardDescription>Get detailed insights and actionable recommendations.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-center">
                  <svg
                    className="h-16 w-16 text-primary"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                  </svg>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="bg-muted py-12" style={{"display":"flex","justifyContent":"center","width":"100%"}}>
          <div className="container">
            <h2 className="text-2xl font-bold tracking-tight mb-8">Try It Now</h2>
            <div className="grid gap-6 lg:grid-cols-1 ">
              <div className="space-y-6" style={{"display":"flex","justifyContent":"space-around","alignItems":"center"}}>
                <Card>
                  <CardHeader>
                    <CardTitle>Recent Analyses</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      <li className="flex items-center justify-between">
                        <span className="text-sm">Amazon Financial Report 2023</span>
                        <Button variant="ghost" size="sm">
                          View
                        </Button>
                      </li>
                      <li className="flex items-center justify-between">
                        <span className="text-sm">Tesla Q2 Financial Statement</span>
                        <Button variant="ghost" size="sm">
                          View
                        </Button>
                      </li>
                      <li className="flex items-center justify-between">
                        <span className="text-sm">Microsoft Annual Report</span>
                        <Button variant="ghost" size="sm">
                          View
                        </Button>
                      </li>
                    </ul>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Quick Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <Button className="w-full" variant="outline">
                        Balance Sheet Analysis
                      </Button>
                      <Button className="w-full" variant="outline">
                        Income Statement Review
                      </Button>
                      <Button className="w-full" variant="outline">
                        Cash Flow Assessment
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </section>
      </main>
      <footer className="border-t py-6" style={{"display":"flex","justifyContent":"center"}}>
        <div className="container flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-sm text-muted-foreground">© 2025 FinAnalyzer. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <Link href="/terms" className="text-sm text-muted-foreground hover:underline">
              Terms of Service
            </Link>
            <Link href="/privacy" className="text-sm text-muted-foreground hover:underline">
              Privacy Policy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}