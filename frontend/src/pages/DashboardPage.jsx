import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

export default function DashboardPage() {
  const [groups, setGroups] = useState([]);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    api.getGroups().then(setGroups).finally(() => setLoading(false));
  }, []);

  async function createGroup(e) {
    e.preventDefault();
    if (!name.trim()) return;
    const g = await api.createGroup({ name });
    setGroups([...groups, g]);
    setName('');
  }

  return (
    <div className="container">
      <h2 style={{ marginBottom: '0.25rem' }}>Hello, {user.name}</h2>
      <p style={{ color: 'var(--muted)', marginBottom: '1.5rem' }}>Your expense groups</p>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Create group</h3>
        <form onSubmit={createGroup} style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            placeholder="Group name (e.g. Flat 4B)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={{ flex: 1 }}
          />
          <button type="submit" className="btn btn-primary">Create</button>
        </form>
      </div>

      {loading ? (
        <p className="empty">Loading...</p>
      ) : groups.length === 0 ? (
        <p className="empty">No groups yet. Create one and import the CSV.</p>
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {groups.map((g) => (
            <Link key={g.id} to={`/groups/${g.id}`} className="card" style={{ display: 'block' }}>
              <strong>{g.name}</strong>
              <p style={{ color: 'var(--muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                {g.members?.length || 0} members
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
