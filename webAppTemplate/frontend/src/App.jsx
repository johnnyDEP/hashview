import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { CssBaseline, Box, Drawer, List, ListItem, ListItemIcon, ListItemText, Toolbar, AppBar, Typography, IconButton, Menu, MenuItem } from '@mui/material';
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
import DashboardFull from './templates/DashboardFull';
import Files from './Files';
import Register from './Register';
import { useState } from 'react';
import Tasks from './Tasks';

const drawerWidth = 240;

const pages = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Jobs', icon: <AssessmentIcon />, path: '/jobs' },
  { text: 'Tasks', icon: <RuleIcon />, path: '/tasks' },
  { text: 'Task Groups', icon: <RuleIcon />, path: '/task-groups' },
  { text: 'Hashfiles', icon: <InsertDriveFileIcon />, path: '/hashfiles' },
  { text: 'Rules', icon: <RuleIcon />, path: '/rules' },
  { text: 'Wordlists', icon: <InsertDriveFileIcon />, path: '/wordlists' },
  { text: 'Analytics', icon: <AssessmentIcon />, path: '/analytics' },
  { text: 'Search', icon: <SearchIcon />, path: '/search' },
  { text: 'Notifications', icon: <AssessmentIcon />, path: '/notifications' },
  { text: 'Wrapped', icon: <AssessmentIcon />, path: '/wrapped' },
  // Optionally, add admin/account sections as needed
];

function Sidebar({ darkMode, setDarkMode }) {
  const location = useLocation();
  const { logout, isAuthenticated, user } = useAuth();
  // TODO: Replace with real admin check from user info
  const isAdmin = true; // <-- Replace with real check

  // Dropdown state
  const [tasksAnchorEl, setTasksAnchorEl] = useState(null);
  const [adminAnchorEl, setAdminAnchorEl] = useState(null);
  const [accountAnchorEl, setAccountAnchorEl] = useState(null);

  const handleDropdownOpen = (setter) => (event) => setter(event.currentTarget);
  const handleDropdownClose = (setter) => () => setter(null);

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
          <span style={{ color: '#e94560' }}>●</span> Hashview
        </Typography>
      </Toolbar>
      <List>
        <ListItem button component={Link} to="/" selected={location.pathname === '/'}>
          <ListItemIcon sx={{ color: '#fff' }}><DashboardIcon /></ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>
        <ListItem button component={Link} to="/jobs" selected={location.pathname === '/jobs'}>
          <ListItemIcon sx={{ color: '#fff' }}><AssessmentIcon /></ListItemIcon>
          <ListItemText primary="Jobs" />
        </ListItem>
        {/* Tasks Dropdown */}
        <ListItem button onClick={handleDropdownOpen(setTasksAnchorEl)}>
          <ListItemIcon sx={{ color: '#fff' }}><RuleIcon /></ListItemIcon>
          <ListItemText primary="Tasks" />
        </ListItem>
        <Menu anchorEl={tasksAnchorEl} open={Boolean(tasksAnchorEl)} onClose={handleDropdownClose(setTasksAnchorEl)}>
          <MenuItem component={Link} to="/tasks" onClick={handleDropdownClose(setTasksAnchorEl)}>Tasks</MenuItem>
          <MenuItem component={Link} to="/task-groups" onClick={handleDropdownClose(setTasksAnchorEl)}>Task Groups</MenuItem>
        </Menu>
        <ListItem button component={Link} to="/hashfiles" selected={location.pathname === '/hashfiles'}>
          <ListItemIcon sx={{ color: '#fff' }}><InsertDriveFileIcon /></ListItemIcon>
          <ListItemText primary="Hashfiles" />
        </ListItem>
        <ListItem button component={Link} to="/rules" selected={location.pathname === '/rules'}>
          <ListItemIcon sx={{ color: '#fff' }}><RuleIcon /></ListItemIcon>
          <ListItemText primary="Rules" />
        </ListItem>
        <ListItem button component={Link} to="/wordlists" selected={location.pathname === '/wordlists'}>
          <ListItemIcon sx={{ color: '#fff' }}><InsertDriveFileIcon /></ListItemIcon>
          <ListItemText primary="Wordlists" />
        </ListItem>
        <ListItem button component={Link} to="/analytics" selected={location.pathname === '/analytics'}>
          <ListItemIcon sx={{ color: '#fff' }}><AssessmentIcon /></ListItemIcon>
          <ListItemText primary="Analytics" />
        </ListItem>
        <ListItem button component={Link} to="/search" selected={location.pathname === '/search'}>
          <ListItemIcon sx={{ color: '#fff' }}><SearchIcon /></ListItemIcon>
          <ListItemText primary="Search" />
        </ListItem>
        <ListItem button component={Link} to="/notifications" selected={location.pathname === '/notifications'}>
          <ListItemIcon sx={{ color: '#fff' }}><AssessmentIcon /></ListItemIcon>
          <ListItemText primary="Notifications" />
        </ListItem>
        <ListItem button component={Link} to="/wrapped" selected={location.pathname === '/wrapped'}>
          <ListItemIcon sx={{ color: '#fff' }}><AssessmentIcon /></ListItemIcon>
          <ListItemText primary="Wrapped" />
        </ListItem>
        {/* Admin Dropdown */}
        {isAdmin && (
          <>
            <ListItem button onClick={handleDropdownOpen(setAdminAnchorEl)}>
              <ListItemIcon sx={{ color: '#fff' }}><SettingsIcon /></ListItemIcon>
              <ListItemText primary="Admin" />
            </ListItem>
            <Menu anchorEl={adminAnchorEl} open={Boolean(adminAnchorEl)} onClose={handleDropdownClose(setAdminAnchorEl)}>
              <MenuItem component={Link} to="/customers" onClick={handleDropdownClose(setAdminAnchorEl)}>Customers</MenuItem>
              <MenuItem component={Link} to="/agents" onClick={handleDropdownClose(setAdminAnchorEl)}>Agents</MenuItem>
              <MenuItem component={Link} to="/settings" onClick={handleDropdownClose(setAdminAnchorEl)}>Settings</MenuItem>
              <MenuItem component={Link} to="/users" onClick={handleDropdownClose(setAdminAnchorEl)}>User Accounts</MenuItem>
            </Menu>
          </>
        )}
        {/* Account Dropdown */}
        {isAuthenticated && (
          <>
            <ListItem button onClick={handleDropdownOpen(setAccountAnchorEl)}>
              <ListItemIcon sx={{ color: '#fff' }}><LogoutIcon /></ListItemIcon>
              <ListItemText primary="Account" />
            </ListItem>
            <Menu anchorEl={accountAnchorEl} open={Boolean(accountAnchorEl)} onClose={handleDropdownClose(setAccountAnchorEl)}>
              <MenuItem component={Link} to="/profile" onClick={handleDropdownClose(setAccountAnchorEl)}>Profile</MenuItem>
              <MenuItem onClick={() => { logout(); handleDropdownClose(setAccountAnchorEl)(); }}>Logout</MenuItem>
            </Menu>
          </>
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
      <Route path="/register" element={<Register />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Routes>
              <Route path="/" element={<DashboardFull />} />
              <Route path="/jobs" element={<Placeholder title="Jobs" />} />
              <Route path="/tasks" element={<Tasks />} />
              <Route path="/task-groups" element={<Placeholder title="Task Groups" />} />
              <Route path="/hashfiles" element={<Placeholder title="Hashfiles" />} />
              <Route path="/rules" element={<Placeholder title="Rules" />} />
              <Route path="/wordlists" element={<Placeholder title="Wordlists" />} />
              <Route path="/analytics" element={<Placeholder title="Analytics" />} />
              <Route path="/search" element={<Placeholder title="Search" />} />
              <Route path="/notifications" element={<Placeholder title="Notifications" />} />
              <Route path="/wrapped" element={<Placeholder title="Wrapped" />} />
              {/* Add admin/account routes as needed */}
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
                    Hashview Dashboard
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