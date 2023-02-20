import React from 'react';
import logo from './logo.svg';
import './App.css';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import TextField from '@mui/material/TextField';


function ButtonAppBar() {
  return (
    <Box sx={{ flexGrow: 1}}>
    <AppBar position="static">
            <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            MATL Online
          </Typography>
          <Button color="inherit">Login</Button>
        </Toolbar>
    </AppBar>
    </Box>
  )
}

function InputControl() {
  return (
  <Box
  component="form"
  autoComplete="off"
  >
      <TextField id="outlined-basic" label="Code" variant="outlined" />

  </Box>
  )

  }

function App() {
  return (
    <div className="App">
    <ButtonAppBar/>
    <InputControl/>
    </div>
  );
}

export default App;
