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
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { api, ApiError } from "@/lib/api";

const MAX_UPLOAD_MB = 20;

function UploadPageContent() {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setError("");
    if (file && file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setError(`File exceeds the ${MAX_UPLOAD_MB}MB upload limit`);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file || null);
  };

  const handleFileUpload = async () => {
    if (!selectedFile || isUploading) return;
    setIsUploading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const data = await api.post("/upload/", formData);
      if (!data?.custom_id) {
        throw new Error("No custom_id received in the response");
      }
      router.push(`/report/${data.custom_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col items-center py-8">
      <div className="container max-w-4xl px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold uppercase tracking-wide mb-2 text-blue-900">
            Upload Financial Documents
          </h1>
          <p className="text-blue-700">
            Upload an annual report or financial statement PDF for AI-powered analysis and
            insights
          </p>
        </div>

        <Card className="mb-8 border-blue-200">
          <CardHeader>
            <CardTitle className="text-blue-900">
              Upload a Financial Document
            </CardTitle>
            <CardDescription className="text-blue-700">
              Drag and drop your PDF or click to browse. We&apos;ll queue it for analysis
              right away.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <div role="alert" className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}
            <div className="border-2 border-dashed border-blue-300 rounded-lg p-12 text-center hover:bg-blue-50 transition-colors cursor-pointer">
              <Upload className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <p className="text-blue-700 mb-2">
                Drag and drop your file here or click to browse
              </p>
              <p className="text-xs text-blue-600 mb-4">
                PDF only, up to {MAX_UPLOAD_MB}MB
              </p>
              <input
                type="file"
                id="file-upload"
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf,application/pdf"
              />
              <Button
                className="bg-blue-600 hover:bg-blue-700"
                onClick={() =>
                  document.getElementById("file-upload").click()
                }
              >
                <FileText className="mr-2 h-4 w-4" />
                Select File
              </Button>
              {selectedFile && (
                <div className="mt-4">
                  <p className="text-sm text-blue-700 mb-2 break-words">
                    Selected: {selectedFile.name}
                  </p>
                  <Button
                    className="bg-blue-600 hover:bg-blue-700"
                    onClick={handleFileUpload}
                    disabled={isUploading}
                  >
                    {isUploading
                      ? "Queuing for analysis..."
                      : "Upload and Analyze"}
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <h2 className="text-xl font-semibold uppercase tracking-wide text-blue-900">
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
    </div>
  );
}

export default function UploadPage() {
  return (
    <AppShell>
      <UploadPageContent />
    </AppShell>
  );
}
