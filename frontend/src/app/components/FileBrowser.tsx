import { useEffect, useState } from 'react';
import { File, Folder, FileText, FileType, Loader2 } from 'lucide-react';
import { runTool } from '../lib/api';

interface FileBrowserProps {
  backendUrl: string;
}

interface FileItem {
  name: string;
  path: string;
  size: number;
  modified: string;
  extension: string;
}

export function FileBrowser({ backendUrl }: FileBrowserProps) {
  const [currentPath, setCurrentPath] = useState('sample_data/resumes');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const normalizeFile = (file: any): FileItem => ({
    name: file.filename || file.name,
    path: file.filepath || file.path,
    size: file.size_bytes || file.size || 0,
    modified: file.modified_date || file.modified || '',
    extension: file.file_type || file.extension || ''
  });

  const browseFiles = async () => {
    setIsLoading(true);
    setError('');

    try {
      const result = await runTool('list', { directory: currentPath, extension: '.txt' });
      const nextFiles = Array.isArray(result) ? result.map(normalizeFile) : [];
      setFiles(nextFiles);
      setSelectedFile(nextFiles[0] || null);
      setPreview(null);
    } catch (err) {
      setFiles([]);
      setSelectedFile(null);
      setPreview(null);
      setError(err instanceof Error ? err.message : 'Unable to browse files');
    } finally {
      setIsLoading(false);
    }
  };

  const readSelectedFile = async (file = selectedFile) => {
    if (!file) return;
    setError('');
    setPreview({ loading: true });

    try {
      const result = await runTool('read', { filepath: file.path });
      setPreview(result);
    } catch (err) {
      setPreview(null);
      setError(err instanceof Error ? err.message : 'Unable to read file');
    }
  };

  useEffect(() => {
    browseFiles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getFileIcon = (extension: string) => {
    switch (extension.toLowerCase()) {
      case '.pdf':
        return <FileType className="w-5 h-5 text-red-500" />;
      case '.docx':
      case '.doc':
        return <FileText className="w-5 h-5 text-blue-500" />;
      case '.txt':
        return <File className="w-5 h-5 text-gray-500" />;
      default:
        return <File className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="h-full flex bg-gray-50">
      {/* File List */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <Folder className="w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={currentPath}
              onChange={(e) => setCurrentPath(e.target.value)}
              className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={browseFiles}
              disabled={isLoading}
              className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-md transition-colors min-w-20 flex justify-center"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Browse'}
            </button>
          </div>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>

        {/* File Table */}
        <div className="flex-1 overflow-auto p-4">
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Modified</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {files.map((file, index) => (
                  <tr
                    key={index}
                    onClick={() => {
                      setSelectedFile(file);
                      setPreview(null);
                    }}
                    className={`cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedFile?.path === file.path ? 'bg-blue-50' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {getFileIcon(file.extension)}
                        <span className="font-medium text-gray-900">{file.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{formatFileSize(file.size)}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{formatDate(file.modified)}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                        {file.extension}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!isLoading && files.length === 0 && (
              <div className="p-6 text-center text-sm text-gray-500">No files found.</div>
            )}
          </div>
        </div>
      </div>

      {/* File Preview */}
      <div className="w-96 bg-white border-l border-gray-200 p-6">
        {selectedFile ? (
          <div>
            <div className="flex items-center gap-3 mb-6">
              {getFileIcon(selectedFile.extension)}
              <h3 className="font-semibold text-lg">{selectedFile.name}</h3>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Path</label>
                <p className="text-sm text-gray-900 break-all">{selectedFile.path}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Size</label>
                <p className="text-sm text-gray-900">{formatFileSize(selectedFile.size)}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Modified</label>
                <p className="text-sm text-gray-900">{formatDate(selectedFile.modified)}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Type</label>
                <p className="text-sm text-gray-900">{selectedFile.extension.toUpperCase()}</p>
              </div>

              <div className="pt-4 space-y-2">
                <button
                  onClick={() => readSelectedFile()}
                  className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  Read File
                </button>
              </div>
            </div>

            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium mb-2">Preview</h4>
              {preview?.loading ? (
                <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              ) : preview?.success ? (
                <pre className="max-h-80 overflow-auto whitespace-pre-wrap text-xs text-gray-700">
                  {preview.content}
                </pre>
              ) : (
                <p className="text-sm text-gray-500">Read a file to preview its contents.</p>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-center">
            <div>
              <File className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Select a file to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
