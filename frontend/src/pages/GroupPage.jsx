import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api, formatINR } from '../api';
import BalancesTab from './BalancesTab';
import ExpensesTab from './ExpensesTab';
import ImportTab from './ImportTab';

export default function GroupPage() {
  const { id } = useParams();
  const groupId = parseInt(id);
  const [group, setGroup] = useState(null);
  const [tab, setTab] = useState('balances');

  useEffect(() => {
    api.getGroup(groupId).then(setGroup);
  }, [groupId]);

  if (!group) return <div className="container"><p className="empty">Loading...</p></div>;

  return (
    <div className="container">
      <h2>{group.name}</h2>
      <p style={{ color: 'var(--muted)', marginBottom: '1rem', fontSize: '0.9rem' }}>
        Members: {group.members?.map((m) => m.user_name).join(', ')}
      </p>

      <div className="tabs">
        {['balances', 'expenses', 'import', 'members'].map((t) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'balances' && <BalancesTab groupId={groupId} />}
      {tab === 'expenses' && <ExpensesTab groupId={groupId} />}
      {tab === 'import' && <ImportTab groupId={groupId} />}
      {tab === 'members' && (
        <div className="card">
          <table>
            <thead>
              <tr><th>Name</th><th>Joined</th><th>Left</th></tr>
            </thead>
            <tbody>
              {group.members?.map((m) => (
                <tr key={m.id}>
                  <td>{m.user_name}</td>
                  <td>{m.joined_at}</td>
                  <td>{m.left_at || 'Active'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
