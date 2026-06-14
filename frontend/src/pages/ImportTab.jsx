import { useState } from 'react';
import { api } from '../api';

export default function ImportTab({ groupId }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleImport(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const result = await api.importCsv(groupId, file);
      setReport(result.report);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  }

  return (
    <div>
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '0.75rem' }}>Import CSV</h3>
        <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Upload <code>Expenses_Export.csv</code> exactly as provided. The importer detects anomalies
          and applies documented policies — nothing is silently guessed.
        </p>
        <input type="file" accept=".csv" onChange={handleImport} disabled={loading} />
        {loading && <p style={{ marginTop: '0.5rem', color: 'var(--muted)' }}>Importing...</p>}
        {error && <p className="error">{error}</p>}
      </div>

      {report && (
        <div className="card">
          <h3>Import Report</h3>
          <div style={{ display: 'flex', gap: '1.5rem', margin: '1rem 0', flexWrap: 'wrap' }}>
            <div><strong>{report.imported_expenses}</strong> <span style={{ color: 'var(--muted)' }}>expenses</span></div>
            <div><strong>{report.imported_settlements}</strong> <span style={{ color: 'var(--muted)' }}>settlements</span></div>
            <div><strong>{report.skipped_rows}</strong> <span style={{ color: 'var(--muted)' }}>skipped</span></div>
            <div><strong>{report.total_anomalies}</strong> <span style={{ color: 'var(--muted)' }}>anomalies</span></div>
            {report.pending_approval_count > 0 && (
              <div><span className="badge badge-warning">{report.pending_approval_count} need approval</span></div>
            )}
          </div>

          <table>
            <thead>
              <tr>
                <th>Row</th>
                <th>Type</th>
                <th>Description</th>
                <th>Action taken</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {report.anomalies.map((a, i) => (
                <tr key={i} className="anomaly-row">
                  <td>{a.row_number}</td>
                  <td className="anomaly-type">{a.anomaly_type}</td>
                  <td>{a.description}</td>
                  <td>{a.action_taken || a.suggested_action}</td>
                  <td>
                    {a.requires_approval ? (
                      <span className="badge badge-warning">pending</span>
                    ) : (
                      <span className="badge badge-success">resolved</span>
                    )}
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
