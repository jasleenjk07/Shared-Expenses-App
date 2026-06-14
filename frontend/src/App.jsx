import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import GroupPage from './pages/GroupPage';
import LoginPage from './pages/LoginPage';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
}

function Navbar() {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  if (!user) return null;

  return (
    <nav className="navbar">
      <a href="/"><h1>Shared Expenses</h1></a>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <span style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>{user.name}</span>
        <button
          className="btn btn-secondary"
          style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
          onClick={() => { localStorage.clear(); window.location.href = '/login'; }}
        >
          Logout
        </button>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
        <Route path="/groups/:id" element={<PrivateRoute><GroupPage /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}
