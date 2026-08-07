/**
 * TestsPage — List tests, take tests with question navigator, view results.
 *
 * Features:
 * - Tab filter: Available / Completed
 * - Full-screen test-taking UI with question navigator
 * - Question display with MCQ/True-False selection
 * - Confirmation dialog before submission
 * - Results view with score + correct answers + explanations
 */
import { useState, useEffect } from 'react';
import {
  ArrowLeft, FileText, CheckCircle2, Clock, BookOpen,
  ChevronRight, ChevronLeft, Award, AlertTriangle, X,
} from 'lucide-react';
import apiClient from '../../api/client';

interface TestItem {
  id: string;
  title: string;
  description?: string;
  subject_name: string;
  subject_name_en?: string;
  question_count: number;
  max_score?: number;
  due_date?: string;
  is_attempted: boolean;
  score?: number;
  percentage?: number;
  attempted_at?: string;
}

interface QuestionItem {
  id: string;
  question_text: string;
  question_type: string;
  options?: Record<string, string>;
  marks: number;
  difficulty?: string;
  display_order: number;
  correct_answer?: string;
  explanation?: string;
  student_answer?: string;
  is_correct?: boolean;
}

interface TestForTaking {
  id: string;
  title: string;
  description?: string;
  subject_name: string;
  max_score?: number;
  questions: QuestionItem[];
}

interface TestResult {
  attempt_id: string;
  test_title: string;
  subject_name: string;
  score: number;
  max_score: number;
  percentage: number;
  is_graded: boolean;
  submitted_at?: string;
  questions: QuestionItem[];
}

type Tab = 'available' | 'completed';
type View = 'list' | 'taking' | 'result';

export function TestsPage() {
  const [tab, setTab] = useState<Tab>('available');
  const [tests, setTests] = useState<TestItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<View>('list');
  const [testData, setTestData] = useState<TestForTaking | null>(null);
  const [resultData, setResultData] = useState<TestResult | null>(null);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => { loadTests(); }, [tab]);

  async function loadTests() {
    try {
      setLoading(true);
      const { data } = await apiClient.get(`/students/tests?status=${tab}`);
      setTests(data.tests || []);
    } catch {
      setTests([]);
    } finally {
      setLoading(false);
    }
  }

  async function startTest(testId: string) {
    try {
      const { data } = await apiClient.get(`/students/tests/${testId}`);
      setTestData(data);
      setAnswers({});
      setCurrentQ(0);
      setView('taking');
    } catch {
      // handle error
    }
  }

  async function viewResult(testId: string) {
    try {
      const { data } = await apiClient.get(`/students/tests/${testId}/result`);
      setResultData(data);
      setView('result');
    } catch {
      // handle error
    }
  }

  async function handleSubmit() {
    if (!testData) return;
    try {
      setSubmitting(true);
      setShowConfirm(false);
      const { data } = await apiClient.post(`/students/tests/${testData.id}/submit`, { answers });
      // Show result immediately
      setResultData({
        attempt_id: data.attempt_id,
        test_title: testData.title,
        subject_name: testData.subject_name,
        score: data.score,
        max_score: data.max_score,
        percentage: data.percentage,
        is_graded: data.is_graded,
        submitted_at: new Date().toISOString(),
        questions: data.results || [],
      });
      setView('result');
      loadTests();
    } catch {
      // error
    } finally {
      setSubmitting(false);
    }
  }

  function backToList() {
    setView('list');
    setTestData(null);
    setResultData(null);
    setAnswers({});
    setCurrentQ(0);
  }

  // ── Result View ──────────────────────────────────────────
  if (view === 'result' && resultData) {
    const correct = resultData.questions.filter(q => q.is_correct === true).length;
    const wrong = resultData.questions.filter(q => q.is_correct === false).length;
    const pending = resultData.questions.filter(q => q.is_correct === null).length;

    return (
      <div className="p-8 animate-fade-in" id="test-result">
        <button onClick={backToList} className="flex items-center gap-2 text-white/50 hover:text-white mb-6 transition-colors">
          <ArrowLeft size={18} /> सर्व चाचण्या
        </button>

        {/* Score banner */}
        <div className="glass-card p-8 mb-8 text-center">
          <h2 className="text-lg font-marathi text-white/60 mb-2">{resultData.test_title}</h2>
          <div className={`text-6xl font-bold mb-3 ${
            resultData.percentage >= 70 ? 'text-emerald-400' :
            resultData.percentage >= 40 ? 'text-amber-400' : 'text-red-400'
          }`}>
            {resultData.percentage}%
          </div>
          <p className="text-white/40 font-marathi text-lg">
            {resultData.score} / {resultData.max_score} गुण
          </p>

          {/* Stats pills */}
          <div className="flex items-center justify-center gap-3 mt-5">
            <span className="px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 text-sm flex items-center gap-1.5">
              <CheckCircle2 size={14} /> {correct} बरोबर
            </span>
            <span className="px-3 py-1.5 rounded-full bg-red-500/10 text-red-400 text-sm flex items-center gap-1.5">
              <X size={14} /> {wrong} चुकीचे
            </span>
            {pending > 0 && (
              <span className="px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-400 text-sm flex items-center gap-1.5">
                <Clock size={14} /> {pending} मूल्यांकन बाकी
              </span>
            )}
          </div>

          {resultData.percentage >= 70 && (
            <div className="mt-4 flex items-center justify-center gap-2">
              <Award size={20} className="text-amber-400" />
              <span className="text-amber-400 font-marathi">🎉 उत्कृष्ट कामगिरी!</span>
            </div>
          )}
        </div>

        {/* Question results */}
        <h3 className="text-lg font-semibold font-marathi mb-4 text-white/80">प्रश्न विश्लेषण</h3>
        <div className="space-y-4">
          {resultData.questions.map((q, i) => (
            <div key={q.id} className={`glass-card p-5 border-l-4 ${
              q.is_correct === true ? 'border-l-emerald-500' :
              q.is_correct === false ? 'border-l-red-500' : 'border-l-blue-500'
            }`}>
              <div className="flex items-start justify-between mb-3">
                <p className="text-sm font-marathi text-white/90 flex-1">
                  <span className="text-white/40 mr-2">प्र.{i + 1}</span>
                  {q.question_text}
                </p>
                <span className="text-xs text-white/30 ml-2">{q.marks} गुण</span>
              </div>

              {/* Show what student answered and correct answer */}
              {q.options && q.student_answer && (
                <div className="mb-2 text-sm font-marathi">
                  <span className="text-white/50">तुमचे उत्तर: </span>
                  <span className={q.is_correct ? 'text-emerald-400' : 'text-red-400'}>
                    {q.options[q.student_answer] || q.student_answer}
                  </span>
                </div>
              )}

              {q.is_correct === false && q.correct_answer && q.options && (
                <div className="text-sm font-marathi mb-2">
                  <span className="text-white/50">बरोबर उत्तर: </span>
                  <span className="text-emerald-400">{q.options[q.correct_answer] || q.correct_answer}</span>
                </div>
              )}

              {q.explanation && (
                <p className="text-xs text-white/40 font-marathi bg-white/[0.03] rounded-lg p-3 mt-2">
                  💡 {q.explanation}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Test-Taking View ─────────────────────────────────────
  if (view === 'taking' && testData) {
    const question = testData.questions[currentQ];
    const totalQ = testData.questions.length;
    const answeredCount = testData.questions.filter(q => answers[q.id]?.trim()).length;

    return (
      <div className="h-full flex" id="test-taking">
        {/* Question Navigator Sidebar */}
        <div className="w-20 md:w-56 border-r border-white/5 bg-surface-950/50 flex flex-col py-4 px-2 md:px-4 flex-shrink-0">
          <div className="mb-4 hidden md:block">
            <h3 className="text-sm font-semibold font-marathi text-white/70 truncate">{testData.title}</h3>
            <p className="text-[10px] text-white/30 mt-1">{answeredCount}/{totalQ} उत्तरे</p>
          </div>

          <div className="flex-1 overflow-y-auto">
            <div className="grid grid-cols-4 md:grid-cols-5 gap-1.5">
              {testData.questions.map((q, i) => {
                const isAnswered = !!answers[q.id]?.trim();
                const isCurrent = i === currentQ;
                return (
                  <button
                    key={q.id}
                    onClick={() => setCurrentQ(i)}
                    className={`w-full aspect-square rounded-lg text-xs font-medium transition-all ${
                      isCurrent
                        ? 'bg-brand-500 text-white ring-2 ring-brand-400/50'
                        : isAnswered
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-white/[0.03] text-white/40 border border-white/5 hover:bg-white/[0.06]'
                    }`}
                  >
                    {i + 1}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Submit button in sidebar */}
          <button
            onClick={() => setShowConfirm(true)}
            disabled={submitting}
            className="mt-4 btn-primary text-sm py-2.5 w-full"
          >
            चाचणी सबमिट करा
          </button>
        </div>

        {/* Question Display */}
        <div className="flex-1 flex flex-col">
          {/* Question header */}
          <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-brand-500/10 text-brand-400 text-sm font-bold">{currentQ + 1}</span>
              <span className="text-sm text-white/40 font-marathi">/ {totalQ} प्रश्न</span>
            </div>
            <div className="flex items-center gap-2">
              {question.difficulty && (
                <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                  question.difficulty === 'easy' ? 'bg-emerald-500/10 text-emerald-400' :
                  question.difficulty === 'medium' ? 'bg-amber-500/10 text-amber-400' :
                  'bg-red-500/10 text-red-400'
                }`}>{question.difficulty === 'easy' ? 'सोपे' : question.difficulty === 'medium' ? 'मध्यम' : 'कठीण'}</span>
              )}
              <span className="text-xs text-white/30">{question.marks} गुण</span>
            </div>
          </div>

          {/* Question body */}
          <div className="flex-1 overflow-y-auto px-6 py-8">
            <p className="text-lg font-marathi text-white/90 mb-8 leading-relaxed">{question.question_text}</p>

            {/* MCQ / True-False options */}
            {(question.question_type === 'mcq' || question.question_type === 'true_false') && question.options && (
              <div className="space-y-3 max-w-2xl">
                {Object.entries(question.options).map(([key, value]) => (
                  <button
                    key={key}
                    onClick={() => setAnswers(prev => ({ ...prev, [question.id]: key }))}
                    className={`w-full text-left px-5 py-4 rounded-xl text-sm font-marathi transition-all duration-200 flex items-center gap-4 ${
                      answers[question.id] === key
                        ? 'bg-brand-500/20 border-2 border-brand-500/50 text-white shadow-lg shadow-brand-500/5'
                        : 'bg-white/[0.03] border-2 border-transparent text-white/60 hover:bg-white/[0.06] hover:text-white'
                    }`}
                  >
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold uppercase transition-colors ${
                      answers[question.id] === key
                        ? 'bg-brand-500 text-white'
                        : 'bg-white/5 text-white/40'
                    }`}>{key}</span>
                    {value}
                  </button>
                ))}
              </div>
            )}

            {/* Text answer */}
            {(question.question_type === 'short_answer' || question.question_type === 'long_answer') && (
              <textarea
                value={answers[question.id] || ''}
                onChange={(e) => setAnswers(prev => ({ ...prev, [question.id]: e.target.value }))}
                placeholder="तुमचे उत्तर येथे लिहा..."
                rows={question.question_type === 'long_answer' ? 6 : 3}
                className="w-full max-w-2xl bg-white/[0.03] border border-white/10 rounded-xl px-5 py-4 text-white text-sm font-marathi placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-brand-500/40 resize-none"
              />
            )}
          </div>

          {/* Navigation footer */}
          <div className="px-6 py-4 border-t border-white/5 flex items-center justify-between">
            <button
              onClick={() => setCurrentQ(Math.max(0, currentQ - 1))}
              disabled={currentQ === 0}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-white/50 hover:text-white hover:bg-white/5 transition-all disabled:opacity-30"
            >
              <ChevronLeft size={16} /> मागे
            </button>

            <span className="text-xs text-white/30">
              {answeredCount} / {totalQ} उत्तरे दिली
            </span>

            <button
              onClick={() => setCurrentQ(Math.min(totalQ - 1, currentQ + 1))}
              disabled={currentQ === totalQ - 1}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-white/50 hover:text-white hover:bg-white/5 transition-all disabled:opacity-30"
            >
              पुढे <ChevronRight size={16} />
            </button>
          </div>
        </div>

        {/* Confirmation Dialog */}
        {showConfirm && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center animate-fade-in">
            <div className="glass-card p-8 max-w-md mx-4 text-center">
              <AlertTriangle size={40} className="text-amber-400 mx-auto mb-4" />
              <h3 className="text-lg font-bold font-marathi mb-2">चाचणी सबमिट करायची?</h3>
              <p className="text-sm text-white/50 font-marathi mb-2">
                तुम्ही {answeredCount} / {totalQ} प्रश्नांची उत्तरे दिली आहेत.
              </p>
              {answeredCount < totalQ && (
                <p className="text-xs text-amber-400/80 font-marathi mb-4">
                  ⚠️ {totalQ - answeredCount} प्रश्नांची उत्तरे अजून दिली नाहीत!
                </p>
              )}
              <div className="flex gap-3 justify-center mt-6">
                <button
                  onClick={() => setShowConfirm(false)}
                  className="btn-secondary px-6 py-2"
                >
                  रद्द करा
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="btn-primary px-6 py-2"
                >
                  {submitting ? 'सबमिट होत आहे...' : 'हो, सबमिट करा'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── List View ────────────────────────────────────────────
  const tabs: { key: Tab; label: string }[] = [
    { key: 'available', label: 'उपलब्ध' },
    { key: 'completed', label: 'पूर्ण' },
  ];

  return (
    <div className="p-8 animate-fade-in" id="tests-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold font-marathi flex items-center gap-3">
          <FileText size={24} className="text-amber-400" />
          चाचण्या
        </h1>
        <p className="text-white/40 mt-1 font-marathi text-sm">ऑटो-ग्रेडिंगसह चाचण्या</p>
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

      {/* Tests list */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2].map(i => (
            <div key={i} className="glass-card p-5 animate-pulse">
              <div className="h-5 bg-white/5 rounded w-3/4 mb-3" />
              <div className="h-3 bg-white/5 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : tests.length === 0 ? (
        <div className="text-center py-16">
          <FileText size={48} className="text-white/10 mx-auto mb-4" />
          <p className="text-white/30 font-marathi">
            {tab === 'available' ? 'सध्या कोणतीही चाचणी उपलब्ध नाही' : 'अजून कोणतीही चाचणी पूर्ण केली नाही'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {tests.map(t => (
            <button
              key={t.id}
              onClick={() => t.is_attempted ? viewResult(t.id) : startTest(t.id)}
              className="glass-card p-5 w-full text-left hover:border-white/15 transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold font-marathi text-white/90 group-hover:text-white transition-colors">{t.title}</h3>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">{t.subject_name}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-white/40">
                    <span className="flex items-center gap-1">
                      <BookOpen size={12} />
                      {t.question_count} प्रश्न
                    </span>
                    {t.max_score && (
                      <span>{t.max_score} गुण</span>
                    )}
                    {t.due_date && (
                      <span className="flex items-center gap-1">
                        <Clock size={12} />
                        {new Date(t.due_date).toLocaleDateString('mr-IN')}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {t.is_attempted ? (
                    <div className="text-right">
                      <div className={`text-lg font-bold ${
                        (t.percentage || 0) >= 70 ? 'text-emerald-400' :
                        (t.percentage || 0) >= 40 ? 'text-amber-400' : 'text-red-400'
                      }`}>
                        {t.percentage}%
                      </div>
                      <span className="text-[10px] text-white/30">निकाल पहा →</span>
                    </div>
                  ) : (
                    <span className="px-3 py-1.5 rounded-xl bg-brand-500/10 text-brand-400 text-xs font-medium group-hover:bg-brand-500/20 transition-all">
                      चाचणी सुरू करा →
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
