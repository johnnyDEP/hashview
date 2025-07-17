import React, { useState } from 'react';
import { Box, Button, TextField, Typography, Paper, CircularProgress, Alert, Link } from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_URL = '/api'; // Adjust if not using proxy

export default function Register() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await axios.post(`${API_URL}/register`, {
        first_name: firstName,
        last_name: lastName,
        email_address: email,
        password: password
      });
      setSuccess(true);
      setLoading(false);
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default' }}>
      <Paper elevation={3} sx={{ p: 4, minWidth: 320 }}>
        <Typography variant="h5" gutterBottom align="center">Register for Nemesis</Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            label="First Name"
            value={firstName}
            onChange={e => setFirstName(e.target.value)}
            fullWidth
            margin="normal"
            required
          />
          <TextField
            label="Last Name"
            value={lastName}
            onChange={e => setLastName(e.target.value)}
            fullWidth
            margin="normal"
            required
          />
          <TextField
            label="Email Address"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            fullWidth
            margin="normal"
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
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mt: 2 }}>Registration successful! Redirecting to login...</Alert>}
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            sx={{ mt: 2 }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Register'}
          </Button>
        </form>
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="body2">
            Already have an account?{' '}
            <Link href="/login">Login</Link>
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
} 