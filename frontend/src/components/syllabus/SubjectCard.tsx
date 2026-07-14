/**
 * SubjectCard — subject card for the syllabus browser.
 * Shows subject icon/emoji, Marathi name, progress ring, and English name.
 */

interface SubjectCardProps {
  id: string;
  name: string;
  nameEn?: string;
  grade: number;
  iconUrl?: string;
  progressPct?: number;
  onClick: (id: string) => void;
}

// Subject emoji map (fallback when icon_url is not set)
const SUBJECT_EMOJIS: Record<string, string> = {
  'गणित': '🔢',
  'विज्ञान': '🔬',
  'मराठी': '📖',
  'हिंदी': '📝',
  'English': '🇬🇧',
  'सामाजिक शास्त्र': '🌍',
  'इतिहास': '🏛️',
  'भूगोल': '🗺️',
};

export function SubjectCard({ id, name, nameEn, grade, iconUrl, progressPct = 0, onClick }: SubjectCardProps) {
  const emoji = SUBJECT_EMOJIS[name] || '📚';
  const circumference = 2 * Math.PI * 18; // radius 18
  const strokeDashoffset = circumference - (progressPct / 100) * circumference;

  return (
    <button
      onClick={() => onClick(id)}
      className="glass-card p-5 hover:border-white/20 hover:bg-white/[0.03] 
                 transition-all duration-300 group text-left w-full"
      id={`subject-card-${id}`}
    >
      <div className="flex items-start justify-between mb-4">
        {/* Icon / Emoji */}
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-brand-500/20 to-purple-600/10 
                        flex items-center justify-center text-2xl
                        group-hover:scale-110 transition-transform duration-300">
          {iconUrl ? (
            <img src={iconUrl} alt={name} className="w-7 h-7 object-contain" />
          ) : (
            emoji
          )}
        </div>

        {/* Progress ring */}
        <div className="relative w-10 h-10">
          <svg className="w-10 h-10 -rotate-90" viewBox="0 0 40 40">
            <circle cx="20" cy="20" r="18" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
            <circle
              cx="20" cy="20" r="18" fill="none"
              stroke="url(#progressGradient)"
              strokeWidth="3"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-700 ease-out"
            />
            <defs>
              <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="rgb(99, 102, 241)" />
                <stop offset="100%" stopColor="rgb(168, 85, 247)" />
              </linearGradient>
            </defs>
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-white/60">
            {progressPct}%
          </span>
        </div>
      </div>

      {/* Subject name */}
      <h3 className="font-semibold font-marathi text-base mb-0.5 group-hover:text-white transition-colors">
        {name}
      </h3>
      {nameEn && (
        <p className="text-xs text-white/30">{nameEn}</p>
      )}
      <p className="text-[10px] text-white/20 mt-2">इयत्ता {grade}</p>
    </button>
  );
}
