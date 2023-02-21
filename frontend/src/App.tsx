import React from 'react'
import {useState} from 'react'
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
import LinearProgress from '@mui/material/LinearProgress'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'
import SchoolIcon from '@mui/icons-material/School'
import HelpIcon from '@mui/icons-material/Help'

const drawerWidth = 240

function ButtonAppBar() {
  const [open, setOpen] = useState<boolean>(true)
  return (
    <>
      <CssBaseline/>
      <AppBar position="fixed" sx={{zIndex: (theme) => theme.zIndex.drawer + 1}}>
        <Toolbar>
          <div onClick={() => setOpen(!open)}>
            <IconButton
              size="large"
              edge="start"
              color="inherit"
              aria-label="menu"
              sx={{mr: 2}}
            >
              <MenuIcon/>
            </IconButton>
          </div>
          <Typography variant="h6" component="div" sx={{flexGrow: 1}}>
                        MATL Online
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        variant='permanent'
        sx={{
          width: drawerWidth,
          flexShrink: 0
        }}
      >
        <Toolbar/>
        <Box sx={{overflow: 'auto', width: drawerWidth}}>
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
            <ListItem key={'Examples'} disablePadding>
              <ListItemButton>
                <ListItemIcon>
                  <SchoolIcon/>
                </ListItemIcon>
                <ListItemText primary={'Examples'}>
                                    Examples
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
            <ListItem key={'Help'} disablePadding>
              <ListItemButton>
                <ListItemIcon>
                  <HelpIcon/>
                </ListItemIcon>
                <ListItemText primary={'Help'}>
                                    Help
                </ListItemText>
              </ListItemButton>
            </ListItem>
          </List>
          <Divider/>
        </Box>
      </Drawer>
    </>
  )
}

interface InterpreterOutputProps {
    running: boolean;
    output: string[];
}

function InterpreterOutput(props: InterpreterOutputProps) {
  return (
    <>
      {props.running && <LinearProgress/>}
      <Box sx={{padding: 1}}>
        <pre>
          {props.output.join("\n")}

        </pre>
      </Box>
    </>
  )
}

function Interpreter() {
  const [code, setCode] = useState<string>("")
  const [running, setRunning] = useState<boolean>(false)
  const [output, setOutput] = useState<string[]>([])

  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <TextField
          id="code"
          label={`Code ${code.length ? `(${code.length} bytes)` : ''}`}
          multiline
          value={code}
          onChange={(el) => setCode(el.target.value)}
          maxRows={Infinity}
          variant="outlined"
          sx={{display: "flex"}}
          InputProps={{style: {fontFamily: "monospace"}}}
        />
      </Grid>
      <Grid item xs={12}>
        <TextField
          id="inputs"
          label="Input Arguments"
          variant="outlined"
          multiline
          maxRows={Infinity}
          sx={{display: "flex"}}
          InputProps={{style: {fontFamily: "monospace"}}}
        />
      </Grid>
      <Grid item xs={12}>
        <Button
          variant='contained'
          sx={{marginRight: 2}}
          onClick={() => {
            setRunning(!running)

            if (!running) {
              setOutput([])
              setTimeout(() => {
                setOutput(["OUTPUT"])
                setRunning(false)
              }, 1000)
            }
          }}
          startIcon={running ? <StopIcon/> : <PlayArrowIcon/>}
        >
          {
            running ? "Cancel" : "Run"
          }
        </Button>
        <Button variant='outlined' startIcon={<ShareIcon/>}>Share</Button>
      </Grid>
      <Grid item xs={12}>
        <InterpreterOutput running={running} output={output}/>
      </Grid>
    </Grid>
  )
}

function App() {
  return (
    <Box sx={{display: 'flex'}}>
      <ButtonAppBar/>
      <Box component="main" sx={{flexGrow: 1, p: 3}}>
        <Toolbar/>
        <Interpreter/>
      </Box>
    </Box>
  )
}

export default App
