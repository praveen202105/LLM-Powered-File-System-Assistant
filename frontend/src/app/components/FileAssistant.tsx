import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ChatInterface } from './ChatInterface';
import { DirectTools } from './DirectTools';
import { FileBrowser } from './FileBrowser';
import { API_BASE_URL } from '../lib/api';
import { FileText, MessageSquare, Wrench } from 'lucide-react';

export function FileAssistant() {
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-xl text-gray-900">LLM File Assistant</h1>
              <p className="text-sm text-gray-500">AI-powered file system operations</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <Tabs defaultValue="chat" className="h-full flex flex-col">
          <div className="border-b border-gray-200 bg-white px-6">
            <TabsList className="inline-flex h-12 items-center gap-2">
              <TabsTrigger value="chat" className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                Chat Interface
              </TabsTrigger>
              <TabsTrigger value="tools" className="flex items-center gap-2">
                <Wrench className="w-4 h-4" />
                Direct Tools
              </TabsTrigger>
              <TabsTrigger value="browser" className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                File Browser
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-hidden">
            <TabsContent value="chat" className="h-full m-0">
              <ChatInterface backendUrl={API_BASE_URL} />
            </TabsContent>

            <TabsContent value="tools" className="h-full m-0">
              <DirectTools backendUrl={API_BASE_URL} />
            </TabsContent>

            <TabsContent value="browser" className="h-full m-0">
              <FileBrowser backendUrl={API_BASE_URL} />
            </TabsContent>
          </div>
        </Tabs>
      </main>
    </div>
  );
}
