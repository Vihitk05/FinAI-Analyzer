import { FileText, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function UploadPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur"  style={{"display":"flex","justifyContent":"center"}}>
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
            <a href="/reports" className="text-sm font-medium text-muted-foreground">
              Reports
            </a>
            <a href="/settings" className="text-sm font-medium text-muted-foreground">
              Settings
            </a>
            <Button size="sm">
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </Button>
          </nav>
        </div>
      </header>
      <main className="flex py-8" style={{"flexDirection":"column","alignItems":"center"}}>
        <div className="container max-w-4xl">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Upload Financial Documents</h1>
            <p className="text-muted-foreground">
              Upload your financial statements for AI-powered analysis and insights
            </p>
          </div>

          <Tabs defaultValue="upload" className="mb-8">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="upload">Upload Files</TabsTrigger>
              <TabsTrigger value="url">Import from URL</TabsTrigger>
            </TabsList>
            <TabsContent value="upload">
              <Card>
                <CardHeader>
                  <CardTitle>Upload Financial Documents</CardTitle>
                  <CardDescription>Drag and drop your financial statements or click to browse</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-12 text-center hover:bg-muted/50 transition-colors cursor-pointer">
                    <Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground mb-2">Drag and drop your files here or click to browse</p>
                    <p className="text-xs text-muted-foreground mb-4">
                      Supports PDF, Excel, CSV, and scanned documents
                    </p>
                    <Button>
                      <FileText className="mr-2 h-4 w-4" />
                      Select Files
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="url">
              <Card>
                <CardHeader>
                  <CardTitle>Import from URL</CardTitle>
                  <CardDescription>Enter the URL of the financial document or data source</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid gap-2">
                      <label htmlFor="url" className="text-sm font-medium">
                        Document URL
                      </label>
                      <input
                        id="url"
                        placeholder="https://example.com/financial-statement.pdf"
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      />
                    </div>
                    <Button>Import Document</Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Supported Document Types</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Financial Statements</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                    <li>Balance Sheets</li>
                    <li>Income Statements</li>
                    <li>Cash Flow Statements</li>
                    <li>Statement of Changes in Equity</li>
                  </ul>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Annual Reports</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                    <li>10-K Reports</li>
                    <li>Annual Shareholder Reports</li>
                    <li>Integrated Reports</li>
                    <li>ESG Reports</li>
                  </ul>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Other Documents</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-muted-foreground list-disc pl-5 space-y-1">
                    <li>Quarterly Reports (10-Q)</li>
                    <li>Management Discussion & Analysis</li>
                    <li>Audit Reports</li>
                    <li>Financial Footnotes</li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}