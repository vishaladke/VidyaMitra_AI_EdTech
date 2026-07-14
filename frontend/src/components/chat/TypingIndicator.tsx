/**
 * TypingIndicator — animated dots shown while AI Guru is thinking.
 */
export function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4 animate-fade-in">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center mr-3">
        <span className="text-xs">✨</span>
      </div>

      <div className="glass-card px-5 py-4 rounded-2xl rounded-bl-md">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
        <p className="text-[10px] text-white/30 mt-1.5 font-marathi">AI गुरू विचार करत आहे...</p>
      </div>
    </div>
  );
}
