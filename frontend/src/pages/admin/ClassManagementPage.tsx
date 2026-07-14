/**
 * ClassManagementPage — admin view: classes, teacher assignments.
 */
import { useState, useEffect } from 'react';
import { GraduationCap, Plus, UserPlus } from 'lucide-react';
import apiClient from '../../api/client';

interface ClassItem { id: string; grade: number; name: string; academic_year: string; }
interface Assignment { id: string; teacher_name: string; class_name: string; subject_id: string | null; }

export function ClassManagementPage() {
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [c, a] = await Promise.all([
        apiClient.get('/admin/classes'),
        apiClient.get('/admin/teacher-assign'),
      ]);
      setClasses(c.data.classes || []);
      setAssignments(a.data.assignments || []);
    } catch {} finally { setLoading(false); }
  }

  async function createClass(grade: number, name: string) {
    try {
      await apiClient.post('/admin/classes', { grade, name });
      setShowCreate(false);
      loadData();
    } catch {}
  }

  return (
    <div className="p-8 animate-fade-in" id="class-management">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <GraduationCap size={24} className="text-purple-400" /> Class Management
          </h1>
          <p className="text-white/40 mt-1 text-sm">Classes and teacher assignments</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm">
          <Plus size={16} /> Create Class
        </button>
      </div>

      {loading ? (
        <div className="glass-card p-12 text-center"><div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin mx-auto" /></div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Classes */}
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold mb-4 text-white/70">Classes ({classes.length})</h3>
            {classes.length === 0 ? (
              <p className="text-sm text-white/20 text-center py-4">No classes yet</p>
            ) : (
              <div className="space-y-2">
                {classes.map(c => (
                  <div key={c.id} className="p-3 rounded-lg bg-white/[0.02] flex justify-between items-center">
                    <div>
                      <span className="text-sm text-white/70">{c.name || `Grade ${c.grade}`}</span>
                      <span className="text-[10px] text-white/20 ml-2">{c.academic_year}</span>
                    </div>
                    <span className="text-xs text-brand-400">Grade {c.grade}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Teacher assignments */}
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold mb-4 text-white/70 flex items-center gap-2">
              <UserPlus size={14} /> Teacher Assignments ({assignments.length})
            </h3>
            {assignments.length === 0 ? (
              <p className="text-sm text-white/20 text-center py-4">No assignments yet</p>
            ) : (
              <div className="space-y-2">
                {assignments.map(a => (
                  <div key={a.id} className="p-3 rounded-lg bg-white/[0.02] flex justify-between items-center">
                    <span className="text-sm text-white/70">{a.teacher_name}</span>
                    <span className="text-xs text-purple-400">{a.class_name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="glass-card p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h3 className="font-semibold mb-4">Create Class</h3>
            <CreateClassForm onCreate={createClass} />
          </div>
        </div>
      )}
    </div>
  );
}

function CreateClassForm({ onCreate }: { onCreate: (grade: number, name: string) => void }) {
  const [grade, setGrade] = useState(7);
  const [name, setName] = useState('');
  return (
    <div className="space-y-3">
      <div>
        <label className="text-xs text-white/30 block mb-1">Grade</label>
        <select value={grade} onChange={e => setGrade(Number(e.target.value))} className="input-field w-full text-sm">
          {[5,6,7,8,9,10].map(g => <option key={g} value={g}>Grade {g}</option>)}
        </select>
      </div>
      <div>
        <label className="text-xs text-white/30 block mb-1">Name (optional)</label>
        <input value={name} onChange={e => setName(e.target.value)} className="input-field w-full text-sm" placeholder="Grade 7 - A" />
      </div>
      <button onClick={() => onCreate(grade, name || `Grade ${grade}`)} className="btn-primary w-full text-sm">Create</button>
    </div>
  );
}
