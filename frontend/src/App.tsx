import React from 'react'
import {useState, useEffect } from 'react'
import io from 'socket.io-client'
import AppBar from '@mui/material/AppBar'
import Card from '@mui/material/Card'
import Paper from '@mui/material/Paper'
import Box from '@mui/material/Box'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import IconButton from '@mui/material/IconButton'
import MenuIcon from '@mui/icons-material/Menu'
import TextField from '@mui/material/TextField'
import Drawer from '@mui/material/Drawer'
import List from '@mui/material/List'
import Stack from '@mui/material/Stack'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Divider from '@mui/material/Divider'
import CssBaseline from '@mui/material/CssBaseline'
import FormControl from '@mui/material/FormControl'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import InputLabel from '@mui/material/InputLabel'
import CodeIcon from '@mui/icons-material/Code'
import MenuBookIcon from '@mui/icons-material/MenuBook'
import BarChartIcon from '@mui/icons-material/BarChart'
import Grid from '@mui/material/Grid'
import Button from '@mui/material/Button'
import HistoryIcon from '@mui/icons-material/History'
import ShareIcon from '@mui/icons-material/Share'
import CircularProgress from '@mui/material/CircularProgress'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'
import SchoolIcon from '@mui/icons-material/School'
import HelpIcon from '@mui/icons-material/Help'

const drawerWidth = 240
const socket = io("http://localhost:5000")

const navigationOptions = [
  {
    label: "Interpreter",
    icon: <CodeIcon/>
  },
  {
    label: "Documentation",
    icon: <MenuBookIcon/>
  },
  {
    label: "Examples",
    icon: <SchoolIcon/>,
  },
  {
    label: "History",
    icon: <HistoryIcon/>
  },
  {
    label: "Analytics",
    icon: <BarChartIcon/>
  },
  {
    label: "Help",
    icon: <HelpIcon/>
  }

]

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
            {
              navigationOptions.map((option) => {
                return (
                  <ListItem key={option.label} disablePadding>
                    <ListItemButton>
                      <ListItemIcon>
                        {option.icon}
                      </ListItemIcon>
                      <ListItemText primary={option.label}>
                        {option.label}
                      </ListItemText>
                    </ListItemButton>
                  </ListItem>
                )
              })

            }
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
    <Paper variant="outlined" sx={{p: 2, whiteSpace: "pre", fontFamily:" monospace", fontSize: 14, overflow: "auto", flexGrow: 1, m: 1}}>
      {props.output.join("\n")}
    </Paper>
  )
}

function Interpreter() {
  const versions = [
    "22.7.4",
    "1.2.3",
    "4.5.6",
  ]

  const [isConnected, setIsConnected] = useState<boolean>(socket.connected)
  const [lastPong, setLastPong] = useState<null|string>(null)
  const [code, setCode] = useState<string>("12:")
  const [running, setRunning] = useState<boolean>(false)
  const [output, setOutput] = useState<string[]>([])
  const [version, setVersion] = useState<string>(versions[0])
  const [session, setSession] = useState<string|null>(null)

  useEffect(() => {
    socket.on('connect', () => {
      setIsConnected(true)
    })

    socket.on('disconnect', () => {
      setIsConnected(false)
    })

    socket.on('pong', () => {
      setLastPong(new Date().toISOString())
    })

    socket.on('complete', () => {
      setRunning(false)
    })

    socket.on('connection', (data) => setSession(data.session_id))

    socket.on('status', (data) => {
      setOutput(data.data.map((o: any) => o.value))
    })
  })

  const onRun = async (code: string, inputs: string, version: string, uuid: string) => {
    await socket.emitWithAck('submit', {
      code,
      inputs,
      version,
      uid: uuid
    })
  }

  return (
    <Box sx={{flexGrow: 1, display: "flex", flexDirection: "column"}}>
      <Grid container spacing={2} sx={{flexGrow: 0, display: "flex"}}>
        <Grid item xs={10}>
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
        <Grid item xs={2}>
          <FormControl fullWidth>
            <InputLabel id="demo-simple-select-label">Version</InputLabel>
            <Select
              labelId="demo-simple-select-label"
              id="demo-simple-select"
              label="Version"
              onChange={(el) => setVersion(el.target.value)}
              value={version}
            >
              {
                versions.map((version) => {
                  return (
                    <MenuItem value={version}>{version}</MenuItem>
                  )
                })

              }
            </Select>
          </FormControl>
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
          <Stack direction="row" spacing={1}>
            <Button
              variant='contained'
              sx={{ minWidth: 120}}
              disabled={!isConnected}
              onClick={() => {
                setRunning(!running)

                if (!running && session) {
                  setOutput([])
                  onRun(code, "", version, session)
                }
              }}
              startIcon={running ? <CircularProgress size={14} color="inherit"/> : <PlayArrowIcon/>}
            >
              {
                running ? "Cancel" : "Run"
              }
            </Button>
            <Button variant='outlined' startIcon={<ShareIcon/>}>Share</Button>
          </Stack>
        </Grid>
      </Grid>
      <InterpreterOutput running={running} output={output}/>
    </Box>
  )
}

function App() {
  return (
    <Box sx={{display: 'flex'}}>
      <ButtonAppBar/>
      <Box component="main" sx={{p: 2, display: "flex", flexDirection: "column", height: "100vh", flexGrow: 1 }}>
        <Toolbar/>
        <Interpreter/>
      </Box>
    </Box>
  )
}

export default App
