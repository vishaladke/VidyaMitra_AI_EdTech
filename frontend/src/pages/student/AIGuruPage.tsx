/**
 * AI Guru Page — main chat interface for students.
 *
 * Features:
 * - Chat bubble layout (student right, AI left)
 * - Typing indicator with shimmer animation
 * - Conversation history sidebar
 * - Safety notice footer
 * - Socket.io real-time messaging
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { History, AlertTriangle, Sparkles, X } from 'lucide-react';
import { useSocket } from '../../hooks/useSocket';
import { ChatBubble } from '../../components/chat/ChatBubble';
import { ChatInput } from '../../components/chat/ChatInput';
import { TypingIndicator } from '../../components/chat/TypingIndicator';

interface Message {
  id: string;
  content: string;
  role: 'student' | 'assistant';
  timestamp: string;
  cacheSource?: string;
}

interface Conversation {
  id: string;
  title: string;
  subject_id?: string;
  created_at?: string;
}

export function AIGuruPage() {
  const { socket, isConnected } = useSocket();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [safetyAlert, setSafetyAlert] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, streamingContent]);

  // Socket.io event listeners
  useEffect(() => {
    if (!socket) return;

    const onTyping = (data: { isTyping: boolean }) => {
      setIsTyping(data.isTyping);
    };

    const onChunk = (data: { content: string; conversationId: string }) => {
      setIsTyping(false);
      setConversationId(data.conversationId);
      setStreamingContent(prev => prev + data.content);
    };

    const onComplete = (data: { conversationId: string; messageId: string; cacheSource: string }) => {
      setIsTyping(false);
      setConversationId(data.conversationId);
      
      // Move streaming content to a finalized message
      setStreamingContent(prev => {
        if (prev) {
          const aiMessage: Message = {
            id: data.messageId || crypto.randomUUID(),
            content: prev,
            role: 'assistant',
            timestamp: new Date().toISOString(),
            cacheSource: data.cacheSource,
          };
          setMessages(msgs => [...msgs, aiMessage]);
        }
        return '';
      });
    };

    const onSafety = (data: { conversationId: string; safetyMessage: string }) => {
      setSafetyAlert(data.safetyMessage);
    };

    const onError = (data: { error: string; code?: string }) => {
      setIsTyping(false);
      setStreamingContent('');
      // Show error as an AI message
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        content: `⚠️ ${data.error}`,
        role: 'assistant',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    };

    const onConversationsList = (data: { conversations: Conversation[] }) => {
      setConversations(data.conversations || []);
    };

    socket.on('ai:chat:typing', onTyping);
    socket.on('ai:chat:chunk', onChunk);
    socket.on('ai:chat:complete', onComplete);
    socket.on('ai:chat:safety', onSafety);
    socket.on('ai:chat:error', onError);
    socket.on('ai:conversations:list', onConversationsList);

    return () => {
      socket.off('ai:chat:typing', onTyping);
      socket.off('ai:chat:chunk', onChunk);
      socket.off('ai:chat:complete', onComplete);
      socket.off('ai:chat:safety', onSafety);
      socket.off('ai:chat:error', onError);
      socket.off('ai:conversations:list', onConversationsList);
    };
  }, [socket]);

  // Load conversation history on mount
  useEffect(() => {
    if (socket && isConnected) {
      socket.emit('ai:conversations:list', { limit: 20 });
    }
  }, [socket, isConnected]);

  const handleSend = useCallback((message: string) => {
    if (!socket || !isConnected) return;

    // Add student message to UI immediately
    const studentMessage: Message = {
      id: crypto.randomUUID(),
      content: message,
      role: 'student',
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, studentMessage]);
    setStreamingContent('');

    // Send to gateway
    socket.emit('ai:chat:send', {
      message,
      conversationId: conversationId || undefined,
    });
  }, [socket, isConnected, conversationId]);

  const startNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setStreamingContent('');
    setShowHistory(false);
  };

  const loadConversation = (convId: string) => {
    setConversationId(convId);
    setMessages([]); // Will be loaded from API
    setShowHistory(false);
  };

  return (
    <div className="h-full flex flex-col" id="ai-guru-page">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
            <Sparkles size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold font-marathi">AI गुरू</h1>
            <p className="text-[11px] text-white/40">
              {isConnected ? (
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                  ऑनलाइन — तुमच्या अभ्यासात मदत करण्यासाठी तयार
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 inline-block" />
                  कनेक्ट होत आहे...
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="p-2.5 rounded-xl hover:bg-white/5 text-white/50 hover:text-white transition-all"
            title="संवाद इतिहास"
          >
            <History size={18} />
          </button>
          <button
            onClick={startNewConversation}
            className="px-3 py-1.5 rounded-xl bg-brand-500/10 text-brand-400 text-xs font-medium
                       hover:bg-brand-500/20 transition-all"
          >
            + नवीन संवाद
          </button>
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Conversation history sidebar */}
        {showHistory && (
          <div className="w-72 border-r border-white/5 bg-surface-900/30 flex flex-col animate-fade-in">
            <div className="flex items-center justify-between p-4 border-b border-white/5">
              <h3 className="text-sm font-semibold font-marathi">संवाद इतिहास</h3>
              <button
                onClick={() => setShowHistory(false)}
                className="p-1 rounded hover:bg-white/5 text-white/40"
              >
                <X size={14} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {conversations.length === 0 ? (
                <p className="text-xs text-white/30 text-center py-8 font-marathi">
                  अजून कोणताही संवाद नाही
                </p>
              ) : (
                conversations.map(conv => (
                  <button
                    key={conv.id}
                    onClick={() => loadConversation(conv.id)}
                    className={`w-full text-left p-3 rounded-lg text-sm transition-all ${
                      conversationId === conv.id
                        ? 'bg-brand-500/10 text-brand-300'
                        : 'text-white/60 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <div className="font-marathi truncate">{conv.title}</div>
                    {conv.created_at && (
                      <div className="text-[10px] text-white/30 mt-1">
                        {new Date(conv.created_at).toLocaleDateString('mr-IN')}
                      </div>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        )}

        {/* Chat messages */}
        <div className="flex-1 flex flex-col">
          <div
            ref={chatContainerRef}
            className="flex-1 overflow-y-auto px-6 py-6"
          >
            {/* Empty state */}
            {messages.length === 0 && !streamingContent && (
              <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-500/20 to-purple-600/20 flex items-center justify-center mb-6">
                  <Sparkles size={36} className="text-brand-400" />
                </div>
                <h2 className="text-xl font-bold font-marathi mb-2">नमस्कार! मी AI गुरू 🙏</h2>
                <p className="text-white/40 text-sm font-marathi max-w-md mb-8">
                  मी तुमच्या अभ्यासात मदत करण्यासाठी येथे आहे. तुमच्या विषयाबद्दल कोणताही प्रश्न विचारा!
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
                  {[
                    'प्रकाश संश्लेषण म्हणजे काय?',
                    'गणिताचे त्रिकोणमिती समजावून सांगा',
                    'भारताचा इतिहास - मुघल साम्राज्य',
                    'इंग्रजी grammar — tenses',
                  ].map(suggestion => (
                    <button
                      key={suggestion}
                      onClick={() => handleSend(suggestion)}
                      className="glass-card px-4 py-3 text-left text-xs text-white/50 font-marathi
                                 hover:bg-white/5 hover:text-white/70 transition-all"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Messages */}
            {messages.map(msg => (
              <ChatBubble
                key={msg.id}
                content={msg.content}
                role={msg.role}
                timestamp={msg.timestamp}
                cacheSource={msg.cacheSource}
              />
            ))}

            {/* Streaming content (partial AI response) */}
            {streamingContent && (
              <ChatBubble
                content={streamingContent}
                role="assistant"
                timestamp={new Date().toISOString()}
              />
            )}

            {/* Typing indicator */}
            {isTyping && !streamingContent && <TypingIndicator />}

            <div ref={messagesEndRef} />
          </div>

          {/* Safety alert */}
          {safetyAlert && (
            <div className="mx-6 mb-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 animate-fade-in">
              <div className="flex items-start gap-3">
                <AlertTriangle size={18} className="text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-amber-300 font-marathi">{safetyAlert}</p>
                  <button
                    onClick={() => setSafetyAlert(null)}
                    className="text-xs text-amber-400/60 hover:text-amber-400 mt-2 transition-colors"
                  >
                    बंद करा
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Input area */}
          <div className="px-6 pb-4 pt-2">
            <ChatInput
              onSend={handleSend}
              disabled={!isConnected || isTyping}
            />

            {/* Safety notice */}
            <p className="text-[10px] text-white/20 text-center mt-2 font-marathi">
              🔒 तुमचे संवाद तुमच्या शिक्षक आणि पालकांना दिसतात — ही सुरक्षिततेसाठीची सुविधा आहे
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
