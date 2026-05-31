import { useState } from 'react';
import { FileText, FolderOpen, FilePlus, Search } from 'lucide-react';
import { runTool } from '../lib/api';

interface DirectToolsProps {
  backendUrl: string;
}

export function DirectTools({ backendUrl }: DirectToolsProps) {
  const [activeTab, setActiveTab] = useState<'read' | 'list' | 'write' | 'search'>('read');
  const [result, setResult] = useState<any>(null);

  // Read File
  const [readPath, setReadPath] = useState('sample_data/resumes/resume_john_doe.txt');

  // List Files
  const [listDir, setListDir] = useState('sample_data/resumes');
  const [listExt, setListExt] = useState('.txt');

  // Write File
  const [writePath, setWritePath] = useState('output/summary.txt');
  const [writeContent, setWriteContent] = useState('Resume Summary Report\n\nCandidate: John Doe\nPosition: Senior Software Engineer\nKey Skills: Python, React, Machine Learning\n\nRecommendation: Strong candidate for senior engineering role.');

  // Search File
  const [searchPath, setSearchPath] = useState('sample_data/resumes/resume_john_doe.txt');
  const [searchKeyword, setSearchKeyword] = useState('Python');

  const executeTool = async (tool: 'read' | 'list' | 'write' | 'search', params: Record<string, unknown>) => {
    setResult({ loading: true });

    try {
      const response = await runTool(tool, params);
      setResult(response);
    } catch (error) {
      setResult({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  };

  const renderResult = () => {
    if (!result) return null;
    if (result.loading) return <div className="text-gray-500">Loading...</div>;
    if (result.error) return <div className="text-red-600">Error: {result.error}</div>;

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="font-medium mb-2">Result:</h3>
        <pre className="bg-gray-50 p-3 rounded text-sm overflow-auto max-h-96">
          {JSON.stringify(result, null, 2)}
        </pre>
      </div>
    );
  };

  const tabs = [
    { id: 'read' as const, label: 'Read File', icon: FileText },
    { id: 'list' as const, label: 'List Files', icon: FolderOpen },
    { id: 'write' as const, label: 'Write File', icon: FilePlus },
    { id: 'search' as const, label: 'Search', icon: Search }
  ];

  return (
    <div className="h-full flex">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 p-4">
        <h2 className="font-semibold mb-4">File System Tools</h2>
        <div className="space-y-1">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6 overflow-auto">
        <div className="max-w-3xl">
          {activeTab === 'read' && (
            <div>
              <h2 className="text-2xl font-semibold mb-2">Read File</h2>
              <p className="text-gray-600 mb-6">Read the contents of a file (supports PDF, DOCX, TXT)</p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">File Path</label>
                  <input
                    type="text"
                    value={readPath}
                    onChange={(e) => setReadPath(e.target.value)}
                    placeholder="e.g., sample_data/resumes/resume_john_doe.txt"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <button
                  onClick={() => executeTool('read', { filepath: readPath })}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Read File
                </button>

                {renderResult()}
              </div>
            </div>
          )}

          {activeTab === 'list' && (
            <div>
              <h2 className="text-2xl font-semibold mb-2">List Files</h2>
              <p className="text-gray-600 mb-6">List all files in a directory with optional filtering</p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Directory Path</label>
                  <input
                    type="text"
                    value={listDir}
                    onChange={(e) => setListDir(e.target.value)}
                    placeholder="e.g., sample_data/resumes"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Extension Filter (Optional)</label>
                  <input
                    type="text"
                    value={listExt}
                    onChange={(e) => setListExt(e.target.value)}
                    placeholder="e.g., .pdf or .txt"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <button
                  onClick={() => executeTool('list', { directory: listDir, extension: listExt || undefined })}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  List Files
                </button>

                {renderResult()}
              </div>
            </div>
          )}

          {activeTab === 'write' && (
            <div>
              <h2 className="text-2xl font-semibold mb-2">Write File</h2>
              <p className="text-gray-600 mb-6">Write content to a file (creates directories if needed)</p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">File Path</label>
                  <input
                    type="text"
                    value={writePath}
                    onChange={(e) => setWritePath(e.target.value)}
                    placeholder="e.g., output/summary.txt"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Content</label>
                  <textarea
                    value={writeContent}
                    onChange={(e) => setWriteContent(e.target.value)}
                    placeholder="Enter content to write..."
                    rows={8}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <button
                  onClick={() => executeTool('write', { filepath: writePath, content: writeContent })}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Write File
                </button>

                {renderResult()}
              </div>
            </div>
          )}

          {activeTab === 'search' && (
            <div>
              <h2 className="text-2xl font-semibold mb-2">Search in File</h2>
              <p className="text-gray-600 mb-6">Search for keywords in a file (case-insensitive)</p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">File Path</label>
                  <input
                    type="text"
                    value={searchPath}
                    onChange={(e) => setSearchPath(e.target.value)}
                    placeholder="e.g., sample_data/resumes/resume_john_doe.txt"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Keyword</label>
                  <input
                    type="text"
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    placeholder="e.g., Python"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <button
                  onClick={() => executeTool('search', { filepath: searchPath, keyword: searchKeyword })}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Search
                </button>

                {renderResult()}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
