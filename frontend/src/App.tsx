import React from 'react'
import { useState } from 'react'
import AppBar from '@mui/material/AppBar'
import Box from '@mui/material/Box'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import IconButton from '@mui/material/IconButton'
import MenuIcon from '@mui/icons-material/Menu'
import TextField from '@mui/material/TextField'
import Drawer from '@mui/material/Drawer'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Divider from '@mui/material/Divider'
import CssBaseline from '@mui/material/CssBaseline'
import CodeIcon from '@mui/icons-material/Code'
import MenuBookIcon from '@mui/icons-material/MenuBook'
import BarChartIcon from '@mui/icons-material/BarChart'
import Grid from '@mui/material/Grid'
import Button from '@mui/material/Button'
import HistoryIcon from '@mui/icons-material/History'
import ShareIcon from '@mui/icons-material/Share'
import CircularProgress from '@mui/material/CircularProgress'

const drawerWidth = 240

function ButtonAppBar() {
  return (
    <>
      <CssBaseline/>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1}}>
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{mr: 2}}
          >
            <MenuIcon/>
          </IconButton>
          <Typography variant="h6" component="div" sx={{flexGrow: 1}}>
            MATL Online
          </Typography>
          <TextField variant="outlined" placeholder="Search"> </TextField>
        </Toolbar>
      </AppBar>
      <Drawer
        open={false}
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0
        }}
      >
        <Toolbar/>
        <Box sx={{ overflow: 'auto', width: drawerWidth }}>
          <List>
            <ListItem key={'Interpreter'} disablePadding>
              <ListItemButton>
                <ListItemIcon>
                  <CodeIcon/>
                </ListItemIcon>
                <ListItemText primary={'Interpreter'}>
                  Interpreter
                </ListItemText>
              </ListItemButton>
            </ListItem>
            <ListItem key={'Documentation'} disablePadding>
              <ListItemButton>
                <ListItemIcon>
                  <MenuBookIcon/>
                </ListItemIcon>
                <ListItemText primary={'Documentation'}>
                  Documentation
                </ListItemText>
              </ListItemButton>
            </ListItem>
            <ListItem key={'History'} disablePadding>
              <ListItemButton>
                <ListItemIcon>
                  <HistoryIcon/>
                </ListItemIcon>
                <ListItemText primary={'History'}>
                  History
                </ListItemText>
              </ListItemButton>
            </ListItem>
            <ListItem key={'Analytics'} disablePadding>
              <ListItemButton>
                <ListItemIcon>
                  <BarChartIcon/>
                </ListItemIcon>
                <ListItemText primary={'Analytics'}>
                  Analytics
                </ListItemText>
              </ListItemButton>
            </ListItem>
          </List>
          <Divider />
        </Box>
      </Drawer>
    </>
  )
}

function InterpreterOutput () {
  return (
    <Box sx={{border: '1px solid #000'}}>
      <pre>HELLO WORLD</pre>
    </Box>
  )
}

function App() {
  const [code, setCode] = useState<string>("10".repeat(1000))
  const [running, setRunning] = useState<boolean>(true)

  // <div style={{ textAlign: "right", display: "block" }}>({code.length} characters)</div>-->
  return (
    <Box sx={{display: 'flex'}}>
      <ButtonAppBar/>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              id="code"
              label={`Code ${code.length ? `(${code.length} bytes)` : ''}`}
              multiline
              value={code}
              onChange={(el) => setCode(el.target.value) }
              maxRows={Infinity}
              variant="outlined"
              sx={{ display: "flex"}}
              InputProps={{style: { fontFamily: "monospace"}}}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              id="inputs"
              label="Input Arguments"
              variant="outlined"
              multiline
              maxRows={Infinity}
              sx={{ display: "flex" }}
              InputProps={{style: { fontFamily: "monospace"}}}
            />
          </Grid>
          <Grid item xs={12}>
            <Button variant='contained' sx={{marginRight:2}} onClick={() => setRunning(!running) }>
              {
                running ?
                  <div>Run
                    <CircularProgress sx={{marginLeft: 2}} size={15} color="inherit"/>
                  </div>
                  : <div>Run</div>
              }
            </Button>
            <Button variant='outlined' startIcon={<ShareIcon/>}>Share</Button>
          </Grid>
          <Grid item xs={12}>
            <InterpreterOutput/>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}

export default App
