import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { CssBaseline, Box, Drawer, List, ListItem, ListItemIcon, ListItemText, Toolbar, AppBar, Typography, IconButton } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SearchIcon from '@mui/icons-material/Search';
import RuleIcon from '@mui/icons-material/Rule';
import AssessmentIcon from '@mui/icons-material/Assessment';
import SettingsIcon from '@mui/icons-material/Settings';
import HelpIcon from '@mui/icons-material/Help';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import LogoutIcon from '@mui/icons-material/Logout';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { AuthProvider, useAuth } from './AuthContext';
import Login from './Login';
import Dashboard from './Dashboard';
import Files from './Files';

const drawerWidth = 240;

const pages = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Files', icon: <InsertDriveFileIcon />, path: '/files' },
  { text: 'File Upload', icon: <CloudUploadIcon />, path: '/upload' },
  { text: 'Findings', icon: <AssessmentIcon />, path: '/findings' },
  { text: 'Document Search', icon: <SearchIcon />, path: '/search' },
  { text: 'Yara Rules', icon: <RuleIcon />, path: '/yara' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  { text: 'Help', icon: <HelpIcon />, path: '/help' },
];

function Sidebar({ darkMode, setDarkMode }) {
  const location = useLocation();
  const { logout, isAuthenticated } = useAuth();
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box', background: '#181c24', color: '#fff' },
      }}
    >
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold', letterSpacing: 2 }}>
          <span style={{ color: '#e94560' }}>●</span> NEMESIS
        </Typography>
      </Toolbar>
      <List>
        {pages.map((page) => (
          <ListItem button key={page.text} component={Link} to={page.path} selected={location.pathname === page.path}>
            <ListItemIcon sx={{ color: '#fff' }}>{page.icon}</ListItemIcon>
            <ListItemText primary={page.text} />
          </ListItem>
        ))}
        {isAuthenticated && (
          <ListItem button onClick={logout}>
            <ListItemIcon sx={{ color: '#fff' }}><LogoutIcon /></ListItemIcon>
            <ListItemText primary="Logout" />
          </ListItem>
        )}
      </List>
      <Box sx={{ flexGrow: 1 }} />
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <IconButton onClick={() => setDarkMode((m) => !m)} color="inherit">
          {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
        </IconButton>
        <Typography variant="body2" sx={{ ml: 1 }}>
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </Typography>
      </Box>
    </Drawer>
  );
}

function Placeholder({ title }) {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>{title}</Typography>
      <Typography variant="body1">This is a placeholder for the {title} page.</Typography>
    </Box>
  );
}

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/files" element={<Files />} />
              <Route path="/upload" element={<Placeholder title="File Upload" />} />
              <Route path="/findings" element={<Placeholder title="Findings" />} />
              <Route path="/search" element={<Placeholder title="Document Search" />} />
              <Route path="/yara" element={<Placeholder title="Yara Rules" />} />
              <Route path="/settings" element={<Placeholder title="Settings" />} />
              <Route path="/help" element={<Placeholder title="Help" />} />
            </Routes>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  const [darkMode, setDarkMode] = React.useState(true);
  const theme = React.useMemo(() => createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      background: {
        default: darkMode ? '#23272f' : '#f4f6fa',
        paper: darkMode ? '#181c24' : '#fff',
      },
      primary: {
        main: '#e94560',
      },
    },
    typography: {
      fontFamily: 'Inter, Roboto, Arial, sans-serif',
    },
  }), [darkMode]);

  const { isAuthenticated } = useAuth();

  return (
    <ThemeProvider theme={theme}>
      <Router>
        <Box sx={{ display: 'flex' }}>
          <CssBaseline />
          {isAuthenticated && <Sidebar darkMode={darkMode} setDarkMode={setDarkMode} />}
          <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default', minHeight: '100vh' }}>
            {isAuthenticated && (
              <AppBar position="static" color="transparent" elevation={0} sx={{ ml: `${drawerWidth}px`, bgcolor: 'background.default' }}>
                <Toolbar>
                  <Typography variant="h5" sx={{ flexGrow: 1, color: theme.palette.text.primary }}>
                    Nemesis Dashboard
                  </Typography>
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                    Last updated: {new Date().toLocaleTimeString()}
                  </Typography>
                </Toolbar>
              </AppBar>
            )}
            <AppRoutes />
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App; 