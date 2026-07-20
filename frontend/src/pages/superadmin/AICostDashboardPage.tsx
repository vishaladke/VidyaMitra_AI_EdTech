/**
 * AICostDashboardPage — Detailed AI cost breakdown with period selector,
 * per-user costs, cache source breakdown, and daily trend.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DollarSign, ArrowLeft, TrendingUp, Cpu, Users, Zap, Database, Cloud,
  RefreshCw, BarChart3,
} from 'lucide-react';
import apiClient from '../../api/client';

interface CostBySource {
  source: string;
  count: number;
  cost_inr: number;
  input_tokens: number;
  output_tokens: number;
}

interface PerUserCost {
  student_id: string;
  student_name: string;
  requests: number;
  cost_inr: number;
}

interface DailyTrend {
  date: string;
  requests: number;
  cost_inr: number;
}

interface CostDashboard {
  period_days: number;
  total_cost_inr: number;
  total_requests: number;
  cache_hit_rate: number;
  by_source: CostBySource[];
  per_user: PerUserCost[];
  daily_trend: DailyTrend[];
}

const PERIODS = [
  { value: 7, label: '7 days' },
  { value: 14, label: '14 days' },
  { value: 30, label: '30 days' },
  { value: 90, label: '90 days' },
];

const SOURCE_META: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  exact_match: { label: 'Exact Match (Redis)', icon: <Zap size={16} />, color: 'text-emerald-400' },
  semantic_cache: { label: 'Semantic Cache (pgvector)', icon: <Database size={16} />, color: 'text-blue-400' },
  faq_bank: { label: 'FAQ Bank', icon: <BarChart3 size={16} />, color: 'text-purple-400' },
  live_llm: { label: 'Live LLM Call', icon: <Cloud size={16} />, color: 'text-orange-400' },
};

export function AICostDashboardPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<CostDashboard | null>(null);
  const [period, setPeriod] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [period]);

  async function loadData() {
    try {
      setLoading(true);
      const { data: resp } = await apiClient.get(`/super-admin/ai-costs?days=${period}`);
      setData(resp);
    } catch { /* error */ } finally { setLoading(false); }
  }

  const maxDailyCost = data?.daily_trend?.length
    ? Math.max(...data.daily_trend.map(d => d.cost_inr), 0.01)
    : 1;

  return (
    <div className="p-8 animate-fade-in" id="ai-cost-dashboard">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => navigate('/super-admin')}
          className="p-2 rounded-lg hover:bg-white/5 text-white/40 hover:text-white transition-all">
          <ArrowLeft size={20} />
        </button>
        <DollarSign size={28} className="text-green-400" />
        <div className="flex-1">
          <h1 className="text-2xl font-bold">AI Cost Dashboard</h1>
          <p className="text-white/40 text-sm">Token usage, costs, and cache performance</p>
        </div>
        <button onClick={loadData}
          className="p-2 rounded-lg hover:bg-white/5 text-white/30 hover:text-white transition-all">
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Period selector */}
      <div className="flex gap-2 mb-6">
        {PERIODS.map(p => (
          <button key={p.value} onClick={() => setPeriod(p.value)}
            className={`px-4 py-2 rounded-lg text-sm transition-all ${
              period === p.value
                ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                : 'text-white/40 hover:bg-white/5 border border-transparent'
            }`}>{p.label}</button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => <div key={i} className="glass-card p-6 animate-pulse"><div className="h-8 bg-white/5 rounded w-1/3" /></div>)}
        </div>
      ) : data ? (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <SummaryCard icon={<DollarSign size={18} />} label="Total Cost"
              value={`₹${data.total_cost_inr.toFixed(2)}`}
              gradient="from-green-500/20 to-emerald-500/10" />
            <SummaryCard icon={<Cpu size={18} />} label="Total Requests"
              value={data.total_requests.toLocaleString()}
              gradient="from-blue-500/20 to-cyan-500/10" />
            <SummaryCard icon={<TrendingUp size={18} />} label="Cache Hit Rate"
              value={`${data.cache_hit_rate}%`}
              sub={data.cache_hit_rate >= 70 ? '✓ Healthy' : '⚠ Low'}
              gradient="from-purple-500/20 to-brand-500/10" />
            <SummaryCard icon={<DollarSign size={18} />} label="Avg Cost/Request"
              value={`₹${data.total_requests ? (data.total_cost_inr / data.total_requests).toFixed(4) : '0.0000'}`}
              gradient="from-orange-500/20 to-red-500/10" />
          </div>

          {/* Daily trend chart */}
          {data.daily_trend.length > 0 && (
            <div className="glass-card p-6 mb-8">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <TrendingUp size={18} className="text-green-400" /> Daily Cost Trend
              </h2>
              <div className="flex items-end gap-1 h-32">
                {data.daily_trend.map((d, i) => {
                  const height = Math.max((d.cost_inr / maxDailyCost) * 100, 2);
                  return (
                    <div key={i} className="flex-1 group relative flex flex-col items-center justify-end">
                      <div className="absolute -top-8 left-1/2 -translate-x-1/2 hidden group-hover:block
                        bg-gray-900 text-xs px-2 py-1 rounded whitespace-nowrap z-10 border border-white/10">
                        <div className="text-white/70">{d.date}</div>
                        <div className="text-green-400">₹{d.cost_inr.toFixed(2)}</div>
                        <div className="text-white/30">{d.requests} req</div>
                      </div>
                      <div
                        className="w-full rounded-t bg-gradient-to-t from-green-500/40 to-green-400/20
                          hover:from-green-500/60 hover:to-green-400/40 transition-all cursor-pointer
                          min-h-[2px]"
                        style={{ height: `${height}%` }}
                      />
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-between mt-2 text-[9px] text-white/20">
                <span>{data.daily_trend[0]?.date}</span>
                <span>{data.daily_trend[data.daily_trend.length - 1]?.date}</span>
              </div>
            </div>
          )}

          {/* Cache source breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="glass-card p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Database size={18} className="text-blue-400" /> Cost by Source
              </h2>
              <div className="space-y-3">
                {data.by_source.map(s => {
                  const meta = SOURCE_META[s.source] || { label: s.source, icon: <Cpu size={16} />, color: 'text-white/60' };
                  const pct = data.total_requests ? Math.round(s.count / data.total_requests * 100) : 0;
                  return (
                    <div key={s.source} className="flex items-center gap-3">
                      <div className={`${meta.color}`}>{meta.icon}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm text-white/70">{meta.label}</span>
                          <span className="text-xs text-white/30">{s.count} ({pct}%)</span>
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-green-500/60 to-green-400/40 rounded-full transition-all duration-500"
                            style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                      <span className="text-sm font-medium text-green-400 whitespace-nowrap">₹{s.cost_inr.toFixed(2)}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Token usage */}
            <div className="glass-card p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Cpu size={18} className="text-purple-400" /> Token Usage by Source
              </h2>
              <div className="space-y-3">
                {data.by_source.filter(s => s.input_tokens > 0 || s.output_tokens > 0).map(s => {
                  const meta = SOURCE_META[s.source] || { label: s.source, icon: <Cpu size={16} />, color: 'text-white/60' };
                  return (
                    <div key={s.source} className="glass-card p-3 bg-white/[0.02]">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={meta.color}>{meta.icon}</span>
                        <span className="text-sm text-white/60">{meta.label}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <div className="text-[10px] text-white/20 uppercase">Input Tokens</div>
                          <div className="text-sm font-medium">{s.input_tokens.toLocaleString()}</div>
                        </div>
                        <div>
                          <div className="text-[10px] text-white/20 uppercase">Output Tokens</div>
                          <div className="text-sm font-medium">{s.output_tokens.toLocaleString()}</div>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {data.by_source.every(s => s.input_tokens === 0 && s.output_tokens === 0) && (
                  <p className="text-white/20 text-sm text-center py-4">No token data available</p>
                )}
              </div>
            </div>
          </div>

          {/* Per-user costs */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Users size={18} className="text-orange-400" /> Top Users by Cost
            </h2>
            {data.per_user.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/5 text-white/30 text-xs">
                      <th className="text-left p-3">#</th>
                      <th className="text-left p-3">Student</th>
                      <th className="text-right p-3">Requests</th>
                      <th className="text-right p-3">Cost (₹)</th>
                      <th className="text-right p-3">Avg/Request</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.per_user.map((u, i) => (
                      <tr key={u.student_id} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                        <td className="p-3 text-white/20">{i + 1}</td>
                        <td className="p-3 text-white/70">{u.student_name}</td>
                        <td className="p-3 text-right text-white/40">{u.requests}</td>
                        <td className="p-3 text-right text-green-400 font-medium">₹{u.cost_inr.toFixed(2)}</td>
                        <td className="p-3 text-right text-white/30">₹{(u.cost_inr / u.requests).toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-white/20 text-sm text-center py-6">No user cost data for this period</p>
            )}
          </div>
        </>
      ) : (
        <div className="glass-card p-8 text-center text-white/30">
          <DollarSign size={48} className="mx-auto mb-4 opacity-20" />
          <p>No cost data available</p>
        </div>
      )}
    </div>
  );
}

function SummaryCard({ icon, label, value, sub, gradient }: {
  icon: React.ReactNode; label: string; value: string; sub?: string; gradient: string;
}) {
  return (
    <div className={`glass-card p-5 bg-gradient-to-br ${gradient}`}>
      <div className="flex items-center gap-2 mb-2 text-white/40">{icon}<span className="text-xs">{label}</span></div>
      <div className="text-xl font-bold">{value}</div>
      {sub && <div className="text-[10px] text-white/30 mt-1">{sub}</div>}
    </div>
  );
}
