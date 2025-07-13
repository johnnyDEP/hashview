import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Box, Typography, Paper, CircularProgress, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

export default function Files() {
  const [files, setFiles] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFiles = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get('/api/files', { headers: authHeader() });
        setFiles(res.data);
      } catch (err) {
        setError('Failed to load files');
      }
      setLoading(false);
    };
    fetchFiles();
  }, []);

  function authHeader() {
    const token = localStorage.getItem('jwt');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  if (loading) return <Box sx={{ p: 3 }}><CircularProgress /></Box>;
  if (error) return <Box sx={{ p: 3 }}><Alert severity="error">{error}</Alert></Box>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Files</Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><InsertDriveFileIcon sx={{ verticalAlign: 'middle' }} /> Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Uploaded</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {files.map((file) => (
              <TableRow key={file.id}>
                <TableCell>{file.name}</TableCell>
                <TableCell>{file.status}</TableCell>
                <TableCell>{file.uploaded}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
} 