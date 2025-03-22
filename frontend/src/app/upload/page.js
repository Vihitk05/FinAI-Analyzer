"use client";

import { FileText, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState } from "react";

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [urlValue, setUrlValue] = useState("");

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      alert("Please select a file first!");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Upload successful:", data);
      alert("File uploaded successfully!");
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed: " + error.message);
    }
  };

  const handleUrlUpload = async () => {
    if (!urlValue) {
      alert("Please enter a URL!");
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/upload-url", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: urlValue }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("URL upload successful:", data);
      alert("URL processed successfully!");
    } catch (error) {
      console.error("URL upload failed:", error);
      alert("URL upload failed: " + error.message);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-blue-50">
      <header
        className="sticky top-0 z-50 border-b bg-blue-100/95 backdrop-blur"
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
              className="text-sm font-medium text-blue-800 hover:text-blue-600"
            >
              Dashboard
            </a>
            <a
              href="/reports"
              className="text-sm font-medium text-blue-800 hover:text-blue-600"
            >
              Reports
            </a>
            <a
              href="/settings"
              className="text-sm font-medium text-blue-800 hover:text-blue-600"
            >
              Settings
            </a>
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
        <div className="container max-w-4xl">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2 text-blue-900">
              Upload Financial Documents
            </h1>
            <p className="text-blue-700">
              Upload your financial statements for AI-powered analysis and
              insights
            </p>
          </div>

          <Tabs defaultValue="upload" className="mb-8">
            <TabsList className="grid w-full grid-cols-2 bg-blue-100">
              <TabsTrigger
                value="upload"
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              >
                Upload Files
              </TabsTrigger>
              <TabsTrigger
                value="url"
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              >
                Import from URL
              </TabsTrigger>
            </TabsList>
            <TabsContent value="upload">
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle className="text-blue-900">
                    Upload Financial Documents
                  </CardTitle>
                  <CardDescription className="text-blue-700">
                    Drag and drop your financial statements or click to browse
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="border-2 border-dashed border-blue-300 rounded-lg p-12 text-center hover:bg-blue-50 transition-colors cursor-pointer">
                    <Upload className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                    <p className="text-blue-700 mb-2">
                      Drag and drop your files here or click to browse
                    </p>
                    <p className="text-xs text-blue-600 mb-4">
                      Supports PDF, Excel, CSV, and scanned documents
                    </p>
                    <input
                      type="file"
                      id="file-upload"
                      onChange={handleFileChange}
                      className="hidden"
                      accept=".pdf,.xlsx,.xls,.csv"
                    />
                    <Button
                      className="bg-blue-600 hover:bg-blue-700"
                      onClick={() =>
                        document.getElementById("file-upload").click()
                      }
                    >
                      <FileText className="mr-2 h-4 w-4" />
                      Select Files
                    </Button>
                    {selectedFile && (
                      <Button
                        className="bg-blue-600 hover:bg-blue-700 ml-4"
                        onClick={handleFileUpload}
                      >
                        Upload Selected File
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="url">
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle className="text-blue-900">
                    Import from URL
                  </CardTitle>
                  <CardDescription className="text-blue-700">
                    Enter the URL of the financial document or data source
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid gap-2">
                      <label
                        htmlFor="url"
                        className="text-sm font-medium text-blue-900"
                      >
                        Document URL
                      </label>
                      <input
                        id="url"
                        value={urlValue}
                        onChange={(e) => setUrlValue(e.target.value)}
                        placeholder="https://example.com/financial-statement.pdf"
                        className="flex h-10 w-full rounded-md border border-blue-200 bg-white px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-blue-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      />
                    </div>
                    <Button
                      className="bg-blue-600 hover:bg-blue-700"
                      onClick={handleUrlUpload}
                    >
                      Import Document
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-blue-900">
              Supported Document Types
            </h2>
            <div className="grid gap-4 md:grid-cols-3">
              <Card className="border-blue-200">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base text-blue-900">
                    Financial Statements
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-blue-700 list-disc pl-5 space-y-1">
                    <li>Balance Sheets</li>
                    <li>Income Statements</li>
                    <li>Cash Flow Statements</li>
                    <li>Statement of Changes in Equity</li>
                  </ul>
                </CardContent>
              </Card>
              <Card className="border-blue-200">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base text-blue-900">
                    Annual Reports
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-blue-700 list-disc pl-5 space-y-1">
                    <li>10-K Reports</li>
                    <li>Annual Shareholder Reports</li>
                    <li>Integrated Reports</li>
                    <li>ESG Reports</li>
                  </ul>
                </CardContent>
              </Card>
              <Card className="border-blue-200">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base text-blue-900">
                    Other Documents
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="text-sm text-blue-700 list-disc pl-5 space-y-1">
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
