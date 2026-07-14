/**
 * UserManagementPage — admin user search, filter, edit, toggle active.
 */
import { useState, useEffect } from 'react';
import { Users, Search, UserCheck, UserX, Edit2, X } from 'lucide-react';
import apiClient from '../../api/client';

interface UserItem {
  id: string; phone: string; email: string | null; full_name: string;
  role: string; is_active: boolean; created_at: string | null;
}

export function UserManagementPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [editingUser, setEditingUser] = useState<UserItem | null>(null);

  useEffect(() => { loadUsers(); }, [roleFilter]);

  async function loadUsers(q?: string) {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (roleFilter) params.set('role', roleFilter);
      if (q || search) params.set('search', q || search);
      const { data } = await apiClient.get(`/admin/users?${params}`);
      setUsers(data.users || []);
      setTotal(data.total || 0);
    } catch { setUsers([]); } finally { setLoading(false); }
  }

  async function toggleActive(userId: string) {
    try {
      await apiClient.post(`/admin/users/${userId}/toggle`);
      loadUsers();
    } catch { /* error */ }
  }

  async function saveUser(userId: string, updates: Record<string, string>) {
    try {
      await apiClient.put(`/admin/users/${userId}`, updates);
      setEditingUser(null);
      loadUsers();
    } catch { /* error */ }
  }

  const ROLES = [
    { value: '', label: 'All' }, { value: 'student', label: 'Student' },
    { value: 'teacher', label: 'Teacher' }, { value: 'parent', label: 'Parent' },
    { value: 'admin', label: 'Admin' },
  ];

  return (
    <div className="p-8 animate-fade-in" id="user-management">
      <div className="mb-8">
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <Users size={24} className="text-green-400" /> User Management
        </h1>
        <p className="text-white/40 mt-1 text-sm">Search, edit, and manage user accounts ({total} total)</p>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && loadUsers(search)}
            placeholder="Search name or phone..."
            className="input-field pl-10 w-full text-sm" />
        </div>
        <div className="flex gap-1">
          {ROLES.map(r => (
            <button key={r.value} onClick={() => setRoleFilter(r.value)}
              className={`px-3 py-2 rounded-lg text-xs transition-all ${
                roleFilter === r.value ? 'bg-brand-500/20 text-brand-300' : 'text-white/40 hover:bg-white/5'
              }`}>{r.label}</button>
          ))}
        </div>
      </div>

      {/* User table */}
      {loading ? (
        <div className="space-y-2">
          {[1,2,3,4,5].map(i => <div key={i} className="glass-card p-4 animate-pulse"><div className="h-5 bg-white/5 rounded w-1/3" /></div>)}
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5 text-white/30 text-xs">
                  <th className="text-left p-3">Name</th>
                  <th className="text-left p-3">Phone</th>
                  <th className="text-left p-3">Role</th>
                  <th className="text-left p-3">Status</th>
                  <th className="text-right p-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="p-3 text-white/70">{u.full_name}</td>
                    <td className="p-3 text-white/40">{u.phone}</td>
                    <td className="p-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        u.role === 'student' ? 'bg-blue-500/20 text-blue-300' :
                        u.role === 'teacher' ? 'bg-purple-500/20 text-purple-300' :
                        u.role === 'parent' ? 'bg-green-500/20 text-green-300' :
                        'bg-orange-500/20 text-orange-300'
                      }`}>{u.role}</span>
                    </td>
                    <td className="p-3">
                      <span className={`text-xs ${u.is_active ? 'text-emerald-400' : 'text-red-400'}`}>
                        {u.is_active ? '● Active' : '● Inactive'}
                      </span>
                    </td>
                    <td className="p-3 text-right space-x-2">
                      <button onClick={() => setEditingUser(u)}
                        className="p-1.5 rounded-lg hover:bg-white/5 text-white/30 hover:text-white transition-all">
                        <Edit2 size={14} />
                      </button>
                      <button onClick={() => toggleActive(u.id)}
                        className="p-1.5 rounded-lg hover:bg-white/5 text-white/30 hover:text-white transition-all"
                        title={u.is_active ? 'Deactivate' : 'Activate'}>
                        {u.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Edit modal */}
      {editingUser && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setEditingUser(null)}>
          <div className="glass-card p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between mb-4">
              <h3 className="font-semibold">Edit User</h3>
              <button onClick={() => setEditingUser(null)} className="text-white/30 hover:text-white"><X size={18} /></button>
            </div>
            <EditUserForm user={editingUser} onSave={saveUser} />
          </div>
        </div>
      )}
    </div>
  );
}

function EditUserForm({ user, onSave }: { user: UserItem; onSave: (id: string, u: Record<string, string>) => void }) {
  const [name, setName] = useState(user.full_name);
  const [phone, setPhone] = useState(user.phone);
  const [email, setEmail] = useState(user.email || '');

  return (
    <div className="space-y-3">
      <div>
        <label className="text-xs text-white/30 block mb-1">Full Name</label>
        <input value={name} onChange={e => setName(e.target.value)} className="input-field w-full text-sm" />
      </div>
      <div>
        <label className="text-xs text-white/30 block mb-1">Phone</label>
        <input value={phone} onChange={e => setPhone(e.target.value)} className="input-field w-full text-sm" />
      </div>
      <div>
        <label className="text-xs text-white/30 block mb-1">Email</label>
        <input value={email} onChange={e => setEmail(e.target.value)} className="input-field w-full text-sm" />
      </div>
      <button onClick={() => onSave(user.id, { full_name: name, phone, email })}
        className="btn-primary w-full text-sm">Save Changes</button>
    </div>
  );
}
