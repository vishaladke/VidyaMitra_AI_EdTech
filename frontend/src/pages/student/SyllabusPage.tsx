/**
 * SyllabusPage — subject grid and chapter/topic browser.
 *
 * Shows a grid of subject cards, clicking one expands into the chapter/topic tree.
 * Fetches from backend /api/syllabus endpoints.
 */
import { useState, useEffect } from 'react';
import { ArrowLeft, BookOpen, Search } from 'lucide-react';
import { SubjectCard } from '../../components/syllabus/SubjectCard';
import { TopicTree } from '../../components/syllabus/TopicTree';
import apiClient from '../../api/client';

interface Subject {
  id: string;
  name: string;
  name_en?: string;
  grade: number;
  icon_url?: string;
  display_order: number;
}

interface TreeNode {
  id: string;
  title: string;
  title_en?: string;
  unit_type: 'chapter' | 'topic' | 'subtopic';
  display_order: number;
  children?: TreeNode[];
}

export function SyllabusPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [treeLoading, setTreeLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Load subjects on mount
  useEffect(() => {
    loadSubjects();
  }, []);

  async function loadSubjects() {
    try {
      setLoading(true);
      const { data } = await apiClient.get('/syllabus/subjects');
      setSubjects(data);
    } catch (err) {
      console.error('Failed to load subjects:', err);
      // Show placeholder subjects if API fails (demo mode)
      setSubjects([
        { id: '1', name: 'गणित', name_en: 'Mathematics', grade: 7, display_order: 1 },
        { id: '2', name: 'विज्ञान', name_en: 'Science', grade: 7, display_order: 2 },
        { id: '3', name: 'मराठी', name_en: 'Marathi', grade: 7, display_order: 3 },
        { id: '4', name: 'हिंदी', name_en: 'Hindi', grade: 7, display_order: 4 },
        { id: '5', name: 'English', name_en: 'English', grade: 7, display_order: 5 },
        { id: '6', name: 'सामाजिक शास्त्र', name_en: 'Social Studies', grade: 7, display_order: 6 },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function loadTree(subjectId: string) {
    try {
      setTreeLoading(true);
      const { data } = await apiClient.get(`/syllabus/subjects/${subjectId}/tree`);
      setTree(data);
    } catch (err) {
      console.error('Failed to load tree:', err);
      setTree([]);
    } finally {
      setTreeLoading(false);
    }
  }

  function handleSubjectClick(id: string) {
    const subject = subjects.find(s => s.id === id);
    if (subject) {
      setSelectedSubject(subject);
      loadTree(id);
    }
  }

  function handleBack() {
    setSelectedSubject(null);
    setTree([]);
    setSearchQuery('');
  }

  function handleTopicClick(topicId: string, topicTitle: string) {
    // Navigate to AI Guru with this topic pre-selected
    // For now, just log it
    console.log(`Topic selected: ${topicTitle} (${topicId})`);
  }

  const filteredSubjects = subjects.filter(s =>
    s.name.includes(searchQuery) || (s.name_en?.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="p-8 animate-fade-in" id="syllabus-page">
      {/* Subject detail view */}
      {selectedSubject ? (
        <>
          {/* Header with back button */}
          <div className="flex items-center gap-4 mb-8">
            <button
              onClick={handleBack}
              className="p-2 rounded-xl hover:bg-white/5 text-white/50 hover:text-white transition-all"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl font-bold font-marathi">{selectedSubject.name}</h1>
              {selectedSubject.name_en && (
                <p className="text-sm text-white/40">{selectedSubject.name_en} — इयत्ता {selectedSubject.grade}</p>
              )}
            </div>
          </div>

          {/* Topic tree */}
          <div className="glass-card p-6">
            {treeLoading ? (
              <div className="flex items-center justify-center py-16">
                <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
              </div>
            ) : (
              <TopicTree nodes={tree} onTopicClick={handleTopicClick} />
            )}
          </div>
        </>
      ) : (
        <>
          {/* Subject grid view */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold font-marathi flex items-center gap-3">
              <BookOpen size={24} className="text-brand-400" />
              अभ्यासक्रम
            </h1>
            <p className="text-white/40 mt-1 font-marathi text-sm">तुमचे विषय निवडा आणि अध्याय ब्राउझ करा</p>
          </div>

          {/* Search */}
          <div className="relative mb-6 max-w-md">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="विषय शोधा..."
              className="input-field pl-10 text-sm"
              id="syllabus-search"
            />
          </div>

          {/* Subject grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="glass-card p-5 animate-pulse">
                  <div className="w-12 h-12 rounded-xl bg-white/5 mb-4" />
                  <div className="h-5 bg-white/5 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-white/5 rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredSubjects
                .sort((a, b) => a.display_order - b.display_order)
                .map(subject => (
                  <SubjectCard
                    key={subject.id}
                    id={subject.id}
                    name={subject.name}
                    nameEn={subject.name_en}
                    grade={subject.grade}
                    iconUrl={subject.icon_url}
                    progressPct={0}
                    onClick={handleSubjectClick}
                  />
                ))}
            </div>
          )}

          {/* Empty state */}
          {!loading && filteredSubjects.length === 0 && (
            <div className="text-center py-16">
              <p className="text-white/30 font-marathi">कोणताही विषय सापडला नाही</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
