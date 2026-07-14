/**
 * SyllabusCRUDPage — admin view: subjects list, create subject, create syllabus unit.
 */
import { useState, useEffect } from 'react';
import { BookOpen, Plus, ChevronDown, ChevronRight } from 'lucide-react';
import apiClient from '../../api/client';

interface SubjectItem {
  id: string; name: string; name_en: string; grade: number; board: string; is_active: boolean;
}

export function SyllabusCRUDPage() {
  const [subjects, setSubjects] = useState<SubjectItem[]>([]);
  const [gradeFilter, setGradeFilter] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => { loadSubjects(); }, [gradeFilter]);

  async function loadSubjects() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (gradeFilter) params.set('grade', String(gradeFilter));
      const { data } = await apiClient.get(`/admin/subjects?${params}`);
      setSubjects(data.subjects || []);
    } catch { setSubjects([]); } finally { setLoading(false); }
  }

  async function createSubject(name: string, nameEn: string, grade: number) {
    try {
      await apiClient.post('/admin/subjects', { name, name_en: nameEn, grade });
      setShowCreate(false);
      loadSubjects();
    } catch { /* error */ }
  }

  // Group by grade
  const grouped = subjects.reduce<Record<number, SubjectItem[]>>((acc, s) => {
    (acc[s.grade] = acc[s.grade] || []).push(s);
    return acc;
  }, {});

  return (
    <div className="p-8 animate-fade-in" id="syllabus-crud">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <BookOpen size={24} className="text-blue-400" /> Syllabus Management
          </h1>
          <p className="text-white/40 mt-1 text-sm">Subjects, chapters, and topics ({subjects.length} subjects)</p>
        </div>
        <div className="flex gap-3">
          <select value={gradeFilter || ''} onChange={e => setGradeFilter(e.target.value ? Number(e.target.value) : null)}
            className="input-field text-sm">
            <option value="">All Grades</option>
            {[5,6,7,8,9,10].map(g => <option key={g} value={g}>Grade {g}</option>)}
          </select>
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm">
            <Plus size={16} /> Add Subject
          </button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="glass-card p-4 animate-pulse"><div className="h-6 bg-white/5 rounded w-1/3" /></div>)}
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(grouped).sort(([a], [b]) => Number(a) - Number(b)).map(([grade, subs]) => (
            <GradeGroup key={grade} grade={Number(grade)} subjects={subs} />
          ))}
          {subjects.length === 0 && (
            <div className="glass-card p-12 text-center">
              <p className="text-white/30">No subjects found</p>
            </div>
          )}
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="glass-card p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h3 className="font-semibold mb-4">Create Subject</h3>
            <CreateSubjectForm onCreate={createSubject} />
          </div>
        </div>
      )}
    </div>
  );
}

function GradeGroup({ grade, subjects }: { grade: number; subjects: SubjectItem[] }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="glass-card overflow-hidden">
      <button onClick={() => setOpen(!open)}
        className="w-full p-4 flex items-center justify-between hover:bg-white/[0.02] transition-all">
        <span className="font-semibold text-sm">Grade {grade} <span className="text-white/20 ml-2">({subjects.length} subjects)</span></span>
        {open ? <ChevronDown size={16} className="text-white/30" /> : <ChevronRight size={16} className="text-white/30" />}
      </button>
      {open && (
        <div className="border-t border-white/5">
          {subjects.map(s => (
            <div key={s.id} className="p-3 px-4 flex items-center justify-between border-b border-white/[0.03] last:border-0 hover:bg-white/[0.01]">
              <div>
                <span className="text-sm font-marathi text-white/70">{s.name}</span>
                <span className="text-xs text-white/20 ml-2">({s.name_en})</span>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${s.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                {s.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CreateSubjectForm({ onCreate }: { onCreate: (name: string, nameEn: string, grade: number) => void }) {
  const [name, setName] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [grade, setGrade] = useState(7);

  return (
    <div className="space-y-3">
      <div>
        <label className="text-xs text-white/30 block mb-1">Name (Marathi)</label>
        <input value={name} onChange={e => setName(e.target.value)} className="input-field w-full text-sm" placeholder="गणित" />
      </div>
      <div>
        <label className="text-xs text-white/30 block mb-1">Name (English)</label>
        <input value={nameEn} onChange={e => setNameEn(e.target.value)} className="input-field w-full text-sm" placeholder="Mathematics" />
      </div>
      <div>
        <label className="text-xs text-white/30 block mb-1">Grade</label>
        <select value={grade} onChange={e => setGrade(Number(e.target.value))} className="input-field w-full text-sm">
          {[5,6,7,8,9,10].map(g => <option key={g} value={g}>Grade {g}</option>)}
        </select>
      </div>
      <button onClick={() => name && nameEn && onCreate(name, nameEn, grade)}
        className="btn-primary w-full text-sm" disabled={!name || !nameEn}>Create Subject</button>
    </div>
  );
}
