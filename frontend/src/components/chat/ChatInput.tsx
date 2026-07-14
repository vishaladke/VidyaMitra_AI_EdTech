/**
 * ChatInput — message input bar for AI Guru chat.
 * Send button with character count and Marathi placeholder text.
 */
import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  maxLength?: number;
}

const MAX_CHARS = 2000;

export function ChatInput({ onSend, disabled = false, maxLength = MAX_CHARS }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [message]);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const charsRemaining = maxLength - message.length;
  const isOverLimit = charsRemaining < 0;

  return (
    <div className="glass-card p-3">
      <div className="flex items-end gap-3">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="AI गुरूला प्रश्न विचारा..."
          disabled={disabled}
          rows={1}
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white 
                     placeholder-white/30 font-marathi text-sm resize-none
                     focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50
                     transition-all duration-200 disabled:opacity-50"
          id="ai-guru-chat-input"
        />
        
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim() || isOverLimit}
          className="flex-shrink-0 w-11 h-11 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 
                     flex items-center justify-center text-white
                     hover:from-brand-600 hover:to-brand-700 hover:shadow-lg hover:shadow-brand-500/25
                     active:scale-95 transition-all duration-200
                     disabled:opacity-30 disabled:cursor-not-allowed"
          id="ai-guru-send-button"
        >
          <Send size={18} />
        </button>
      </div>

      {/* Character count */}
      {message.length > maxLength * 0.8 && (
        <div className={`text-[10px] mt-1.5 ml-1 ${isOverLimit ? 'text-red-400' : 'text-white/30'}`}>
          {charsRemaining} अक्षरे शिल्लक
        </div>
      )}
    </div>
  );
}
