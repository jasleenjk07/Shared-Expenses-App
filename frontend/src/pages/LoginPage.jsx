import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api';

export default function LoginPage() {
  const [email, setEmail] = useState('demo@flatmates.app');
  const [password, setPassword] = useState('demo1234');
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      const data = isRegister
        ? await api.register(email, password, name)
        : await api.login(email, password);
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate('/');
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card card">
        <h2 style={{ marginBottom: '0.5rem' }}>{isRegister ? 'Create account' : 'Sign in'}</h2>
        <p style={{ color: 'var(--muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          Shared Expenses — split bills fairly
        </p>
        <form onSubmit={handleSubmit}>
          {isRegister && (
            <div className="form-group">
              <label>Name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
          )}
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }}>
            {isRegister ? 'Register' : 'Login'}
          </button>
        </form>
        <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--muted)', textAlign: 'center' }}>
          {isRegister ? 'Already have an account?' : 'No account?'}{' '}
          <a href="#" onClick={(e) => { e.preventDefault(); setIsRegister(!isRegister); }}>
            {isRegister ? 'Sign in' : 'Register'}
          </a>
        </p>
        {!isRegister && (
          <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--muted)', textAlign: 'center' }}>
            Demo: demo@flatmates.app / demo1234
          </p>
        )}
      </div>
    </div>
  );
}
