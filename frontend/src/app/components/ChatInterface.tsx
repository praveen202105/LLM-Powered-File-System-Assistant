import { useState, useRef, useEffect } from 'react';
import { Send, RotateCcw, Loader2, User, Bot } from 'lucide-react';
import { queryAssistant, resetAssistant } from '../lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: any[];
}

interface ChatInterfaceProps {
  backendUrl: string;
}

export function ChatInterface({ backendUrl }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const exampleQueries = [
    "List all files in sample_data/resumes folder",
    "Find resumes mentioning Python and machine learning",
    "Read sample_data/resumes/resume_john_doe.txt and summarize key skills",
    "Search for 'React' across all resume files in sample_data/resumes",
    "Compare the experience levels in all resumes",
    "Create a summary report of all candidates"
  ];

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const result = await queryAssistant(input);
      const assistantMessage: Message = {
        role: 'assistant',
        content: result.response || result.error || 'No response returned.',
        toolCalls: result.tool_calls
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}\n\nBackend: ${backendUrl}`
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const resetConversation = async () => {
    try {
      await resetAssistant();
    } catch {
      // The local assistant is stateless; clearing UI is still useful if reset fails.
    }
    setMessages([]);
  };

  const handleExampleClick = (query: string) => {
    setInput(query);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-2xl mx-auto">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4">
              <Bot className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">Welcome to LLM File Assistant</h2>
            <p className="text-gray-600 mb-8">
              Ask me to read files, search content, create summaries, or manage your file system using natural language.
            </p>

            <div className="w-full">
              <p className="text-sm font-medium text-gray-700 mb-3">Try these examples with the sample resume files:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {exampleQueries.slice(0, 4).map((query, i) => (
                  <button
                    key={i}
                    onClick={() => handleExampleClick(query)}
                    className="p-4 bg-white border border-gray-200 rounded-lg text-left hover:border-blue-500 hover:shadow-md transition-all group"
                  >
                    <p className="text-sm text-gray-700 group-hover:text-blue-700">{query}</p>
                  </button>
                ))}
              </div>

              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-900 font-medium mb-2">Sample Files Ready</p>
                <p className="text-xs text-blue-700">
                  The backend reads resumes from <code className="bg-blue-100 px-1 py-0.5 rounded">sample_data/resumes/</code>.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.map((message, index) => (
              <div key={index} className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}

                <div className={`max-w-[70%] ${message.role === 'user' ? 'order-first' : ''}`}>
                  <div className={`rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200'
                  }`}>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>

                  {message.toolCalls && message.toolCalls.length > 0 && (
                    <div className="mt-2 p-3 bg-gray-100 rounded-lg border border-gray-200">
                      <p className="text-xs font-medium text-gray-600 mb-2">Tools Used:</p>
                      {message.toolCalls.map((call, i) => (
                        <div key={i} className="text-xs text-gray-700">
                          <code className="bg-gray-200 px-1.5 py-0.5 rounded">
                            {call.tool}({JSON.stringify(call.input)})
                          </code>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 bg-gray-300 rounded-lg flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-gray-600" />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="max-w-4xl mx-auto flex gap-3">
          <button
            onClick={resetConversation}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors flex items-center gap-2"
            disabled={isLoading}
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask me to read, search, or manage files..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />

          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
