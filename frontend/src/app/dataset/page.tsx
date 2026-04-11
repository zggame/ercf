"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Database, Upload, CheckCircle2, FileUp } from "lucide-react";
import axios from "axios";

export default function DatasetPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:8000/api/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setStatus(res.data);
    } catch (err) {
      console.error(err);
      alert("Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Public Dataset Manager</h2>
          <p className="text-slate-600">Ingest and map GSE multifamily loan performance data</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="shadow-sm border-slate-200">
          <CardHeader className="bg-slate-50 border-b border-slate-100">
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-blue-600" />
              Manual Upload
            </CardTitle>
            <CardDescription>Upload CSV/Parquet files from Fannie Mae or Freddie Mac</CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer relative">
              <input
                type="file"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                accept=".csv"
                onChange={handleFileChange}
              />
              <FileUp className="w-10 h-10 mx-auto text-slate-400 mb-4" />
              <p className="text-sm font-medium text-slate-700">
                {file ? file.name : "Click or drag file to this area to upload"}
              </p>
              <p className="text-xs text-slate-500 mt-2">CSV files are currently supported in v1.</p>
            </div>
          </CardContent>
          <CardFooter className="bg-slate-50 border-t border-slate-100 p-4">
            <Button
              className="w-full bg-blue-600 hover:bg-blue-700"
              disabled={!file || loading}
              onClick={handleUpload}
            >
              {loading ? "Processing..." : "Upload and Map"}
            </Button>
          </CardFooter>
        </Card>

        <Card className="shadow-sm border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-600" />
              Ingestion Status
            </CardTitle>
            <CardDescription>Current mapping and database metrics</CardDescription>
          </CardHeader>
          <CardContent>
            {status ? (
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-emerald-900">Upload Successful</h4>
                  <p className="text-sm text-emerald-700 mt-1">
                    Successfully mapped <strong>{status.mapped_records}</strong> records to the canonical schema. They are now available in the portfolio analytics engine.
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-sm text-slate-600">
                <p className="mb-4">No recent uploads in this session. The system is currently running with seeded mock data.</p>
                <div className="space-y-2">
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-slate-500">Current Schema Version</span>
                    <span className="font-mono">v1.0.0</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-slate-500">Active Parsers</span>
                    <span>Generic CSV, Mock Seed</span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-sm border-slate-200">
        <CardHeader>
          <CardTitle>Loaded Datasets</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Source</TableHead>
                <TableHead>Filename</TableHead>
                <TableHead>Load Date</TableHead>
                <TableHead className="text-right">Records</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {status && (
                <TableRow>
                  <TableCell className="font-medium">User Upload</TableCell>
                  <TableCell>{file?.name}</TableCell>
                  <TableCell>{new Date().toLocaleDateString()}</TableCell>
                  <TableCell className="text-right">{status.mapped_records}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>
                  </TableCell>
                </TableRow>
              )}
              <TableRow>
                <TableCell className="font-medium">System</TableCell>
                <TableCell>mock_seed_data.py</TableCell>
                <TableCell>System Init</TableCell>
                <TableCell className="text-right">2</TableCell>
                <TableCell>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
