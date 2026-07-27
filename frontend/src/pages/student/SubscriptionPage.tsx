/**
 * SubscriptionPage.tsx — Subscription management for students.
 * 
 * Shows current subscription status, plan comparison, and payment flow.
 * Supports offline_mock (dev), razorpay_test, and razorpay_live modes.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import api from '../../api/client';

// ── Types ────────────────────────────────────────────────────────

interface SubscriptionPlan {
  id: string;
  name: string;
  description: string | null;
  price_inr: number;
  duration_days: number;
  features: Record<string, unknown> | null;
  is_active: boolean;
}

interface UserSubscription {
  has_active_subscription: boolean;
  plan_name: string | null;
  status: string | null;
  expires_at: string | null;
  days_remaining: number | null;
  features: Record<string, unknown> | null;
}

interface PaymentHistoryItem {
  id: string;
  amount_inr: number;
  currency: string;
  status: string;
  provider: string;
  subscription_name: string | null;
  paid_at: string | null;
  created_at: string;
}

// ── Component ────────────────────────────────────────────────────

export function SubscriptionPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [subscription, setSubscription] = useState<UserSubscription | null>(null);
  const [history, setHistory] = useState<PaymentHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // ── Data fetching ──────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [plansRes, subRes, histRes] = await Promise.all([
        api.get('/api/payments/plans'),
        api.get('/api/payments/subscription'),
        api.get('/api/payments/history'),
      ]);
      setPlans(plansRes.data.plans || []);
      setSubscription(subRes.data);
      setHistory(histRes.data.payments || []);
    } catch (err) {
      console.error('Failed to load subscription data', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // ── Payment flow ───────────────────────────────────────────────

  const handleSubscribe = async (planId: string) => {
    setProcessing(planId);
    setMessage(null);

    try {
      // 1. Create order on backend
      const orderRes = await api.post('/api/payments/create-order', {
        subscription_id: planId,
      });
      const orderData = orderRes.data;

      // 2. Check if we're using offline mock
      if (orderData.provider === 'offline_mock') {
        // Mock flow: auto-verify with mock signature
        await handleMockPayment(orderData);
        return;
      }

      // 3. Launch Razorpay checkout (for razorpay_test / razorpay_live)
      await launchRazorpayCheckout(orderData);

    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Payment failed';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setProcessing(null);
    }
  };

  const handleMockPayment = async (orderData: Record<string, unknown>) => {
    // Simulate a successful mock payment
    const mockPaymentId = `mock_pay_${Date.now()}`;

    // For offline_mock, generate the expected HMAC signature
    // The mock provider accepts any non-"fail" payment ID
    const mockSignature = 'mock_signature_for_dev';

    try {
      const verifyRes = await api.post('/api/payments/verify', {
        order_id: orderData.order_id,
        payment_id: mockPaymentId,
        signature: mockSignature,
      });

      if (verifyRes.data.success) {
        setMessage({ type: 'success', text: '✅ सदस्यता सक्रिय झाली! (Mock payment)' });
        fetchData();
      } else {
        setMessage({ type: 'error', text: verifyRes.data.message || 'Verification failed' });
      }
    } catch {
      setMessage({ type: 'error', text: 'Mock payment verification failed' });
    }
  };

  const launchRazorpayCheckout = async (orderData: Record<string, unknown>) => {
    // Razorpay Checkout.js must be loaded via <script> tag
    const Razorpay = (window as unknown as Record<string, unknown>).Razorpay;
    if (!Razorpay) {
      setMessage({
        type: 'error',
        text: 'Razorpay not loaded. Add the Razorpay checkout script to index.html.',
      });
      return;
    }

    const providerData = (orderData.provider_data || {}) as Record<string, unknown>;

    const options = {
      key: providerData.razorpay_key_id,
      amount: providerData.amount_paise,
      currency: 'INR',
      name: 'विद्यामित्र EdTech',
      description: `Subscription — ${(orderData.plan as Record<string, unknown>)?.name || 'Plan'}`,
      order_id: orderData.order_id,
      handler: async (response: Record<string, string>) => {
        // Verify on backend
        try {
          const verifyRes = await api.post('/api/payments/verify', {
            order_id: response.razorpay_order_id,
            payment_id: response.razorpay_payment_id,
            signature: response.razorpay_signature,
          });

          if (verifyRes.data.success) {
            setMessage({ type: 'success', text: '✅ सदस्यता सक्रिय झाली!' });
            fetchData();
          } else {
            setMessage({ type: 'error', text: verifyRes.data.message || 'Verification failed' });
          }
        } catch {
          setMessage({ type: 'error', text: 'Payment verification failed' });
        }
      },
      prefill: {
        contact: user?.phone || '',
      },
      theme: {
        color: '#6366f1',
      },
    };

    const rzp = new (Razorpay as new (opts: unknown) => { open: () => void })(options);
    rzp.open();
  };

  // ── Helpers ────────────────────────────────────────────────────

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleDateString('mr-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return '#10b981';
      case 'pending': return '#f59e0b';
      case 'failed': return '#ef4444';
      case 'refunded': return '#8b5cf6';
      default: return '#6b7280';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'success': return '✅ यशस्वी';
      case 'pending': return '⏳ प्रतीक्षेत';
      case 'failed': return '❌ अयशस्वी';
      case 'refunded': return '💸 परतावा';
      default: return status;
    }
  };

  const getPlanIcon = (name: string) => {
    if (name.includes('Free') || name.includes('Trial')) return '🎁';
    if (name.includes('Monthly')) return '📅';
    if (name.includes('Quarterly')) return '📆';
    if (name.includes('Annual')) return '🏆';
    return '📋';
  };

  const getPlanHighlight = (name: string) => {
    if (name.includes('Quarterly')) return 'सर्वात लोकप्रिय';
    if (name.includes('Annual')) return 'सर्वोत्तम मूल्य';
    return null;
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
        <h1 style={styles.title}>💳 सदस्यता व्यवस्थापन</h1>
        <p style={styles.subtitle}>तुमच्या शिक्षणाला पुढे नेण्यासाठी योग्य प्लान निवडा</p>
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

      {/* Current Subscription */}
      {subscription && (
        <div style={styles.currentSubCard}>
          <div style={styles.currentSubHeader}>
            <h2 style={styles.sectionTitle}>📌 सध्याची सदस्यता</h2>
            <span style={{
              ...styles.statusBadge,
              backgroundColor: subscription.has_active_subscription ? '#10b981' : '#6b7280',
            }}>
              {subscription.has_active_subscription ? '✅ सक्रिय' : '⏸️ निष्क्रिय'}
            </span>
          </div>

          {subscription.has_active_subscription ? (
            <div style={styles.currentSubDetails}>
              <div style={styles.subDetailItem}>
                <span style={styles.subDetailLabel}>प्लान</span>
                <span style={styles.subDetailValue}>{subscription.plan_name}</span>
              </div>
              <div style={styles.subDetailItem}>
                <span style={styles.subDetailLabel}>समाप्ती</span>
                <span style={styles.subDetailValue}>
                  {subscription.expires_at ? formatDate(subscription.expires_at) : '—'}
                </span>
              </div>
              <div style={styles.subDetailItem}>
                <span style={styles.subDetailLabel}>उर्वरित</span>
                <span style={{
                  ...styles.subDetailValue,
                  color: (subscription.days_remaining ?? 0) < 7 ? '#ef4444' : '#10b981',
                }}>
                  {subscription.days_remaining} दिवस
                </span>
              </div>
            </div>
          ) : (
            <p style={styles.noSubText}>
              तुमची कोणतीही सक्रिय सदस्यता नाही। खालील प्लानमधून एक निवडा.
            </p>
          )}
        </div>
      )}

      {/* Plans Grid */}
      <h2 style={styles.sectionTitle}>📋 उपलब्ध प्लान</h2>
      <div style={styles.plansGrid}>
        {plans.map((plan) => {
          const highlight = getPlanHighlight(plan.name);
          const isCurrentPlan = subscription?.plan_name === plan.name && subscription?.has_active_subscription;

          return (
            <div
              key={plan.id}
              style={{
                ...styles.planCard,
                ...(highlight ? styles.planCardHighlighted : {}),
                ...(isCurrentPlan ? styles.planCardCurrent : {}),
              }}
            >
              {highlight && (
                <div style={styles.planBadge}>{highlight}</div>
              )}

              <div style={styles.planIcon}>{getPlanIcon(plan.name)}</div>
              <h3 style={styles.planName}>{plan.name}</h3>

              <div style={styles.planPricing}>
                <span style={styles.planPrice}>
                  {plan.price_inr === 0 ? 'मोफत' : `₹${plan.price_inr}`}
                </span>
                <span style={styles.planDuration}>
                  / {plan.duration_days} दिवस
                </span>
              </div>

              {plan.description && (
                <p style={styles.planDescription}>{plan.description}</p>
              )}

              {/* Features */}
              <ul style={styles.featureList}>
                {plan.features && Object.entries(plan.features).map(([key, val]) => (
                  <li key={key} style={styles.featureItem}>
                    <span style={styles.featureCheck}>
                      {val === true || (typeof val === 'number' && val !== 0) ? '✅' : '❌'}
                    </span>
                    <span style={styles.featureText}>
                      {key === 'ai_conversations_per_day'
                        ? val === -1 ? 'अमर्यादित AI संवाद' : `${val} AI संवाद/दिवस`
                        : key === 'voice_enabled'
                          ? 'आवाज चॅट'
                          : key === 'weekly_reports'
                            ? 'साप्ताहिक अहवाल'
                            : key === 'priority_support'
                              ? 'प्राधान्य सहाय्य'
                              : key === 'early_access'
                                ? 'नवीन वैशिष्ट्ये लवकर'
                                : key.replace(/_/g, ' ')}
                    </span>
                  </li>
                ))}
              </ul>

              <button
                style={{
                  ...styles.subscribeBtn,
                  ...(isCurrentPlan ? styles.subscribeBtnCurrent : {}),
                  ...(processing === plan.id ? styles.subscribeBtnProcessing : {}),
                }}
                disabled={isCurrentPlan || processing !== null}
                onClick={() => handleSubscribe(plan.id)}
              >
                {processing === plan.id
                  ? '⏳ प्रक्रिया सुरू...'
                  : isCurrentPlan
                    ? '✅ सध्याचा प्लान'
                    : plan.price_inr === 0
                      ? '🎁 मोफत सुरू करा'
                      : '💳 सदस्यता घ्या'}
              </button>
            </div>
          );
        })}
      </div>

      {/* Payment History */}
      {history.length > 0 && (
        <div style={styles.historySection}>
          <h2 style={styles.sectionTitle}>📜 पेमेंट इतिहास</h2>
          <div style={styles.historyTable}>
            <div style={styles.historyHeader}>
              <span style={styles.historyCol}>प्लान</span>
              <span style={styles.historyCol}>रक्कम</span>
              <span style={styles.historyCol}>स्थिती</span>
              <span style={styles.historyCol}>तारीख</span>
            </div>
            {history.map((item) => (
              <div key={item.id} style={styles.historyRow}>
                <span style={styles.historyCol}>
                  {item.subscription_name || '—'}
                </span>
                <span style={styles.historyCol}>₹{item.amount_inr}</span>
                <span style={{
                  ...styles.historyCol,
                  color: getStatusColor(item.status),
                  fontWeight: 600,
                }}>
                  {getStatusLabel(item.status)}
                </span>
                <span style={styles.historyCol}>
                  {item.paid_at ? formatDate(item.paid_at) : formatDate(item.created_at)}
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
    maxWidth: 1100,
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
  currentSubCard: {
    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(168, 85, 247, 0.05))',
    border: '1px solid rgba(99, 102, 241, 0.2)',
    borderRadius: 16,
    padding: 24,
    marginBottom: 32,
  },
  currentSubHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 700,
    color: '#e2e8f0',
    marginBottom: 16,
  },
  statusBadge: {
    padding: '4px 12px',
    borderRadius: 20,
    color: '#fff',
    fontSize: 12,
    fontWeight: 600,
  },
  currentSubDetails: {
    display: 'flex',
    gap: 32,
    flexWrap: 'wrap',
  },
  subDetailItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  subDetailLabel: {
    fontSize: 12,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  subDetailValue: {
    fontSize: 18,
    fontWeight: 700,
    color: '#e2e8f0',
  },
  noSubText: {
    color: '#94a3b8',
    fontSize: 14,
  },
  plansGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: 20,
    marginBottom: 40,
  },
  planCard: {
    background: 'rgba(30, 41, 59, 0.6)',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    borderRadius: 16,
    padding: 24,
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    transition: 'all 0.3s ease',
  },
  planCardHighlighted: {
    border: '2px solid #6366f1',
    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(30, 41, 59, 0.8))',
    transform: 'scale(1.02)',
  },
  planCardCurrent: {
    border: '2px solid #10b981',
    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(30, 41, 59, 0.8))',
  },
  planBadge: {
    position: 'absolute',
    top: -12,
    left: '50%',
    transform: 'translateX(-50%)',
    background: 'linear-gradient(135deg, #6366f1, #a855f7)',
    color: '#fff',
    padding: '4px 16px',
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 700,
    whiteSpace: 'nowrap',
  },
  planIcon: {
    fontSize: 40,
    marginBottom: 12,
  },
  planName: {
    fontSize: 18,
    fontWeight: 700,
    color: '#e2e8f0',
    marginBottom: 8,
  },
  planPricing: {
    marginBottom: 12,
  },
  planPrice: {
    fontSize: 28,
    fontWeight: 800,
    color: '#6366f1',
  },
  planDuration: {
    fontSize: 14,
    color: '#94a3b8',
    marginLeft: 4,
  },
  planDescription: {
    fontSize: 13,
    color: '#94a3b8',
    marginBottom: 16,
    lineHeight: 1.5,
  },
  featureList: {
    listStyle: 'none',
    padding: 0,
    margin: '0 0 20px 0',
    width: '100%',
    textAlign: 'left',
  },
  featureItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '4px 0',
    fontSize: 13,
    color: '#cbd5e1',
  },
  featureCheck: {
    fontSize: 12,
  },
  featureText: {},
  subscribeBtn: {
    width: '100%',
    padding: '12px 20px',
    background: 'linear-gradient(135deg, #6366f1, #a855f7)',
    color: '#fff',
    border: 'none',
    borderRadius: 12,
    fontSize: 14,
    fontWeight: 700,
    cursor: 'pointer',
    marginTop: 'auto',
    transition: 'all 0.3s ease',
  },
  subscribeBtnCurrent: {
    background: 'rgba(16, 185, 129, 0.2)',
    color: '#10b981',
    cursor: 'default',
  },
  subscribeBtnProcessing: {
    opacity: 0.7,
    cursor: 'wait',
  },
  historySection: {
    marginTop: 16,
  },
  historyTable: {
    background: 'rgba(30, 41, 59, 0.6)',
    border: '1px solid rgba(148, 163, 184, 0.1)',
    borderRadius: 12,
    overflow: 'hidden',
  },
  historyHeader: {
    display: 'grid',
    gridTemplateColumns: '1fr 100px 120px 140px',
    padding: '12px 16px',
    background: 'rgba(99, 102, 241, 0.1)',
    fontSize: 12,
    fontWeight: 600,
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  historyRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 100px 120px 140px',
    padding: '12px 16px',
    borderTop: '1px solid rgba(148, 163, 184, 0.06)',
    fontSize: 13,
    color: '#cbd5e1',
  },
  historyCol: {
    display: 'flex',
    alignItems: 'center',
  },
};
