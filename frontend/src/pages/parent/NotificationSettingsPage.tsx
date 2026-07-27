/**
 * NotificationSettingsPage.tsx — Parent notification preferences.
 * 
 * Toggle WhatsApp/email notifications, view delivery history,
 * and preview the last Marathi weekly report.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import api from '../../api/client';

// ── Types ────────────────────────────────────────────────────────

interface NotificationPrefs {
  whatsapp: boolean;
  email: boolean;
}

interface NotificationHistoryItem {
  id: string;
  channel: string;
  template_name: string | null;
  content_preview: string | null;
  status: string;
  created_at: string;
  metadata: Record<string, unknown> | null;
}

interface WeeklyReport {
  student: { full_name: string; grade: number };
  summary_mr: string;
  ai_activity: { conversations: number; active_days: number };
  attendance: { percentage: number | null };
}

// ── Component ────────────────────────────────────────────────────

export function NotificationSettingsPage() {
  const { user } = useAuth();
  const [prefs, setPrefs] = useState<NotificationPrefs>({ whatsapp: true, email: false });
  const [history] = useState<NotificationHistoryItem[]>([]);
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // ── Data fetching ──────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [prefsRes, reportsRes] = await Promise.all([
        api.get('/api/parents/notifications'),
        api.get('/api/parents/reports').catch(() => ({ data: { reports: [] } })),
      ]);
      setPrefs(prefsRes.data.preferences || { whatsapp: true, email: false });
      setReports(reportsRes.data.reports || []);
    } catch (err) {
      console.error('Failed to load notification data', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // ── Save preferences ──────────────────────────────────────────

  const handleToggle = async (channel: 'whatsapp' | 'email') => {
    const newPrefs = { ...prefs, [channel]: !prefs[channel] };
    setPrefs(newPrefs);
    setSaving(true);
    setMessage(null);

    try {
      await api.put('/api/parents/notifications', newPrefs);
      setMessage({ type: 'success', text: '✅ सेटिंग्स जतन केले!' });
      setTimeout(() => setMessage(null), 3000);
    } catch {
      // Revert on failure
      setPrefs(prefs);
      setMessage({ type: 'error', text: '❌ सेटिंग्स जतन करता आली नाही' });
    } finally {
      setSaving(false);
    }
  };

  // ── Helpers ────────────────────────────────────────────────────

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleDateString('mr-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sent': return '📤';
      case 'delivered': return '✅';
      case 'read': return '👁️';
      case 'failed': return '❌';
      default: return '📨';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'sent': return 'पाठवले';
      case 'delivered': return 'वितरित';
      case 'read': return 'वाचले';
      case 'failed': return 'अयशस्वी';
      default: return status;
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'whatsapp': return '💬';
      case 'email': return '📧';
      case 'sms': return '📱';
      case 'push': return '🔔';
      default: return '📨';
    }
  };

  // ── Render ─────────────────────────────────────────────────────

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>लोड होत आहे...</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>🔔 सूचना सेटिंग्स</h1>
        <p style={styles.subtitle}>तुमच्या मुलाच्या प्रगतीचे अपडेट कसे मिळवायचे ते निवडा</p>
      </div>

      {/* Message */}
      {message && (
        <div style={{
          ...styles.message,
          background: message.type === 'success'
            ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1))'
            : 'linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.1))',
          borderColor: message.type === 'success' ? '#10b981' : '#ef4444',
        }}>
          {message.text}
        </div>
      )}

      {/* Notification Channels */}
      <div style={styles.channelSection}>
        <h2 style={styles.sectionTitle}>📡 सूचना चॅनेल</h2>

        {/* WhatsApp Toggle */}
        <div style={styles.channelCard}>
          <div style={styles.channelInfo}>
            <div style={styles.channelIconContainer}>
              <span style={styles.channelIconText}>💬</span>
            </div>
            <div>
              <h3 style={styles.channelName}>WhatsApp अहवाल</h3>
              <p style={styles.channelDesc}>
                दर आठवड्याला मराठीत प्रगती अहवाल WhatsApp वर मिळवा
              </p>
              <p style={styles.channelPhone}>
                📱 {user?.phone || 'फोन नंबर सेट नाही'}
              </p>
            </div>
          </div>
          <button
            style={{
              ...styles.toggleBtn,
              ...(prefs.whatsapp ? styles.toggleBtnOn : styles.toggleBtnOff),
            }}
            onClick={() => handleToggle('whatsapp')}
            disabled={saving}
          >
            <span style={{
              ...styles.toggleDot,
              ...(prefs.whatsapp ? styles.toggleDotOn : styles.toggleDotOff),
            }} />
          </button>
        </div>

        {/* Email Toggle */}
        <div style={styles.channelCard}>
          <div style={styles.channelInfo}>
            <div style={styles.channelIconContainer}>
              <span style={styles.channelIconText}>📧</span>
            </div>
            <div>
              <h3 style={styles.channelName}>ईमेल अहवाल</h3>
              <p style={styles.channelDesc}>
                साप्ताहिक प्रगती अहवाल ईमेल वर मिळवा (लवकरच)
              </p>
              <span style={styles.comingSoonBadge}>लवकरच</span>
            </div>
          </div>
          <button
            style={{
              ...styles.toggleBtn,
              ...(prefs.email ? styles.toggleBtnOn : styles.toggleBtnOff),
              opacity: 0.5,
            }}
            onClick={() => handleToggle('email')}
            disabled={saving}
          >
            <span style={{
              ...styles.toggleDot,
              ...(prefs.email ? styles.toggleDotOn : styles.toggleDotOff),
            }} />
          </button>
        </div>
      </div>

      {/* Report Preview */}
      {reports.length > 0 && (
        <div style={styles.previewSection}>
          <h2 style={styles.sectionTitle}>📋 अहवाल पूर्वावलोकन</h2>
          <p style={styles.previewSubtitle}>
            WhatsApp वर पाठवल्या जाणाऱ्या अहवालाचे नमुना
          </p>

          {reports.map((report, idx) => (
            <div key={idx} style={styles.reportPreviewCard}>
              <div style={styles.reportHeader}>
                <span style={styles.reportStudentName}>
                  👤 {report.student.full_name}
                </span>
                <span style={styles.reportGrade}>
                  इयत्ता {report.student.grade}
                </span>
              </div>

              {/* Stats Row */}
              <div style={styles.reportStats}>
                <div style={styles.reportStatItem}>
                  <span style={styles.reportStatValue}>
                    {report.ai_activity.conversations}
                  </span>
                  <span style={styles.reportStatLabel}>AI संवाद</span>
                </div>
                <div style={styles.reportStatItem}>
                  <span style={styles.reportStatValue}>
                    {report.ai_activity.active_days}/7
                  </span>
                  <span style={styles.reportStatLabel}>सक्रिय दिवस</span>
                </div>
                <div style={styles.reportStatItem}>
                  <span style={styles.reportStatValue}>
                    {report.attendance.percentage !== null
                      ? `${report.attendance.percentage}%`
                      : 'N/A'}
                  </span>
                  <span style={styles.reportStatLabel}>उपस्थिती</span>
                </div>
              </div>

              {/* Marathi Summary Preview */}
              <div style={styles.whatsappPreview}>
                <div style={styles.whatsappBubble}>
                  <pre style={styles.whatsappText}>{report.summary_mr}</pre>
                </div>
                <span style={styles.whatsappLabel}>
                  💬 WhatsApp संदेश पूर्वावलोकन
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delivery History */}
      {history.length > 0 && (
        <div style={styles.historySection}>
          <h2 style={styles.sectionTitle}>📜 वितरण इतिहास</h2>
          <div style={styles.historyList}>
            {history.map((item) => (
              <div key={item.id} style={styles.historyItem}>
                <span style={styles.historyIcon}>{getChannelIcon(item.channel)}</span>
                <div style={styles.historyContent}>
                  <span style={styles.historyTemplate}>
                    {item.template_name || 'Notification'}
                  </span>
                  <span style={styles.historyTime}>{formatDate(item.created_at)}</span>
                </div>
                <span style={styles.historyStatus}>
                  {getStatusIcon(item.status)} {getStatusLabel(item.status)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: 800,
    margin: '0 auto',
    padding: '24px 16px',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 400,
  },
  spinner: {
    width: 40,
    height: 40,
    border: '4px solid rgba(99, 102, 241, 0.2)',
    borderTop: '4px solid #6366f1',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
  loadingText: {
    marginTop: 16,
    color: '#94a3b8',
    fontSize: 14,
  },
  header: {
    textAlign: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 800,
    background: 'linear-gradient(135deg, #6366f1, #a855f7)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    marginBottom: 8,
  },
  subtitle: {
    color: '#94a3b8',
    fontSize: 16,
  },
  message: {
    padding: '14px 20px',
    borderRadius: 12,
    borderLeft: '4px solid',
    marginBottom: 24,
    fontSize: 14,
    color: '#e2e8f0',
  },
  channelSection: {
    marginBottom: 36,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 700,
    color: '#e2e8f0',
    marginBottom: 16,
  },
  channelCard: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    background: 'rgba(30, 41, 59, 0.6)',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    borderRadius: 16,
    padding: '20px 24px',
    marginBottom: 12,
    transition: 'all 0.3s ease',
  },
  channelInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  },
  channelIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.1))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  channelIconText: {
    fontSize: 24,
  },
  channelName: {
    fontSize: 16,
    fontWeight: 600,
    color: '#e2e8f0',
    marginBottom: 4,
  },
  channelDesc: {
    fontSize: 13,
    color: '#94a3b8',
    maxWidth: 400,
  },
  channelPhone: {
    fontSize: 12,
    color: '#6366f1',
    marginTop: 4,
  },
  comingSoonBadge: {
    display: 'inline-block',
    marginTop: 4,
    padding: '2px 8px',
    background: 'rgba(245, 158, 11, 0.15)',
    color: '#f59e0b',
    borderRadius: 8,
    fontSize: 11,
    fontWeight: 600,
  },
  toggleBtn: {
    width: 56,
    height: 30,
    borderRadius: 15,
    border: 'none',
    cursor: 'pointer',
    position: 'relative',
    transition: 'all 0.3s ease',
    flexShrink: 0,
  },
  toggleBtnOn: {
    background: 'linear-gradient(135deg, #6366f1, #a855f7)',
  },
  toggleBtnOff: {
    background: 'rgba(148, 163, 184, 0.2)',
  },
  toggleDot: {
    display: 'block',
    width: 22,
    height: 22,
    borderRadius: '50%',
    background: '#fff',
    position: 'absolute',
    top: 4,
    transition: 'all 0.3s ease',
    boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
  },
  toggleDotOn: {
    left: 30,
  },
  toggleDotOff: {
    left: 4,
  },
  previewSection: {
    marginBottom: 36,
  },
  previewSubtitle: {
    color: '#94a3b8',
    fontSize: 13,
    marginBottom: 16,
    marginTop: -8,
  },
  reportPreviewCard: {
    background: 'rgba(30, 41, 59, 0.6)',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    borderRadius: 16,
    padding: 24,
    marginBottom: 16,
  },
  reportHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  reportStudentName: {
    fontSize: 16,
    fontWeight: 600,
    color: '#e2e8f0',
  },
  reportGrade: {
    fontSize: 13,
    color: '#6366f1',
    fontWeight: 600,
  },
  reportStats: {
    display: 'flex',
    gap: 24,
    marginBottom: 20,
  },
  reportStatItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 4,
    flex: 1,
    padding: 12,
    background: 'rgba(99, 102, 241, 0.06)',
    borderRadius: 12,
  },
  reportStatValue: {
    fontSize: 20,
    fontWeight: 700,
    color: '#6366f1',
  },
  reportStatLabel: {
    fontSize: 11,
    color: '#94a3b8',
  },
  whatsappPreview: {
    marginTop: 8,
  },
  whatsappBubble: {
    background: 'linear-gradient(135deg, rgba(37, 211, 102, 0.08), rgba(37, 211, 102, 0.03))',
    border: '1px solid rgba(37, 211, 102, 0.2)',
    borderRadius: '4px 16px 16px 16px',
    padding: '16px 20px',
    marginBottom: 8,
  },
  whatsappText: {
    fontFamily: 'inherit',
    fontSize: 13,
    color: '#cbd5e1',
    lineHeight: 1.7,
    margin: 0,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  whatsappLabel: {
    fontSize: 11,
    color: '#94a3b8',
    display: 'flex',
    alignItems: 'center',
    gap: 4,
  },
  historySection: {
    marginBottom: 36,
  },
  historyList: {
    background: 'rgba(30, 41, 59, 0.6)',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    borderRadius: 12,
    overflow: 'hidden',
  },
  historyItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '14px 16px',
    borderBottom: '1px solid rgba(148, 163, 184, 0.06)',
  },
  historyIcon: {
    fontSize: 20,
  },
  historyContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
  },
  historyTemplate: {
    fontSize: 13,
    fontWeight: 600,
    color: '#e2e8f0',
  },
  historyTime: {
    fontSize: 11,
    color: '#94a3b8',
  },
  historyStatus: {
    fontSize: 12,
    color: '#94a3b8',
    fontWeight: 600,
    whiteSpace: 'nowrap',
  },
};
