/**
 * Login page — phone number → OTP → (TOTP for Super Admin) → dashboard.
 * 
 * Includes first-time registration: name + role + grade selection.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { requestOTP, verifyOTP, verifyTOTP } from '../../api/auth';

type Step = 'phone' | 'otp' | 'register' | 'totp';

const ROLE_OPTIONS = [
  { value: 'student', label: 'विद्यार्थी (Student)', icon: '🎓' },
  { value: 'teacher', label: 'शिक्षक (Teacher)', icon: '👨‍🏫' },
  { value: 'parent', label: 'पालक (Parent)', icon: '👨‍👧‍👦' },
];

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [step, setStep] = useState<Step>('phone');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('student');
  const [grade, setGrade] = useState(5);
  const [totpCode, setTotpCode] = useState('');
  const [tempToken, setTempToken] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleRequestOTP = async () => {
    setError('');
    setIsLoading(true);
    try {
      await requestOTP(phone);
      setStep('otp');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'OTP पाठवता आले नाही');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOTP = async (regName?: string, regRole?: string, regGrade?: number) => {
    setError('');
    setIsLoading(true);
    try {
      const result = await verifyOTP(phone, otp, regName, regRole, regGrade);

      if (result.requires_registration) {
        setStep('register');
        return;
      }

      if (result.requires_totp && result.temp_token) {
        setTempToken(result.temp_token);
        setStep('totp');
        return;
      }

      if (result.access_token && result.refresh_token && result.user) {
        login(result.access_token, result.refresh_token, result.user);
        navigateToDashboard(result.user.role);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'OTP चुकीचा आहे');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = () => {
    handleVerifyOTP(fullName, role, grade);
  };

  const handleVerifyTOTP = async () => {
    setError('');
    setIsLoading(true);
    try {
      const result = await verifyTOTP(tempToken, totpCode);
      if (result.access_token && result.refresh_token && result.user) {
        login(result.access_token, result.refresh_token, result.user);
        navigateToDashboard(result.user.role);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'TOTP चुकीचा आहे');
    } finally {
      setIsLoading(false);
    }
  };

  const navigateToDashboard = (userRole: string) => {
    const paths: Record<string, string> = {
      student: '/student',
      teacher: '/teacher',
      parent: '/parent',
      admin: '/admin',
      super_admin: '/super-admin',
    };
    navigate(paths[userRole] || '/');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-950 px-4">
      <div className="w-full max-w-md animate-fade-in">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">🎓</div>
          <h1 className="text-3xl font-bold font-marathi bg-gradient-to-r from-brand-400 to-brand-600 bg-clip-text text-transparent">
            विद्यामित्र
          </h1>
          <p className="text-white/50 mt-2 font-marathi">AI शिक्षण मंच</p>
        </div>

        {/* Card */}
        <div className="glass-card p-8">
          {error && (
            <div className="mb-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm animate-fade-in">
              {error}
            </div>
          )}

          {/* Step: Phone */}
          {step === 'phone' && (
            <div className="space-y-4 animate-slide-up">
              <div>
                <label className="block text-sm text-white/60 mb-2 font-marathi">
                  मोबाइल नंबर
                </label>
                <input
                  type="tel"
                  className="input-field text-lg tracking-wider"
                  placeholder="9999999999"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                  maxLength={10}
                  autoFocus
                />
              </div>
              <button
                className="btn-primary w-full"
                onClick={handleRequestOTP}
                disabled={phone.length < 10 || isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    पाठवत आहे...
                  </span>
                ) : (
                  'OTP पाठवा'
                )}
              </button>
            </div>
          )}

          {/* Step: OTP */}
          {step === 'otp' && (
            <div className="space-y-4 animate-slide-up">
              <div>
                <label className="block text-sm text-white/60 mb-2 font-marathi">
                  OTP टाका ({phone})
                </label>
                <input
                  type="text"
                  className="input-field text-center text-2xl tracking-[0.5em]"
                  placeholder="------"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  maxLength={6}
                  autoFocus
                />
              </div>
              <button
                className="btn-primary w-full"
                onClick={() => handleVerifyOTP()}
                disabled={otp.length < 6 || isLoading}
              >
                {isLoading ? 'तपासत आहे...' : 'पुष्टी करा'}
              </button>
              <button
                className="btn-secondary w-full text-sm"
                onClick={() => { setStep('phone'); setOtp(''); setError(''); }}
              >
                ← नंबर बदला
              </button>
            </div>
          )}

          {/* Step: Registration (first-time user) */}
          {step === 'register' && (
            <div className="space-y-4 animate-slide-up">
              <h2 className="text-lg font-semibold font-marathi text-center">नोंदणी करा</h2>
              <div>
                <label className="block text-sm text-white/60 mb-2 font-marathi">पूर्ण नाव</label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="तुमचे नाव"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2 font-marathi">तुम्ही कोण आहात?</label>
                <div className="grid grid-cols-3 gap-2">
                  {ROLE_OPTIONS.map((r) => (
                    <button
                      key={r.value}
                      className={`p-3 rounded-xl text-center transition-all duration-200 ${
                        role === r.value
                          ? 'bg-brand-500/20 border border-brand-500/40 text-white'
                          : 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10'
                      }`}
                      onClick={() => setRole(r.value)}
                    >
                      <div className="text-2xl mb-1">{r.icon}</div>
                      <div className="text-xs font-marathi">{r.label.split(' ')[0]}</div>
                    </button>
                  ))}
                </div>
              </div>
              {role === 'student' && (
                <div>
                  <label className="block text-sm text-white/60 mb-2 font-marathi">इयत्ता (Grade)</label>
                  <select
                    className="input-field"
                    value={grade}
                    onChange={(e) => setGrade(Number(e.target.value))}
                  >
                    {[1,2,3,4,5,6,7,8,9,10,11,12].map((g) => (
                      <option key={g} value={g} className="bg-surface-900">
                        इयत्ता {g}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <button
                className="btn-primary w-full"
                onClick={handleRegister}
                disabled={!fullName.trim() || isLoading}
              >
                {isLoading ? 'नोंदणी करत आहे...' : 'नोंदणी पूर्ण करा'}
              </button>
            </div>
          )}

          {/* Step: TOTP (Super Admin only) */}
          {step === 'totp' && (
            <div className="space-y-4 animate-slide-up">
              <div className="text-center">
                <div className="text-3xl mb-2">🔐</div>
                <h2 className="text-lg font-semibold">Authenticator Code</h2>
                <p className="text-white/50 text-sm mt-1">
                  Enter the code from your authenticator app
                </p>
              </div>
              <input
                type="text"
                className="input-field text-center text-2xl tracking-[0.5em]"
                placeholder="------"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength={6}
                autoFocus
              />
              <button
                className="btn-primary w-full"
                onClick={handleVerifyTOTP}
                disabled={totpCode.length < 6 || isLoading}
              >
                {isLoading ? 'Verifying...' : 'Verify'}
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-white/30 text-xs mt-6 font-marathi">
          सोलापूर, महाराष्ट्र • विद्यामित्र AI शिक्षण मंच
        </p>
      </div>
    </div>
  );
}
