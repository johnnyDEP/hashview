import React, { useState } from 'react';
import { useAuth } from './AuthContext';
import { Box, Button, TextField, Typography, Paper, CircularProgress, Alert, Link } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const { login, loading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Pass remember to login if your backend supports it
    const ok = await login(email, password, remember);
    setSuccess(ok);
    if (ok) {
      navigate('/');
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default' }}>
      <Paper elevation={3} sx={{ p: 4, minWidth: 320 }}>
        <Typography variant="h5" gutterBottom align="center">Hashview Login</Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            fullWidth
            margin="normal"
            autoFocus
            required
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            fullWidth
            margin="normal"
            required
          />
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
            <input
              type="checkbox"
              id="remember"
              checked={remember}
              onChange={e => setRemember(e.target.checked)}
              style={{ marginRight: 8 }}
            />
            <label htmlFor="remember" style={{ fontSize: 14 }}>Remember me</label>
          </Box>
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mt: 2 }}>Login successful!</Alert>}
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            sx={{ mt: 2 }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Login'}
          </Button>
        </form>
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="body2">
            <Link href="/reset-request">Forgot Password?</Link>
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            Don't have an account?{' '}
            <Link href="/register">Register</Link>
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
} 