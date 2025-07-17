import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Box, Typography, Grid, Card, CardHeader, CardContent, Button, LinearProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Alert, Accordion, AccordionSummary, AccordionDetails, CircularProgress } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Line } from 'react-chartjs-2';
import Chart from 'chart.js/auto';

function authHeader() {
  const token = localStorage.getItem('jwt');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export default function DashboardFull() {
  const [agents, setAgents] = useState([]);
  const [runningJobs, setRunningJobs] = useState([]);
  const [queuedJobs, setQueuedJobs] = useState([]);
  const [chartLabels, setChartLabels] = useState([]);
  const [chartValues, setChartValues] = useState([]);
  const [users, setUsers] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      axios.get('/api/agents', { headers: authHeader() }),
      axios.get('/api/jobs?status=running', { headers: authHeader() }),
      axios.get('/api/jobs?status=queued', { headers: authHeader() }),
      axios.get('/api/analytics', { headers: authHeader() }),
      axios.get('/api/users', { headers: authHeader() }),
      axios.get('/api/customers', { headers: authHeader() }),
    ])
      .then(([
        agentsRes,
        runningJobsRes,
        queuedJobsRes,
        analyticsRes,
        usersRes,
        customersRes,
      ]) => {
        setAgents(agentsRes.data || []);
        setRunningJobs(runningJobsRes.data || []);
        setQueuedJobs(queuedJobsRes.data || []);
        setChartLabels(analyticsRes.data.labels || []);
        setChartValues(analyticsRes.data.values || []);
        setUsers(usersRes.data || []);
        setCustomers(customersRes.data || []);
      })
      .catch((err) => {
        setError('Failed to load dashboard data');
      })
      .finally(() => setLoading(false));
  }, []);

  const chartData = {
    labels: chartLabels,
    datasets: [
      {
        label: 'Passwords Recovered',
        data: chartValues,
        fill: false,
        borderColor: '#1976d2',
        tension: 0.1,
      },
    ],
  };

  if (loading) return <Box sx={{ p: 3 }}><CircularProgress /></Box>;
  if (error) return <Box sx={{ p: 3 }}><Alert severity="error">{error}</Alert></Box>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      {/* Agent Status */}
      <Grid container spacing={2}>
        {agents.length === 0 ? (
          <Grid item xs={12}>
            <Alert severity="info">
              No Agents configured. Please <Button variant="outlined" size="small" href="/agents">add a new agent</Button>.
            </Alert>
          </Grid>
        ) : (
          agents.map(agent => (
            <Grid item xs={12} sm={6} md={4} key={agent.id}>
              <Card sx={{ bgcolor: agent.status === 'Online' ? 'background.paper' : 'error.main', color: agent.status === 'Online' ? 'text.primary' : '#fff' }}>
                <CardHeader title={agent.name} subheader={`Last Seen: ${agent.last_checkin}`} />
                <CardContent>
                  <Typography variant="body2">Status: {agent.status}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>
      {/* Passwords Recovered Chart */}
      <Box sx={{ mt: 4 }}>
        <Card>
          <CardHeader title="Passwords Recovered" />
          <CardContent>
            <Box sx={{ height: 300 }}>
              <Line data={chartData} options={{ responsive: true, maintainAspectRatio: false }} />
            </Box>
          </CardContent>
        </Card>
      </Box>
      {/* Jobs Section */}
      <Box sx={{ mt: 4 }}>
        {runningJobs.length === 0 && queuedJobs.length === 0 ? (
          <Card>
            <CardHeader title="No Configured Jobs" />
            <CardContent>
              <Button variant="contained" color="success" href="/jobs/add">Create a New Job</Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Running Jobs */}
            {runningJobs.length > 0 && (
              <Card sx={{ mb: 2 }}>
                <CardHeader title="Running Jobs" />
                <CardContent>
                  {runningJobs.map(job => {
                    const percentCompleted = (job.tasks.filter(t => t.status === 'Completed').length / job.tasks.length) * 100;
                    const percentRunning = (job.tasks.filter(t => t.status === 'Running').length / job.tasks.length) * 100;
                    return (
                      <Accordion key={job.id} defaultExpanded sx={{ mb: 2 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography sx={{ flexGrow: 1 }}>{job.name} (Owner: {users.find(u => u.id === job.owner_id)?.first_name || '-'})</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Box sx={{ mb: 2 }}>
                            <LinearProgress variant="determinate" value={percentCompleted + percentRunning} sx={{ height: 10, mb: 1 }} />
                            <Typography variant="caption">Completed: {percentCompleted.toFixed(0)}% | In Progress: {percentRunning.toFixed(0)}%</Typography>
                          </Box>
                          <TableContainer component={Paper}>
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  <TableCell>Task Name</TableCell>
                                  <TableCell>Status</TableCell>
                                  <TableCell>Agent</TableCell>
                                  <TableCell>Recovered</TableCell>
                                  <TableCell>Rate</TableCell>
                                  <TableCell>EST Completion</TableCell>
                                  <TableCell>Control</TableCell>
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {job.tasks.map(task => (
                                  <TableRow key={task.id}>
                                    <TableCell>{task.name}</TableCell>
                                    <TableCell>{task.status}</TableCell>
                                    <TableCell>{agents.find(a => a.id === task.agent_id)?.name || '-'}</TableCell>
                                    <TableCell align="center">{task.recovered}</TableCell>
                                    <TableCell>{task.rate}</TableCell>
                                    <TableCell>{task.est}</TableCell>
                                    <TableCell>{task.control ? <Button size="small" variant="outlined" color="secondary">Stop</Button> : ''}</TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </TableContainer>
                        </AccordionDetails>
                      </Accordion>
                    );
                  })}
                </CardContent>
              </Card>
            )}
            {/* Queued Jobs */}
            {queuedJobs.length > 0 && (
              <Card>
                <CardHeader title="Queued Jobs" />
                <CardContent>
                  {queuedJobs.map(job => (
                    <Accordion key={job.id} sx={{ mb: 2 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography sx={{ flexGrow: 1 }}>{job.name} (Owner: {users.find(u => u.id === job.owner_id)?.first_name || '-'})</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <TableContainer component={Paper}>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Task Name</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Agent</TableCell>
                                <TableCell>Recovered</TableCell>
                                <TableCell>Rate</TableCell>
                                <TableCell>EST Completion</TableCell>
                                <TableCell>Control</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {job.tasks.map(task => (
                                <TableRow key={task.id}>
                                  <TableCell>{task.name}</TableCell>
                                  <TableCell>{task.status}</TableCell>
                                  <TableCell>{agents.find(a => a.id === task.agent_id)?.name || '-'}</TableCell>
                                  <TableCell align="center">{task.recovered}</TableCell>
                                  <TableCell>{task.rate}</TableCell>
                                  <TableCell>{task.est}</TableCell>
                                  <TableCell>{task.control ? <Button size="small" variant="outlined" color="secondary">Stop</Button> : ''}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </CardContent>
              </Card>
            )}
          </>
        )}
      </Box>
      {/* Add more sections as needed */}
    </Box>
  );
} 