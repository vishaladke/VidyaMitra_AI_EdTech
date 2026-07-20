/**
 * ChatAuditPage — Full AI conversation audit log with search, filters,
 * and drill-down into individual conversations.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MessageCircle, ArrowLeft, Search, AlertTriangle, ChevronRight,
  X, RefreshCw, User, Clock, Bot, Shield,
} from 'lucide-react';
import apiClient from '../../api/client';

interface Conversation {
  id: string;
  student_id: string;
  student_name: string;
  title: string;
  is_flagged: boolean;
  flag_reason: string | null;
  created_at: string | null;
}

interface Message {
  id: string;
  role: string;
  content: string;
  topic_tag: string | null;
  cache_source: string | null;
  created_at: string | null;
}

export function ChatAuditPage() {
  const navigate = useNavigate();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const limit = 30;

  // Drill-down state
  const [selectedConv, setSelectedConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  useEffect(() => { loadConversations(); }, [flaggedOnly, offset]);

  async function loadConversations(q?: string) {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (q || search) params.set('search', q || search);
      if (flaggedOnly) params.set('flagged_only', 'true');
      params.set('limit', String(limit));
      params.set('offset', String(offset));
      const { data } = await apiClient.get(`/super-admin/chat-audit?${params}`);
      setConversations(data.conversations || []);
      setTotal(data.total || 0);
    } catch { setConversations([]); } finally { setLoading(false); }
  }

  async function openConversation(conv: Conversation) {
    setSelectedConv(conv);
    setLoadingMessages(true);
    try {
      const { data } = await apiClient.get(`/super-admin/chat-audit/${conv.id}`);
      setMessages(data.messages || []);
    } catch { setMessages([]); } finally { setLoadingMessages(false); }
  }

  function formatDate(iso: string | null) {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
      + ' ' + d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  }

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <div className="p-8 animate-fade-in" id="chat-audit">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => navigate('/super-admin')}
          className="p-2 rounded-lg hover:bg-white/5 text-white/40 hover:text-white transition-all">
          <ArrowLeft size={20} />
        </button>
        <MessageCircle size={28} className="text-red-400" />
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Chat Audit Log</h1>
          <p className="text-white/40 text-sm">Full AI conversation audit access ({total} conversations)</p>
        </div>
        <button onClick={() => loadConversations()}
          className="p-2 rounded-lg hover:bg-white/5 text-white/30 hover:text-white transition-all">
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Search & filters */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') { setOffset(0); loadConversations(search); } }}
            placeholder="Search conversations or student name..."
            className="input-field pl-10 w-full text-sm" />
        </div>
        <button onClick={() => { setFlaggedOnly(!flaggedOnly); setOffset(0); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all border ${
            flaggedOnly
              ? 'bg-red-500/20 text-red-300 border-red-500/30'
              : 'text-white/40 hover:bg-white/5 border-transparent'
          }`}>
          <AlertTriangle size={14} />
          Flagged Only
        </button>
      </div>

      {/* Conversation list */}
      {loading ? (
        <div className="space-y-2">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="glass-card p-4 animate-pulse">
              <div className="h-5 bg-white/5 rounded w-2/3 mb-2" />
              <div className="h-3 bg-white/5 rounded w-1/3" />
            </div>
          ))}
        </div>
      ) : conversations.length > 0 ? (
        <>
          <div className="space-y-2 mb-6">
            {conversations.map(conv => (
              <button key={conv.id} onClick={() => openConversation(conv)}
                className={`glass-card p-4 w-full text-left hover:border-white/20 transition-all group ${
                  conv.is_flagged ? 'border-l-2 border-l-red-500/50' : ''
                }`}>
                <div className="flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {conv.is_flagged && <AlertTriangle size={14} className="text-red-400 shrink-0" />}
                      <span className="font-medium text-sm truncate">{conv.title}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-white/30">
                      <span className="flex items-center gap-1"><User size={11} />{conv.student_name}</span>
                      <span className="flex items-center gap-1"><Clock size={11} />{formatDate(conv.created_at)}</span>
                    </div>
                    {conv.is_flagged && conv.flag_reason && (
                      <div className="mt-1 text-[11px] text-red-400/70">⚠ {conv.flag_reason}</div>
                    )}
                  </div>
                  <ChevronRight size={16} className="text-white/10 group-hover:text-white/40 transition-colors shrink-0" />
                </div>
              </button>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3">
              <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}
                className="px-3 py-1.5 rounded-lg text-sm text-white/40 hover:bg-white/5 disabled:opacity-20 disabled:cursor-not-allowed">
                ← Previous
              </button>
              <span className="text-xs text-white/20">Page {currentPage} of {totalPages}</span>
              <button disabled={currentPage >= totalPages} onClick={() => setOffset(offset + limit)}
                className="px-3 py-1.5 rounded-lg text-sm text-white/40 hover:bg-white/5 disabled:opacity-20 disabled:cursor-not-allowed">
                Next →
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="glass-card p-8 text-center text-white/30">
          <MessageCircle size={48} className="mx-auto mb-4 opacity-20" />
          <p>{search || flaggedOnly ? 'No conversations match your filters' : 'No conversations yet'}</p>
        </div>
      )}

      {/* Message detail modal */}
      {selectedConv && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedConv(null)}>
          <div className="glass-card w-full max-w-2xl max-h-[80vh] flex flex-col overflow-hidden"
            onClick={e => e.stopPropagation()}>
            {/* Modal header */}
            <div className="p-4 border-b border-white/5 flex items-center gap-3 shrink-0">
              <MessageCircle size={18} className={selectedConv.is_flagged ? 'text-red-400' : 'text-brand-400'} />
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-sm truncate">{selectedConv.title}</h3>
                <div className="text-xs text-white/30 flex items-center gap-2">
                  <span>{selectedConv.student_name}</span>
                  <span>•</span>
                  <span>{formatDate(selectedConv.created_at)}</span>
                </div>
              </div>
              <button onClick={() => setSelectedConv(null)}
                className="p-1.5 rounded-lg hover:bg-white/5 text-white/30 hover:text-white transition-all">
                <X size={18} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {loadingMessages ? (
                <div className="space-y-3">
                  {[1,2,3].map(i => (
                    <div key={i} className="animate-pulse">
                      <div className="h-12 bg-white/5 rounded-lg" />
                    </div>
                  ))}
                </div>
              ) : messages.length > 0 ? (
                messages.map(m => (
                  <div key={m.id} className={`flex gap-3 ${m.role === 'assistant' ? '' : 'flex-row-reverse'}`}>
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                      m.role === 'assistant'
                        ? 'bg-brand-500/20 text-brand-400'
                        : 'bg-blue-500/20 text-blue-400'
                    }`}>
                      {m.role === 'assistant' ? <Bot size={14} /> : <User size={14} />}
                    </div>
                    <div className={`max-w-[80%] ${
                      m.role === 'assistant'
                        ? 'glass-card p-3 bg-white/[0.02]'
                        : 'glass-card p-3 bg-brand-500/[0.08]'
                    }`}>
                      <p className="text-sm text-white/80 whitespace-pre-wrap">{m.content}</p>
                      <div className="flex items-center gap-2 mt-2 text-[9px] text-white/20">
                        {m.topic_tag && <span className="px-1.5 py-0.5 rounded bg-white/5">{m.topic_tag}</span>}
                        {m.cache_source && (
                          <span className={`px-1.5 py-0.5 rounded ${
                            m.cache_source === 'live_llm' ? 'bg-orange-500/10 text-orange-300/50' : 'bg-green-500/10 text-green-300/50'
                          }`}>{m.cache_source}</span>
                        )}
                        <span>{formatDate(m.created_at)}</span>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-white/20 text-sm py-8">No messages in this conversation</p>
              )}
            </div>

            {/* Footer */}
            {selectedConv.is_flagged && (
              <div className="p-3 border-t border-white/5 bg-red-500/[0.05] shrink-0">
                <div className="flex items-center gap-2 text-xs text-red-400">
                  <Shield size={14} />
                  <span className="font-medium">Flagged conversation</span>
                  {selectedConv.flag_reason && (
                    <span className="text-red-400/60">— {selectedConv.flag_reason}</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
