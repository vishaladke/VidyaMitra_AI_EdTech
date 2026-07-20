/**
 * MasterDataPage — Subjects, boards, grades management with CRUD.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Settings, ArrowLeft, BookOpen, GraduationCap, Layers, Plus,
  RefreshCw, Hash, ChevronDown,
} from 'lucide-react';
import apiClient from '../../api/client';

interface GradeInfo {
  grade: number;
  subject_count: number;
}

interface BoardInfo {
  board: string;
  subject_count: number;
}

interface MasterData {
  grades: GradeInfo[];
  boards: BoardInfo[];
  total_subjects: number;
  total_units: number;
}

interface SubjectItem {
  id: string;
  name: string;
  code: string;
  board: string;
  grade: number;
  medium: string;
}

export function MasterDataPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<MasterData | null>(null);
  const [subjects, setSubjects] = useState<SubjectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [expandedGrade, setExpandedGrade] = useState<number | null>(null);

  useEffect(() => { loadAll(); }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [masterResp, subjectResp] = await Promise.all([
        apiClient.get('/super-admin/master-data'),
        apiClient.get('/admin/subjects'),
      ]);
      setData(masterResp.data);
      setSubjects(subjectResp.data?.subjects || []);
    } catch { /* error */ } finally { setLoading(false); }
  }

  async function createSubject(form: { name: string; code: string; board: string; grade: number; medium: string }) {
    try {
      await apiClient.post('/admin/subjects', form);
      setShowCreateForm(false);
      loadAll();
    } catch { /* error */ }
  }

  const subjectsByGrade = subjects.reduce<Record<number, SubjectItem[]>>((acc, s) => {
    (acc[s.grade] ||= []).push(s);
    return acc;
  }, {});

  return (
    <div className="p-8 animate-fade-in" id="master-data">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => navigate('/super-admin')}
          className="p-2 rounded-lg hover:bg-white/5 text-white/40 hover:text-white transition-all">
          <ArrowLeft size={20} />
        </button>
        <Settings size={28} className="text-blue-400" />
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Master Data</h1>
          <p className="text-white/40 text-sm">Subjects, boards, and grade management</p>
        </div>
        <button onClick={loadAll}
          className="p-2 rounded-lg hover:bg-white/5 text-white/30 hover:text-white transition-all">
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => <div key={i} className="glass-card p-6 animate-pulse"><div className="h-8 bg-white/5 rounded w-1/3" /></div>)}
        </div>
      ) : data ? (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <SummaryCard icon={<BookOpen size={18} />} label="Total Subjects"
              value={String(data.total_subjects)}
              gradient="from-blue-500/20 to-cyan-500/10" />
            <SummaryCard icon={<Layers size={18} />} label="Syllabus Units"
              value={data.total_units.toLocaleString()}
              gradient="from-purple-500/20 to-brand-500/10" />
            <SummaryCard icon={<GraduationCap size={18} />} label="Grades"
              value={String(data.grades.length)}
              gradient="from-green-500/20 to-emerald-500/10" />
            <SummaryCard icon={<Hash size={18} />} label="Boards"
              value={String(data.boards.length)}
              gradient="from-orange-500/20 to-red-500/10" />
          </div>

          {/* Boards overview */}
          <div className="glass-card p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Hash size={18} className="text-orange-400" /> Education Boards
            </h2>
            <div className="flex flex-wrap gap-3">
              {data.boards.map(b => (
                <div key={b.board} className="glass-card p-3 bg-white/[0.02] flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-400 text-xs font-bold">
                    {b.board.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="text-sm font-medium">{b.board}</div>
                    <div className="text-[10px] text-white/30">{b.subject_count} subjects</div>
                  </div>
                </div>
              ))}
              {data.boards.length === 0 && (
                <p className="text-white/20 text-sm">No boards configured</p>
              )}
            </div>
          </div>

          {/* Subjects by grade */}
          <div className="glass-card p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <BookOpen size={18} className="text-blue-400" /> Subjects by Grade
              </h2>
              <button onClick={() => setShowCreateForm(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500/20 text-brand-300 text-sm hover:bg-brand-500/30 transition-all">
                <Plus size={14} /> Add Subject
              </button>
            </div>

            <div className="space-y-2">
              {data.grades.map(g => (
                <div key={g.grade}>
                  <button
                    onClick={() => setExpandedGrade(expandedGrade === g.grade ? null : g.grade)}
                    className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-white/[0.03] transition-all">
                    <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 text-sm font-bold">
                      {g.grade}
                    </div>
                    <div className="flex-1 text-left">
                      <span className="text-sm font-medium">Grade {g.grade}</span>
                      <span className="text-xs text-white/30 ml-2">{g.subject_count} subjects</span>
                    </div>
                    <ChevronDown size={16} className={`text-white/20 transition-transform ${
                      expandedGrade === g.grade ? 'rotate-180' : ''
                    }`} />
                  </button>

                  {/* Expanded subjects */}
                  {expandedGrade === g.grade && subjectsByGrade[g.grade] && (
                    <div className="ml-11 space-y-1 mb-2 animate-fade-in">
                      {subjectsByGrade[g.grade].map(s => (
                        <div key={s.id} className="flex items-center gap-3 p-2 rounded-lg bg-white/[0.02]">
                          <div className="w-6 h-6 rounded bg-purple-500/20 flex items-center justify-center text-[10px] text-purple-400 font-bold">
                            {s.code.slice(0, 2)}
                          </div>
                          <div className="flex-1">
                            <div className="text-sm">{s.name}</div>
                            <div className="text-[10px] text-white/20">{s.code} · {s.board} · {s.medium}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {data.grades.length === 0 && (
                <p className="text-white/20 text-sm text-center py-4">No grades configured</p>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="glass-card p-8 text-center text-white/30">
          <Settings size={48} className="mx-auto mb-4 opacity-20" />
          <p>Unable to load master data</p>
        </div>
      )}

      {/* Create subject modal */}
      {showCreateForm && (
        <CreateSubjectModal onClose={() => setShowCreateForm(false)} onSave={createSubject} />
      )}
    </div>
  );
}

function SummaryCard({ icon, label, value, gradient }: {
  icon: React.ReactNode; label: string; value: string; gradient: string;
}) {
  return (
    <div className={`glass-card p-5 bg-gradient-to-br ${gradient}`}>
      <div className="flex items-center gap-2 mb-2 text-white/40">{icon}<span className="text-xs">{label}</span></div>
      <div className="text-xl font-bold">{value}</div>
    </div>
  );
}

function CreateSubjectModal({ onClose, onSave }: {
  onClose: () => void;
  onSave: (form: { name: string; code: string; board: string; grade: number; medium: string }) => void;
}) {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [board, setBoard] = useState('Maharashtra State Board');
  const [grade, setGrade] = useState(5);
  const [medium, setMedium] = useState('marathi');

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}>
      <div className="glass-card p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-5">
          <h3 className="font-semibold text-lg">Add New Subject</h3>
          <button onClick={onClose} className="text-white/30 hover:text-white p-1"><Settings size={18} /></button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-xs text-white/30 block mb-1">Subject Name</label>
            <input value={name} onChange={e => setName(e.target.value)}
              placeholder="e.g., गणित (Mathematics)"
              className="input-field w-full text-sm" />
          </div>
          <div>
            <label className="text-xs text-white/30 block mb-1">Subject Code</label>
            <input value={code} onChange={e => setCode(e.target.value)}
              placeholder="e.g., MATH"
              className="input-field w-full text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/30 block mb-1">Grade</label>
              <select value={grade} onChange={e => setGrade(Number(e.target.value))}
                className="input-field w-full text-sm">
                {[5,6,7,8,9,10].map(g => (
                  <option key={g} value={g}>Grade {g}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-white/30 block mb-1">Medium</label>
              <select value={medium} onChange={e => setMedium(e.target.value)}
                className="input-field w-full text-sm">
                <option value="marathi">Marathi</option>
                <option value="english">English</option>
                <option value="hindi">Hindi</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-white/30 block mb-1">Board</label>
            <input value={board} onChange={e => setBoard(e.target.value)}
              className="input-field w-full text-sm" />
          </div>
          <button onClick={() => { if (name && code) onSave({ name, code, board, grade, medium }); }}
            disabled={!name || !code}
            className="btn-primary w-full text-sm disabled:opacity-40 disabled:cursor-not-allowed">
            Create Subject
          </button>
        </div>
      </div>
    </div>
  );
}
