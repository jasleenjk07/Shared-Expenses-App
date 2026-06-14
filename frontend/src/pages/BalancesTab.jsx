import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api, formatINR } from '../api';

export default function BalancesTab({ groupId }) {
  const [data, setData] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [breakdown, setBreakdown] = useState(null);

  useEffect(() => {
    api.getBalances(groupId).then(setData);
  }, [groupId]);

  async function showBreakdown(userId) {
    setSelectedUser(userId);
    const b = await api.getMemberBreakdown(groupId, userId);
    setBreakdown(b);
  }

  if (!data) return <p className="empty">Loading balances...</p>;

  return (
    <div>
      <h3 style={{ marginBottom: '1rem' }}>Who pays whom</h3>
      {data.simplified_debts.length === 0 ? (
        <p className="empty">All settled up!</p>
      ) : (
        data.simplified_debts.map((d, i) => (
          <div key={i} className="debt-card">
            <span>
              <strong>{d.from_user_name}</strong> pays <strong>{d.to_user_name}</strong>
            </span>
            <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>{formatINR(d.amount_inr)}</span>
          </div>
        ))
      )}

      <h3 style={{ margin: '2rem 0 1rem' }}>Individual balances</h3>
      <table>
        <thead>
          <tr>
            <th>Member</th>
            <th>Balance</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data.member_balances.map((m) => (
            <tr key={m.user_id}>
              <td>{m.user_name}</td>
              <td className={m.balance_inr >= 0 ? 'positive' : 'negative'}>
                {formatINR(m.balance_inr)}
              </td>
              <td>
                <button className="btn btn-secondary" style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem' }}
                  onClick={() => showBreakdown(m.user_id)}>
                  Details
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {breakdown && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <h4>{breakdown.user_name}'s expense breakdown</h4>
          <p style={{ color: 'var(--muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            Total balance: {formatINR(breakdown.total_balance_inr)}
          </p>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Paid</th>
                <th>Share</th>
                <th>Net</th>
              </tr>
            </thead>
            <tbody>
              {breakdown.lines.map((line, i) => (
                <tr key={i}>
                  <td>{line.date}</td>
                  <td>{line.description}</td>
                  <td>{line.paid_inr ? formatINR(line.paid_inr) : '—'}</td>
                  <td>{line.share_inr ? formatINR(line.share_inr) : '—'}</td>
                  <td className={line.net_inr >= 0 ? 'positive' : 'negative'}>
                    {formatINR(line.net_inr)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
