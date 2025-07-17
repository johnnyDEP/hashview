import React from 'react';
import { AppBar, Toolbar, Typography, Box, Button, Menu, MenuItem, Container, Alert } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Layout({ children, title = 'Hashview', flashMessages = [] }) {
  const { isAuthenticated, user } = useAuth();
  const isAdmin = user?.admin;
  const [tasksAnchorEl, setTasksAnchorEl] = React.useState(null);
  const [adminAnchorEl, setAdminAnchorEl] = React.useState(null);
  const [accountAnchorEl, setAccountAnchorEl] = React.useState(null);
  const location = useLocation();

  const handleDropdownOpen = (setter) => (event) => setter(event.currentTarget);
  const handleDropdownClose = (setter) => () => setter(null);

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="fixed" color="primary">
        <Toolbar>
          <Typography variant="h6" component={Link} to="/" sx={{ color: '#fff', textDecoration: 'none', flexGrow: 1 }}>
            {title}
          </Typography>
          {isAuthenticated && (
            <>
              <Button color="inherit" component={Link} to="/">Dashboard</Button>
              <Button color="inherit" component={Link} to="/jobs">Jobs</Button>
              <Button color="inherit" onClick={handleDropdownOpen(setTasksAnchorEl)}>Tasks</Button>
              <Menu anchorEl={tasksAnchorEl} open={Boolean(tasksAnchorEl)} onClose={handleDropdownClose(setTasksAnchorEl)}>
                <MenuItem component={Link} to="/tasks" onClick={handleDropdownClose(setTasksAnchorEl)}>Tasks</MenuItem>
                <MenuItem component={Link} to="/task-groups" onClick={handleDropdownClose(setTasksAnchorEl)}>Task Groups</MenuItem>
              </Menu>
              <Button color="inherit" component={Link} to="/hashfiles">Hashfiles</Button>
              <Button color="inherit" component={Link} to="/rules">Rules</Button>
              <Button color="inherit" component={Link} to="/wordlists">Wordlists</Button>
              <Button color="inherit" component={Link} to="/analytics">Analytics</Button>
              <Button color="inherit" component={Link} to="/search">Search</Button>
              <Button color="inherit" component={Link} to="/notifications">Notifications</Button>
              <Button color="inherit" component={Link} to="/wrapped">Wrapped</Button>
              {isAdmin && (
                <>
                  <Button color="inherit" onClick={handleDropdownOpen(setAdminAnchorEl)}>Admin</Button>
                  <Menu anchorEl={adminAnchorEl} open={Boolean(adminAnchorEl)} onClose={handleDropdownClose(setAdminAnchorEl)}>
                    <MenuItem component={Link} to="/customers" onClick={handleDropdownClose(setAdminAnchorEl)}>Customers</MenuItem>
                    <MenuItem component={Link} to="/agents" onClick={handleDropdownClose(setAdminAnchorEl)}>Agents</MenuItem>
                    <MenuItem component={Link} to="/settings" onClick={handleDropdownClose(setAdminAnchorEl)}>Settings</MenuItem>
                    <MenuItem component={Link} to="/users" onClick={handleDropdownClose(setAdminAnchorEl)}>User Accounts</MenuItem>
                  </Menu>
                </>
              )}
              <Button color="inherit" onClick={handleDropdownOpen(setAccountAnchorEl)}>Account</Button>
              <Menu anchorEl={accountAnchorEl} open={Boolean(accountAnchorEl)} onClose={handleDropdownClose(setAccountAnchorEl)}>
                <MenuItem component={Link} to="/profile" onClick={handleDropdownClose(setAccountAnchorEl)}>Profile</MenuItem>
                <MenuItem component={Link} to="/logout" onClick={handleDropdownClose(setAccountAnchorEl)}>Logout</MenuItem>
              </Menu>
            </>
          )}
        </Toolbar>
      </AppBar>
      <Toolbar /> {/* Spacer for fixed AppBar */}
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        {/* Flash messages */}
        {flashMessages.map((msg, idx) => (
          <Alert key={idx} severity={msg.category || 'info'} sx={{ mb: 2 }}>{msg.message}</Alert>
        ))}
        {/* Main content */}
        {children}
      </Container>
    </Box>
  );
} 