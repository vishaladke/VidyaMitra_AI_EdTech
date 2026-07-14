/**
 * AttendancePage — mark and view attendance for students.
 */
import { useState, useEffect } from 'react';
import { Calendar, Check, X, Clock, Save } from 'lucide-react';
import apiClient from '../../api/client';

interface Student {
  id: string;
  full_name: string;
  grade: number | null;
}

type Status = 'present' | 'absent' | 'late';

export function AttendancePage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [attendance, setAttendance] = useState<Record<string, Status>>({});
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadStudents();
  }, []);

  async function loadStudents() {
    try {
      setLoading(true);
      const { data } = await apiClient.get('/teachers/students');
      setStudents(data.students || []);
      // Default all to present
      const defaults: Record<string, Status> = {};
      (data.students || []).forEach((s: Student) => { defaults[s.id] = 'present'; });
      setAttendance(defaults);
    } catch {
      setStudents([]);
    } finally {
      setLoading(false);
    }
  }

  function toggleStatus(studentId: string) {
    setAttendance(prev => {
      const current = prev[studentId] || 'present';
      const next: Status = current === 'present' ? 'absent' : current === 'absent' ? 'late' : 'present';
      return { ...prev, [studentId]: next };
    });
    setSaved(false);
  }

  async function saveAttendance() {
    setSaving(true);
    try {
      const records = Object.entries(attendance).map(([id, status]) => ({
        student_id: id,
        status,
      }));
      await apiClient.post('/teachers/attendance/bulk', {
        class_id: '00000000-0000-0000-0000-000000000000', // placeholder for pilot
        date: selectedDate,
        records,
      });
      setSaved(true);
    } catch (err) {
      console.error('Failed to save attendance:', err);
    } finally {
      setSaving(false);
    }
  }

  const presentCount = Object.values(attendance).filter(s => s === 'present').length;
  const absentCount = Object.values(attendance).filter(s => s === 'absent').length;
  const lateCount = Object.values(attendance).filter(s => s === 'late').length;

  const STATUS_CONFIG = {
    present: { icon: <Check size={16} />, label: 'उपस्थित', bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' },
    absent: { icon: <X size={16} />, label: 'अनुपस्थित', bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' },
    late: { icon: <Clock size={16} />, label: 'उशीर', bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' },
  };

  return (
    <div className="p-8 animate-fade-in" id="attendance-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold font-marathi flex items-center gap-3">
            <Calendar size={24} className="text-emerald-400" />
            उपस्थिती
          </h1>
          <p className="text-white/40 mt-1 font-marathi text-sm">विद्यार्थ्यांची उपस्थिती नोंदवा</p>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="date"
            value={selectedDate}
            onChange={e => { setSelectedDate(e.target.value); setSaved(false); }}
            className="input-field text-sm w-44"
            id="attendance-date"
          />
          <button
            onClick={saveAttendance}
            disabled={saving || students.length === 0}
            className="btn-primary flex items-center gap-2 text-sm"
            id="save-attendance"
          >
            <Save size={16} />
            {saving ? 'सेव्ह होत आहे...' : saved ? '✅ सेव्ह झाले' : 'सेव्ह करा'}
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="glass-card p-3 bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 text-center">
          <div className="text-lg font-bold text-emerald-400">{presentCount}</div>
          <div className="text-[10px] text-white/40 font-marathi">उपस्थित</div>
        </div>
        <div className="glass-card p-3 bg-gradient-to-br from-red-500/10 to-red-600/5 text-center">
          <div className="text-lg font-bold text-red-400">{absentCount}</div>
          <div className="text-[10px] text-white/40 font-marathi">अनुपस्थित</div>
        </div>
        <div className="glass-card p-3 bg-gradient-to-br from-amber-500/10 to-amber-600/5 text-center">
          <div className="text-lg font-bold text-amber-400">{lateCount}</div>
          <div className="text-[10px] text-white/40 font-marathi">उशीर</div>
        </div>
      </div>

      {/* Student list */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="glass-card p-4 animate-pulse">
              <div className="h-5 bg-white/5 rounded w-1/3" />
            </div>
          ))}
        </div>
      ) : students.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <p className="text-white/30 font-marathi">कोणतेही विद्यार्थी सापडले नाहीत</p>
        </div>
      ) : (
        <div className="space-y-2">
          {students.map(student => {
            const status = attendance[student.id] || 'present';
            const config = STATUS_CONFIG[status];

            return (
              <button
                key={student.id}
                onClick={() => toggleStatus(student.id)}
                className={`glass-card w-full p-4 flex items-center justify-between 
                           hover:bg-white/[0.03] transition-all group ${config.border} border`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full ${config.bg} flex items-center justify-center ${config.text}`}>
                    {config.icon}
                  </div>
                  <div className="text-left">
                    <span className="text-sm font-marathi text-white/80 group-hover:text-white">
                      {student.full_name}
                    </span>
                    {student.grade && (
                      <span className="text-[10px] text-white/20 ml-2">इयत्ता {student.grade}</span>
                    )}
                  </div>
                </div>

                <span className={`text-xs px-3 py-1 rounded-full ${config.bg} ${config.text} font-marathi`}>
                  {config.label}
                </span>
              </button>
            );
          })}
        </div>
      )}

      <p className="text-[10px] text-white/20 text-center mt-6 font-marathi">
        टॅप करा: उपस्थित → अनुपस्थित → उशीर → उपस्थित
      </p>
    </div>
  );
}
