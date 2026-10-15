'use client';

import React, { useState, useEffect } from 'react';
import { 
  FolderGit2, 
  Upload, 
  FileText, 
  FileSpreadsheet, 
  Download, 
  Trash2, 
  Search,
  HardDrive,
  Eye
} from 'lucide-react';
import { FileService } from '@/services/api';

export default function FilesPage() {
  const [files, setFiles] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState('');

  const loadFiles = async () => {
    try {
      const fls = await FileService.listFiles();
      setFiles(fls);
    } catch (e) {}
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await FileService.uploadFile(file);
      await loadFiles();
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const filteredFiles = files.filter(f => f.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FolderGit2 className="w-5 h-5 text-indigo-400" />
            Workspace Files & Data Artifacts
          </h1>
          <p className="text-xs text-slate-400">Sandbox storage for spreadsheets, PDFs, charts, generated reports and tool inputs.</p>
        </div>

        <label className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold cursor-pointer flex items-center gap-2 shadow-md shadow-indigo-600/20 transition-all">
          <Upload className="w-4 h-4" />
          {uploading ? 'Uploading...' : 'Upload Workspace File'}
          <input type="file" onChange={handleFileUpload} className="hidden" />
        </label>
      </div>

      {/* Search Bar */}
      <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200">
        <Search className="w-4 h-4 text-slate-500 mr-2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter workspace files by name..."
          className="bg-transparent w-full focus:outline-none placeholder-slate-500"
        />
      </div>

      {/* Files Grid */}
      {filteredFiles.length === 0 ? (
        <div className="py-16 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
          No files in workspace matching search. Upload files above or run workflows to generate artifacts.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {filteredFiles.map((file) => {
            const isSpreadsheet = ['.xlsx', '.xls', '.csv'].includes(file.extension);
            const isPdf = file.extension === '.pdf';
            const isImage = ['.png', '.jpg', '.jpeg'].includes(file.extension);

            return (
              <div key={file.name} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                      {isSpreadsheet ? (
                        <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
                      ) : isPdf ? (
                        <FileText className="w-5 h-5 text-blue-400" />
                      ) : (
                        <HardDrive className="w-5 h-5 text-indigo-400" />
                      )}
                    </div>
                    <div className="overflow-hidden">
                      <div className="text-xs font-semibold text-slate-200 truncate max-w-[180px]">{file.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{(file.size_bytes / 1024).toFixed(1)} KB</div>
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                    {file.extension.replace('.', '')}
                  </span>

                  <a
                    href={`http://127.0.0.1:8000/artifacts/${file.name}`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 rounded text-xs font-medium flex items-center gap-1 transition-colors"
                  >
                    <Download className="w-3 h-3 text-slate-400" />
                    Download
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
