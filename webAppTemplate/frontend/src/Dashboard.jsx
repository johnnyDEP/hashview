import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Box, Typography, Paper, Grid, CircularProgress, Alert, List, ListItem, ListItemText } from '@mui/material';
import AssessmentIcon from '@mui/icons-material/Assessment';
import StorageIcon from '@mui/icons-material/Storage';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

export default function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [system, setSystem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [analyticsRes, systemRes] = await Promise.all([
          axios.get('/api/analytics', { headers: authHeader() }),
          axios.get('/api/system_status', { headers: authHeader() })
        ]);
        setAnalytics(analyticsRes.data);
        setSystem(systemRes.data);
      } catch (err) {
        setError('Failed to load dashboard data');
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  function authHeader() {
    const token = localStorage.getItem('jwt');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  if (loading) return <Box sx={{ p: 3 }}><CircularProgress /></Box>;
  if (error) return <Box sx={{ p: 3 }}><Alert severity="error">{error}</Alert></Box>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
            <AssessmentIcon color="primary" sx={{ mr: 2 }} />
            <Box>
              <Typography variant="h6">Total Files</Typography>
              <Typography>{analytics.total_files}</Typography>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
            <CheckCircleIcon color="success" sx={{ mr: 2 }} />
            <Box>
              <Typography variant="h6">Processed</Typography>
              <Typography>{analytics.processed}</Typography>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
            <StorageIcon color="warning" sx={{ mr: 2 }} />
            <Box>
              <Typography variant="h6">Pending</Typography>
              <Typography>{analytics.pending}</Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>System Status</Typography>
        <Paper sx={{ p: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>Status: <b>{system.status}</b> (as of {new Date(system.timestamp).toLocaleString()})</Typography>
          <List>
            {system.services.map((svc) => (
              <ListItem key={svc.name}>
                <ListItemText primary={svc.name} secondary={svc.status} />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Box>
    </Box>
  );
} 