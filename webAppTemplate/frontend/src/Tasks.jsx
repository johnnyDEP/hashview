import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Box, Typography, Paper, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import DeleteIcon from '@mui/icons-material/Delete';
import DialogContentText from '@mui/material/DialogContentText';

function authHeader() {
  const token = localStorage.getItem('jwt');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editOpen, setEditOpen] = useState(false);
  const [editTaskId, setEditTaskId] = useState(null);
  const [editTask, setEditTask] = useState(null);
  const [wordlists, setWordlists] = useState([]);
  const [rules, setRules] = useState([]);
  const [taskGroups, setTaskGroups] = useState([]);
  const [groupMembership, setGroupMembership] = useState([]);
  const [editForm, setEditForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});
  const [successOpen, setSuccessOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteTaskId, setDeleteTaskId] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    axios.get('/api/tasks', { headers: authHeader() })
      .then(res => setTasks(res.data))
      .catch(() => setError('Failed to load tasks'))
      .finally(() => setLoading(false));
  }, []);

  const validateForm = (form) => {
    const errors = {};
    const mode = String(form.hc_attackmode);
    if (!form.name) errors.name = 'Name is required';
    if (mode === '0') {
      if (!form.wl_id) errors.wl_id = 'Wordlist is required';
    } else if (mode === '1') {
      if (!form.wl_id) errors.wl_id = 'Wordlist 1 is required';
      if (!form.wl_id_2) errors.wl_id_2 = 'Wordlist 2 is required';
    } else if (mode === '3') {
      if (!form.hc_mask) errors.hc_mask = 'Mask is required';
    } else if (mode === '6' || mode === '7') {
      if (!form.wl_id) errors.wl_id = 'Wordlist is required';
      if (!form.hc_mask) errors.hc_mask = 'Mask is required';
    } else {
      errors.hc_attackmode = 'Unsupported attack mode';
    }
    return errors;
  };

  const handleEdit = (taskId) => {
    setEditTaskId(taskId);
    setEditOpen(true);
    setValidationErrors({});
    setSaveError(null);
    // Fetch all needed data in parallel
    Promise.all([
      axios.get(`/api/tasks/${taskId}`, { headers: authHeader() }),
      axios.get('/api/wordlists', { headers: authHeader() }),
      axios.get('/api/rules', { headers: authHeader() }),
      axios.get('/api/task-groups', { headers: authHeader() })
    ]).then(([taskRes, wlRes, ruleRes, groupRes]) => {
      setEditTask(taskRes.data);
      setEditForm(taskRes.data); // initialize editable form state
      setWordlists(wlRes.data);
      setRules(ruleRes.data);
      setTaskGroups(groupRes.data);
      // Find which groups this task is a member of
      const memberOf = groupRes.data.filter(g => (g.tasks || []).includes(taskId)).map(g => g.id);
      setGroupMembership(memberOf);
    }).catch(() => {
      setError('Failed to load edit data');
      setEditTask(null);
    });
  };

  const handleClose = () => {
    setEditOpen(false);
    setEditTaskId(null);
    setEditTask(null);
    setEditForm(null);
    setWordlists([]);
    setRules([]);
    setTaskGroups([]);
    setGroupMembership([]);
    setValidationErrors({});
    setSaveError(null);
  };

  const handleFormChange = (field, value) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  };

  const handleGroupToggle = (groupId) => {
    setGroupMembership(prev =>
      prev.includes(groupId)
        ? prev.filter(id => id !== groupId)
        : [...prev, groupId]
    );
  };

  const handleSave = async () => {
    const errors = validateForm(editForm);
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;
    setSaving(true);
    setSaveError(null);
    try {
      // Update the task
      await axios.put(`/api/tasks/${editTaskId}`, editForm, { headers: authHeader() });
      // Update group membership
      // For each group, if membership changed, update it
      for (const group of taskGroups) {
        const wasMember = (group.tasks || []).includes(editTaskId);
        const isMember = groupMembership.includes(group.id);
        if (wasMember !== isMember) {
          // Update this group
          let newTasks = group.tasks ? [...group.tasks] : [];
          if (isMember && !wasMember) {
            newTasks.push(editTaskId);
          } else if (!isMember && wasMember) {
            newTasks = newTasks.filter(tid => tid !== editTaskId);
          }
          await axios.put(`/api/task-groups/${group.id}`, { tasks: newTasks }, { headers: authHeader() });
        }
      }
      // Refresh tasks list
      const res = await axios.get('/api/tasks', { headers: authHeader() });
      setTasks(res.data);
      setSuccessOpen(true);
      handleClose();
    } catch (err) {
      setSaveError('Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  const handleSuccessClose = () => setSuccessOpen(false);

  const handleDeleteClick = (taskId) => {
    setDeleteTaskId(taskId);
    setDeleteDialogOpen(true);
    setDeleteError(null);
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setDeleteTaskId(null);
    setDeleteError(null);
  };

  const handleDeleteConfirm = async () => {
    setDeleting(true);
    setDeleteError(null);
    try {
      await axios.delete(`/api/tasks/${deleteTaskId}`, { headers: authHeader() });
      const res = await axios.get('/api/tasks', { headers: authHeader() });
      setTasks(res.data);
      setSuccessOpen(true);
      setDeleteDialogOpen(false);
      setDeleteTaskId(null);
    } catch (err) {
      setDeleteError(err.response?.data?.detail || 'Failed to delete task');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) return <Box sx={{ p: 3 }}><CircularProgress /></Box>;
  if (error) return <Box sx={{ p: 3 }}><Alert severity="error">{error}</Alert></Box>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Tasks</Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Attack Mode</TableCell>
              <TableCell>Owner</TableCell>
              <TableCell>Wordlist 1</TableCell>
              <TableCell>Wordlist 2</TableCell>
              <TableCell>J Rule</TableCell>
              <TableCell>K Rule</TableCell>
              <TableCell>Rule ID</TableCell>
              <TableCell>Mask</TableCell>
              <TableCell>Control</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map(task => (
              <TableRow key={task.id}>
                <TableCell>{task.id}</TableCell>
                <TableCell>{task.name}</TableCell>
                <TableCell>{task.hc_attackmode}</TableCell>
                <TableCell>{task.owner_id}</TableCell>
                <TableCell>{task.wl_id}</TableCell>
                <TableCell>{task.wl_id_2}</TableCell>
                <TableCell>{task.j_rule}</TableCell>
                <TableCell>{task.k_rule}</TableCell>
                <TableCell>{task.rule_id}</TableCell>
                <TableCell>{task.hc_mask}</TableCell>
                <TableCell>
                  <button onClick={() => handleEdit(task.id)}>Edit</button>
                  <button onClick={() => handleDeleteClick(task.id)} disabled={deleting} style={{marginLeft:8}} title="Delete Task">
                    <DeleteIcon fontSize="small" />
                  </button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Dialog open={editOpen} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>Edit Task</DialogTitle>
        <DialogContent>
          {editForm ? (
            <>
              <TextField
                label="Name"
                value={editForm.name}
                onChange={e => handleFormChange('name', e.target.value)}
                fullWidth
                margin="normal"
                error={!!validationErrors.name}
                helperText={validationErrors.name}
              />
              <FormControl fullWidth margin="normal" error={!!validationErrors.hc_attackmode}>
                <InputLabel>Attack Mode</InputLabel>
                <Select
                  value={editForm.hc_attackmode}
                  onChange={e => handleFormChange('hc_attackmode', e.target.value)}
                >
                  <MenuItem value="0">Straight (Wordlist + Rules)</MenuItem>
                  <MenuItem value="1">Combinator</MenuItem>
                  <MenuItem value="3">Mask</MenuItem>
                  <MenuItem value="6">Hybrid (Wordlist + Mask)</MenuItem>
                  <MenuItem value="7">Hybrid (Mask + Wordlist)</MenuItem>
                </Select>
                {validationErrors.hc_attackmode && <div style={{color:'red',fontSize:12}}>{validationErrors.hc_attackmode}</div>}
              </FormControl>
              <FormControl fullWidth margin="normal" error={!!validationErrors.wl_id}>
                <InputLabel>Wordlist 1</InputLabel>
                <Select
                  value={editForm.wl_id || ''}
                  onChange={e => handleFormChange('wl_id', e.target.value)}
                >
                  {wordlists.map(wl => (
                    <MenuItem key={wl.id} value={wl.id}>{wl.name}</MenuItem>
                  ))}
                </Select>
                {validationErrors.wl_id && <div style={{color:'red',fontSize:12}}>{validationErrors.wl_id}</div>}
              </FormControl>
              <FormControl fullWidth margin="normal" error={!!validationErrors.wl_id_2}>
                <InputLabel>Wordlist 2</InputLabel>
                <Select
                  value={editForm.wl_id_2 || ''}
                  onChange={e => handleFormChange('wl_id_2', e.target.value)}
                >
                  {wordlists.map(wl => (
                    <MenuItem key={wl.id} value={wl.id}>{wl.name}</MenuItem>
                  ))}
                </Select>
                {validationErrors.wl_id_2 && <div style={{color:'red',fontSize:12}}>{validationErrors.wl_id_2}</div>}
              </FormControl>
              <FormControl fullWidth margin="normal">
                <InputLabel>Rule</InputLabel>
                <Select
                  value={editForm.rule_id || ''}
                  onChange={e => handleFormChange('rule_id', e.target.value)}
                >
                  {rules.map(rule => (
                    <MenuItem key={rule.id} value={rule.id}>{rule.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                label="J Rule"
                value={editForm.j_rule || ''}
                onChange={e => handleFormChange('j_rule', e.target.value)}
                fullWidth
                margin="normal"
              />
              <TextField
                label="K Rule"
                value={editForm.k_rule || ''}
                onChange={e => handleFormChange('k_rule', e.target.value)}
                fullWidth
                margin="normal"
              />
              <TextField
                label="Mask"
                value={editForm.hc_mask || ''}
                onChange={e => handleFormChange('hc_mask', e.target.value)}
                fullWidth
                margin="normal"
                error={!!validationErrors.hc_mask}
                helperText={validationErrors.hc_mask}
              />
              <div style={{ marginTop: 16 }}>
                <div>Task Groups:</div>
                {taskGroups.map(group => (
                  <FormControlLabel
                    key={group.id}
                    control={<Checkbox checked={groupMembership.includes(group.id)} onChange={() => handleGroupToggle(group.id)} />}
                    label={group.name}
                  />
                ))}
              </div>
            </>
          ) : (
            <CircularProgress />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={saving}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" color="primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</Button>
        </DialogActions>
        {saveError && <Alert severity="error">{saveError}</Alert>}
      </Dialog>
      <Dialog open={deleteDialogOpen} onClose={handleDeleteCancel}>
        <DialogTitle>Delete Task</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this task? This action cannot be undone.
          </DialogContentText>
          {deleteError && <Alert severity="error">{deleteError}</Alert>}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={deleting}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained" disabled={deleting}>
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={successOpen} autoHideDuration={3000} onClose={handleSuccessClose} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={handleSuccessClose} severity="success" sx={{ width: '100%' }}>
          Task updated successfully!
        </Alert>
      </Snackbar>
    </Box>
  );
} 