/**
 * ChatBubble — styled message bubble for AI Guru chat.
 * Student messages align right, AI messages align left.
 * Glass-card styling with Marathi-friendly typography.
 */
import { Sparkles } from 'lucide-react';

interface ChatBubbleProps {
  content: string;
  role: 'student' | 'assistant';
  timestamp?: string;
  cacheSource?: string;
}

export function ChatBubble({ content, role, timestamp, cacheSource }: ChatBubbleProps) {
  const isStudent = role === 'student';

  return (
    <div className={`flex ${isStudent ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in`}>
      {/* AI avatar */}
      {!isStudent && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center mr-3 mt-1">
          <Sparkles size={14} className="text-white" />
        </div>
      )}

      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl ${
          isStudent
            ? 'bg-gradient-to-br from-brand-500 to-brand-600 text-white rounded-br-md'
            : 'glass-card text-white/90 rounded-bl-md'
        }`}
      >
        {/* Message content */}
        <div className="text-sm leading-relaxed font-marathi whitespace-pre-wrap">
          {content}
        </div>

        {/* Metadata row */}
        <div className={`flex items-center gap-2 mt-2 text-[10px] ${
          isStudent ? 'text-white/50 justify-end' : 'text-white/30'
        }`}>
          {timestamp && (
            <span>{new Date(timestamp).toLocaleTimeString('mr-IN', { hour: '2-digit', minute: '2-digit' })}</span>
          )}
          {cacheSource && !isStudent && (
            <span className="px-1.5 py-0.5 rounded-full bg-white/5 text-white/40">
              {cacheSource === 'exact_redis' ? '⚡ कॅश' : 
               cacheSource === 'semantic_pgvector' ? '🧠 सिमेंटिक' :
               cacheSource === 'faq_bank' ? '📚 FAQ' : '🤖 AI'}
            </span>
          )}
        </div>
      </div>

      {/* Student avatar */}
      {isStudent && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center ml-3 mt-1">
          <span className="text-xs font-bold text-white">मी</span>
        </div>
      )}
    </div>
  );
}
