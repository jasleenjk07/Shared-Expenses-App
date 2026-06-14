import React, { useEffect, useState } from 'react';
import { api, formatINR } from '../api';

export default function ExpensesTab({ groupId }) {
  const [expenses, setExpenses] = useState([]);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    api.getExpenses(groupId).then(setExpenses);
  }, [groupId]);

  if (!expenses.length) return <p className="empty">No expenses yet. Import the CSV to get started.</p>;

  return (
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Description</th>
          <th>Paid by</th>
          <th>Amount</th>
          <th>Split</th>
        </tr>
      </thead>
      <tbody>
        {expenses.map((e) => (
          <React.Fragment key={e.id}>
            <tr style={{ cursor: 'pointer' }} onClick={() => setExpanded(expanded === e.id ? null : e.id)}>
              <td>{e.expense_date}</td>
              <td>{e.description}</td>
              <td>{e.paid_by_name || '—'}</td>
              <td>
                {e.currency !== 'INR'
                  ? `${e.amount} ${e.currency} (${formatINR(e.amount_inr)})`
                  : formatINR(e.amount_inr)}
              </td>
              <td><span className="badge badge-info">{e.split_type}</span></td>
            </tr>
            {expanded === e.id && (
              <tr key={`${e.id}-detail`}>
                <td colSpan={5} style={{ background: 'var(--surface2)' }}>
                  {e.notes && <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>{e.notes}</p>}
                  <table>
                    <thead><tr><th>Member</th><th>Share (₹)</th></tr></thead>
                    <tbody>
                      {e.splits?.map((s) => (
                        <tr key={s.id}>
                          <td>{s.user_name}</td>
                          <td>{formatINR(s.allocated_amount_inr)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </td>
              </tr>
            )}
          </React.Fragment>
        ))}
      </tbody>
    </table>
  );
}
