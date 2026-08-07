/**
 * AssignmentsPage — List, view, and submit homework/practice assignments.
 *
 * Features:
 * - Tab filter: All / Pending / Completed
 * - Assignment cards with subject badge, due date, score
 * - Click → Question view with MCQ/True-False selection
 * - Submit → Auto-graded results with explanations
 */
import { useState, useEffect } from 'react';
import { ArrowLeft, ClipboardList, CheckCircle2, Clock, BookOpen, ChevronRight, Award, AlertCircle } from 'lucide-react';
import apiClient from '../../api/client';

interface AssignmentItem {
  id: string;
  title: string;
  description?: string;
  assignment_type: string;
  subject_name: string;
  subject_name_en?: string;
  due_date?: string;
  max_score?: number;
  question_count: number;
  is_submitted: boolean;
  score?: number;
  percentage?: number;
  submitted_at?: string;
}

interface QuestionItem {
  id: string;
  question_text: string;
  question_type: string;
  options?: Record<string, string>;
  marks: number;
  difficulty?: string;
  display_order: number;
  // For results
  correct_answer?: string;
  explanation?: string;
  student_answer?: string;
  is_correct?: boolean;
}

interface AssignmentDetail {
  id: string;
  title: string;
  description?: string;
  assignment_type: string;
  subject_name: string;
  subject_name_en?: string;
  due_date?: string;
  max_score?: number;
  questions: QuestionItem[];
  previous_attempt?: {
    score: number;
    max_score: number;
    percentage: number;
    answers: Record<string, string>;
    submitted_at: string;
  };
}

interface SubmitResult {
  success: boolean;
  score: number;
  max_score: number;
  percentage: number;
  is_graded: boolean;
  results: QuestionItem[];
}

type Tab = 'all' | 'pending' | 'completed';

export function AssignmentsPage() {
  const [tab, setTab] = useState<Tab>('all');
  const [assignments, setAssignments] = useState<AssignmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<AssignmentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmitResult | null>(null);

  useEffect(() => { loadAssignments(); }, [tab]);

  async function loadAssignments() {
    try {
      setLoading(true);
      const params = tab !== 'all' ? `?status=${tab}` : '';
      const { data } = await apiClient.get(`/students/assignments${params}`);
      setAssignments(data.assignments || []);
    } catch {
      setAssignments([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadDetail(id: string) {
    try {
      setDetailLoading(true);
      setSelectedId(id);
      setResult(null);
      setAnswers({});
      const { data } = await apiClient.get(`/students/assignments/${id}`);
      setDetail(data);
      // Pre-fill answers if previous attempt exists
      if (data.previous_attempt?.answers) {
        setAnswers(data.previous_attempt.answers);
      }
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleSubmit() {
    if (!selectedId || !detail) return;
    try {
      setSubmitting(true);
      const { data } = await apiClient.post(`/students/assignments/${selectedId}/submit`, { answers });
      setResult(data);
      loadAssignments(); // refresh list
    } catch {
      // error
    } finally {
      setSubmitting(false);
    }
  }

  function handleBack() {
    setSelectedId(null);
    setDetail(null);
    setResult(null);
    setAnswers({});
  }

  // ── Results View ─────────────────────────────────────────
  if (result) {
    return (
      <div className="p-8 animate-fade-in" id="assignment-results">
        <button onClick={handleBack} className="flex items-center gap-2 text-white/50 hover:text-white mb-6 transition-colors">
          <ArrowLeft size={18} /> सर्व असाइनमेंट
        </button>

        {/* Score card */}
        <div className="glass-card p-8 mb-6 text-center">
          <div className={`text-5xl font-bold mb-2 ${result.percentage >= 70 ? 'text-emerald-400' : result.percentage >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
            {result.percentage}%
          </div>
          <p className="text-white/50 font-marathi">
            {result.score} / {result.max_score} गुण
          </p>
          <div className="mt-4 flex items-center justify-center gap-2">
            {result.percentage >= 70 ? (
              <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-sm font-marathi">🎉 उत्कृष्ट!</span>
            ) : result.percentage >= 40 ? (
              <span className="px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 text-sm font-marathi">👍 चांगले</span>
            ) : (
              <span className="px-3 py-1 rounded-full bg-red-500/10 text-red-400 text-sm font-marathi">📖 अजून सराव करा</span>
            )}
            {!result.is_graded && (
              <span className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs">काही उत्तरांचे मूल्यांकन शिक्षकांकडून होईल</span>
            )}
          </div>
        </div>

        {/* Question-by-question results */}
        <div className="space-y-4">
          {result.results.map((q, i) => (
            <div key={q.id} className={`glass-card p-5 border-l-4 ${
              q.is_correct === true ? 'border-l-emerald-500' : q.is_correct === false ? 'border-l-red-500' : 'border-l-blue-500'
            }`}>
              <div className="flex items-start justify-between mb-3">
                <p className="text-sm font-marathi text-white/90 flex-1">
                  <span className="text-white/40 mr-2">प्र.{i + 1}</span>
                  {q.question_text}
                </p>
                <span className="text-xs text-white/30 ml-2">{q.marks} गुण</span>
              </div>

              {q.is_correct !== null && (
                <div className="flex items-center gap-4 text-sm mb-2">
                  <span className={q.is_correct ? 'text-emerald-400' : 'text-red-400'}>
                    {q.is_correct ? '✅ बरोबर' : '❌ चुकीचे'}
                  </span>
                  {!q.is_correct && q.correct_answer && q.options && (
                    <span className="text-white/50 font-marathi">
                      बरोबर उत्तर: <strong className="text-emerald-400">{q.options[q.correct_answer] || q.correct_answer}</strong>
                    </span>
                  )}
                </div>
              )}

              {q.explanation && (
                <p className="text-xs text-white/40 font-marathi mt-2 bg-white/[0.03] rounded-lg p-3">
                  💡 {q.explanation}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Detail View (Questions) ──────────────────────────────
  if (selectedId && detail) {
    const allAnswered = detail.questions.every(q => answers[q.id]?.trim());
    const hasAlreadySubmitted = !!detail.previous_attempt;

    return (
      <div className="p-8 animate-fade-in" id="assignment-detail">
        <button onClick={handleBack} className="flex items-center gap-2 text-white/50 hover:text-white mb-6 transition-colors">
          <ArrowLeft size={18} /> सर्व असाइनमेंट
        </button>

        <div className="mb-6">
          <h1 className="text-2xl font-bold font-marathi">{detail.title}</h1>
          <p className="text-white/40 text-sm mt-1 font-marathi">{detail.subject_name} • {detail.questions.length} प्रश्न</p>
          {detail.description && <p className="text-white/50 text-sm mt-2 font-marathi">{detail.description}</p>}
        </div>

        {hasAlreadySubmitted && (
          <div className="glass-card p-4 mb-6 border-l-4 border-l-emerald-500">
            <p className="text-sm text-emerald-400 font-marathi flex items-center gap-2">
              <CheckCircle2 size={16} />
              तुम्ही हे आधीच सबमिट केले आहे — {detail.previous_attempt!.percentage}% ({detail.previous_attempt!.score}/{detail.previous_attempt!.max_score} गुण)
            </p>
            <p className="text-xs text-white/30 mt-1">तुम्ही पुन्हा सबमिट करू शकता.</p>
          </div>
        )}

        {/* Questions */}
        <div className="space-y-5 mb-8">
          {detail.questions.map((q, i) => (
            <div key={q.id} className="glass-card p-5">
              <div className="flex items-start justify-between mb-4">
                <p className="text-sm font-marathi text-white/90 flex-1">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-brand-500/10 text-brand-400 text-xs mr-2">{i + 1}</span>
                  {q.question_text}
                </p>
                <div className="flex items-center gap-2 ml-2">
                  {q.difficulty && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                      q.difficulty === 'easy' ? 'bg-emerald-500/10 text-emerald-400' :
                      q.difficulty === 'medium' ? 'bg-amber-500/10 text-amber-400' :
                      'bg-red-500/10 text-red-400'
                    }`}>{q.difficulty === 'easy' ? 'सोपे' : q.difficulty === 'medium' ? 'मध्यम' : 'कठीण'}</span>
                  )}
                  <span className="text-[10px] text-white/30">{q.marks} गुण</span>
                </div>
              </div>

              {/* MCQ Options */}
              {(q.question_type === 'mcq' || q.question_type === 'true_false') && q.options && (
                <div className="grid gap-2">
                  {Object.entries(q.options).map(([key, value]) => (
                    <button
                      key={key}
                      onClick={() => setAnswers(prev => ({ ...prev, [q.id]: key }))}
                      className={`w-full text-left px-4 py-3 rounded-xl text-sm font-marathi transition-all duration-200 ${
                        answers[q.id] === key
                          ? 'bg-brand-500/20 border border-brand-500/40 text-white'
                          : 'bg-white/[0.03] border border-white/5 text-white/60 hover:bg-white/[0.06] hover:text-white'
                      }`}
                    >
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-white/5 text-white/40 text-xs mr-3 uppercase">{key}</span>
                      {value}
                    </button>
                  ))}
                </div>
              )}

              {/* Short / Long answer */}
              {(q.question_type === 'short_answer' || q.question_type === 'long_answer') && (
                <textarea
                  value={answers[q.id] || ''}
                  onChange={(e) => setAnswers(prev => ({ ...prev, [q.id]: e.target.value }))}
                  placeholder="तुमचे उत्तर येथे लिहा..."
                  rows={q.question_type === 'long_answer' ? 4 : 2}
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white text-sm font-marathi placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-brand-500/40 resize-none"
                />
              )}
            </div>
          ))}
        </div>

        {/* Submit button */}
        <div className="sticky bottom-0 bg-surface-950/80 backdrop-blur-xl py-4 border-t border-white/5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-white/40 font-marathi">
              {Object.keys(answers).filter(k => answers[k]?.trim()).length} / {detail.questions.length} प्रश्नांची उत्तरे दिली
            </p>
            <button
              onClick={handleSubmit}
              disabled={submitting || !allAnswered}
              className="btn-primary px-8 disabled:opacity-40"
            >
              {submitting ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  तपासत आहे...
                </span>
              ) : (
                'उत्तरे सबमिट करा'
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Loading detail ───────────────────────────────────────
  if (detailLoading) {
    return (
      <div className="p-8 flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
      </div>
    );
  }

  // ── List View ────────────────────────────────────────────
  const tabs: { key: Tab; label: string }[] = [
    { key: 'all', label: 'सर्व' },
    { key: 'pending', label: 'पेंडिंग' },
    { key: 'completed', label: 'पूर्ण' },
  ];

  return (
    <div className="p-8 animate-fade-in" id="assignments-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold font-marathi flex items-center gap-3">
          <ClipboardList size={24} className="text-emerald-400" />
          असाइनमेंट
        </h1>
        <p className="text-white/40 mt-1 font-marathi text-sm">गृहपाठ आणि सराव</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-xl text-sm font-marathi transition-all ${
              tab === t.key
                ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                : 'bg-white/[0.03] text-white/50 border border-white/5 hover:bg-white/[0.06]'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Assignment list */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-card p-5 animate-pulse">
              <div className="h-5 bg-white/5 rounded w-3/4 mb-3" />
              <div className="h-3 bg-white/5 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : assignments.length === 0 ? (
        <div className="text-center py-16">
          <ClipboardList size={48} className="text-white/10 mx-auto mb-4" />
          <p className="text-white/30 font-marathi">
            {tab === 'pending' ? 'कोणतेही पेंडिंग असाइनमेंट नाही 🎉' :
             tab === 'completed' ? 'अजून कोणतेही असाइनमेंट पूर्ण केले नाही' :
             'कोणतेही असाइनमेंट उपलब्ध नाही'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {assignments.map(a => (
            <button
              key={a.id}
              onClick={() => loadDetail(a.id)}
              className="glass-card p-5 w-full text-left hover:border-white/15 transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold font-marathi text-white/90 group-hover:text-white transition-colors">{a.title}</h3>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">{a.subject_name}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-white/40">
                    <span className="flex items-center gap-1">
                      <BookOpen size={12} />
                      {a.question_count} प्रश्न
                    </span>
                    {a.due_date && (
                      <span className="flex items-center gap-1">
                        <Clock size={12} />
                        {new Date(a.due_date).toLocaleDateString('mr-IN')}
                      </span>
                    )}
                    {a.assignment_type === 'homework' && <span className="text-white/20">गृहपाठ</span>}
                    {a.assignment_type === 'practice' && <span className="text-white/20">सराव</span>}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {a.is_submitted ? (
                    <div className="text-right">
                      <div className={`text-lg font-bold ${
                        (a.percentage || 0) >= 70 ? 'text-emerald-400' :
                        (a.percentage || 0) >= 40 ? 'text-amber-400' : 'text-red-400'
                      }`}>
                        {a.percentage}%
                      </div>
                      <span className="text-[10px] text-white/30 flex items-center gap-1">
                        <CheckCircle2 size={10} className="text-emerald-400" /> पूर्ण
                      </span>
                    </div>
                  ) : (
                    <span className="text-[10px] px-2 py-1 rounded-full bg-amber-500/10 text-amber-400">पेंडिंग</span>
                  )}
                  <ChevronRight size={16} className="text-white/20 group-hover:text-white/40 transition-colors" />
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
