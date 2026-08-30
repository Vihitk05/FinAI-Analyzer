import { BarChart3, FileText, Upload } from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header
        className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur"
        style={{ display: "flex", justifyContent: "center" }}
      >
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl">
            <Link href="/" className="flex items-center gap-2" style={{ cursor: "pointer" }}>
              <Image
                src="/favicon.ico"
                alt="FinAI Analyzer"
                width={32}
                height={32}
                className="h-8 w-8 rounded-md"
                priority
              />
              <span className="text-blue-500">FinAI</span>
              <span>Analyzer</span>
            </Link>
          </div>
          <nav className="flex items-center gap-6">
            <Link href="/login" className="text-sm font-medium text-blue-500">
              Sign in
            </Link>
            <Link href="/signup">
              <Button size="sm" className="bg-blue-500 hover:bg-blue-600">
                Get Started
              </Button>
            </Link>
          </nav>
        </div>
      </header>
      <main
        className="flex"
        style={{ flexDirection: "column", alignItems: "center" }}
      >
        <section className="container py-12">
          <div className="grid gap-6 lg:grid-cols-1">
            <div className="space-y-4">
              <h1 className="text-3xl font-bold uppercase tracking-tight sm:text-4xl md:text-5xl text-blue-900">
                AI-Powered Financial Statement Analysis
              </h1>
              <p className="text-blue-700 md:text-xl">
                Automate the extraction and analysis of financial statements
                with advanced AI. Get real-time insights and actionable
                recommendations.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Link href="/upload">
                  <Button
                    size="lg"
                    className="bg-blue-500 hover:bg-transparent hover:text-blue-500 hover:border-2 hover:border-blue-500"
                  >
                    Upload Documents
                  </Button>
                </Link>
                <Link href="/demo">
                  <Button
                    size="lg"
                    variant="outline"
                    className="text-blue-500 border-blue-500"
                  >
                    View Demo
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="container py-12 border-t">
          <h2 className="text-2xl font-bold uppercase tracking-tight mb-8 text-blue-900">
            How It Works
          </h2>
          <div className="grid gap-6 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-blue-800">
                  Upload Financial Documents
                </CardTitle>
                <CardDescription className="text-blue-600">
                  Upload PDFs, spreadsheets, or scanned financial statements.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-center">
                  <Upload className="h-16 w-16 text-blue-500" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-blue-800">
                  AI-Powered Analysis
                </CardTitle>
                <CardDescription className="text-blue-600">
                  Our AI extracts and analyzes key financial data.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-center">
                  <BarChart3 className="h-16 w-16 text-blue-500" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-blue-800">
                  Comprehensive Reports
                </CardTitle>
                <CardDescription className="text-blue-600">
                  Get detailed insights and actionable recommendations.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-center">
                  <FileText className="h-16 w-16 text-blue-500" />
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section
          className="bg-blue-50 py-12"
          style={{ display: "flex", justifyContent: "center", width: "100%" }}
        >
          <div className="container">
            <div
              className="space-y-6"
              style={{
                display: "flex",
                justifyContent: "space-around",
                alignItems: "center",
                width: "100%",
              }}
            >
              <Card className="w-full">
                <CardHeader>
                  <CardTitle className="text-blue-800">
                    Quick Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Button
                      className="w-full text-blue-500 border-blue-500"
                      variant="outline"
                    >
                      Balance Sheet Analysis
                    </Button>
                    <Button
                      className="w-full text-blue-500 border-blue-500"
                      variant="outline"
                    >
                      Income Statement Review
                    </Button>
                    <Button
                      className="w-full text-blue-500 border-blue-500"
                      variant="outline"
                    >
                      Cash Flow Assessment
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>
      </main>
      <footer
        className="border-t py-6"
        style={{ display: "flex", justifyContent: "center" }}
      >
        <div className="container flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-sm text-blue-600">
            (c) 2025 FinAI Analyzer. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
