import React from 'react'
import {useState, useEffect } from 'react'
import io from 'socket.io-client'
import AppBar from '@mui/material/AppBar'
import Alert from '@mui/material/Alert'
import Paper from '@mui/material/Paper'
import Box from '@mui/material/Box'
import Switch from '@mui/material/Switch'
import FormGroup from '@mui/material/FormGroup'
import FormControlLabel from '@mui/material/FormControlLabel'
import Toolbar from '@mui/material/Toolbar'
import Tooltip from '@mui/material/Tooltip'
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
import SchoolIcon from '@mui/icons-material/School'
import HelpIcon from '@mui/icons-material/Help'
import ContentPasteIcon from '@mui/icons-material/ContentPaste'
import TroubleshootIcon from '@mui/icons-material/Troubleshoot'
import SearchIcon from '@mui/icons-material/Search'
import ClearIcon from '@mui/icons-material/Clear'
import MUIDataTable from "mui-datatables"

interface SearchBarProps {
  value: string
  onChange: (newValue: string) => void
}

function SearchBar(props: SearchBarProps) {

  const icon = props.value.length == 0 ? <SearchIcon/> : (
    <IconButton onClick={() => props.onChange("")}><ClearIcon/></IconButton>
  )

  return (
    <Stack direction="column" sx={{ p: 1}}>
      <TextField
        value={props.value}
        onChange={(el) => {
          const value = el.target.value
          props.onChange(value)
        }}
        InputProps={{ endAdornment: icon}}
      />
    </Stack>
  )
}

interface DocumentationTableProps {
  version: string
}

interface documentation {
  source: string,
  description: string,
}

function DocumentationTable(props: DocumentationTableProps) {
  const [value, setValue] = useState<string>("")
  const [data, setData] = useState<string[][]>([])
  const [loading, setLoading] = useState<boolean>(false)
  
  const columns = ["Source", "Description"]

  const fetchData = async (version: string) => {
    if (loading || data.length > 0) {
      return
    }

    setLoading(true)
    const response = await fetch(`http://localhost:5000/help/${version}`)
    const json = await response.json()
    setData(json.data)

    const newData = json.data.map((element: documentation) => [element.source, element.description])
    setData(newData)
    setLoading(false)

  }

  fetchData(props.version)

  return (
    <Box>
      <SearchBar value={value} onChange={setValue}/>

      <MUIDataTable
        title={"Employee List"}
        data={data}
        columns={columns}
        options={{
          download: false,
          print: false,
          viewColumns: false,
          filter: false,
          pagination: false,
          searchAlwaysOpen: true,
          selectableRows: undefined,
          searchProps: {
            style: { float: "right" }
          }
        }}
      />

    </Box>
  )
}

const drawerWidth = 240
const socket = io("http://localhost:5000")

interface Version {
  label: string
  releaseDate: Date
}

const navigationOptions = [
  {
    label: "Interpreter",
    icon: <CodeIcon/>,
    selected: true
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
        variant='persistent'
        open={true}
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
                  <ListItem key={option.label} disablePadding selected={option.selected == true}>
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
        </Box>
      </Drawer>
    </>
  )
}

interface InterpreterOutputProps {
    running: boolean;
    output: string[];
    errors: string[];
}

function InterpreterOutput(props: InterpreterOutputProps) {

  return (
    <Paper variant="outlined" sx={{p: 2, whiteSpace: "pre", fontFamily:" monospace", fontSize: 14, overflow: "auto", flexGrow: 1, marginTop: 2, marginLeft: 0}} >
      {props.output.join("\n")}
      { props.errors.length > 0 &&
      <Alert severity="error">
        { props.errors.join("\n")}
      </Alert>
      }
    </Paper>
  )
}

interface VersionSelectProps {
  onChange: (value: string) => void;
  value: string;
  versions: Version[];
}

function VersionSelect(props: VersionSelectProps) {
  return (
    <FormControl fullWidth>
      <InputLabel id="version">Version</InputLabel>
      <Select
        labelId="version"
        id="version"
        label="Version"
        onChange={(el) => props.onChange(el.target.value)}
        value={props.value}
      >
        {
          props.versions.map((version) => {
            return (
              <MenuItem value={version.label}>{version.label}</MenuItem>
            )
          })

        }
      </Select>
    </FormControl>
  )
}

interface StatusMessage {
  type: string;
  value: string;
}

function ExplainIconButton() {
  return (
    <Tooltip title="Explain the code">
      <IconButton size="small" sx={{m: -1}}>
        <TroubleshootIcon/>
      </IconButton>
    </Tooltip>
  )
}

function PasteIconButton () {
  return (
    <Tooltip title="Paste formatted input">
      <IconButton size="small" sx={{m: -1}}>
        <ContentPasteIcon/>
      </IconButton>
    </Tooltip>
  )
}

function Interpreter() {
  const versions = [
    { "label": "22.7.4", "releaseDate": new Date()},
    { "label": "22.7.3", "releaseDate": new Date()}
  ]

  const [isConnected, setIsConnected] = useState<boolean>(socket.connected)
  const [code, setCode] = useState<string>(":")
  const [running, setRunning] = useState<boolean>(false)
  const [output, setOutput] = useState<string[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [version, setVersion] = useState<string>(versions[0].label)
  const [session, setSession] = useState<string|null>(null)
  const [inputs, setInputs] = useState<string>("12")
  const [showDocumentation, setShowDocumentation] = useState<boolean>(false)

  useEffect(() => {
    socket.on('connect', () => {
      setIsConnected(true)
    })

    socket.on('disconnect', () => {
      setIsConnected(false)
    })

    socket.on('complete', () => {
      setRunning(false)
    })

    socket.on('connection', (data) => setSession(data.session_id))

    socket.on('status', (data) => {
      const messages = data.data as StatusMessage[]
      const errors = []
      const outputs = []

      for (const message of messages) {
        if (message.type == "stderr") {
          errors.push(message.value)
        } else if (message.type == "stdout") {
          outputs.push(message.value)
        }
      }

      setOutput(outputs)
      setErrors(errors)
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
      <Stack direction="row">
        <Typography variant="h5" component="div" sx={{flexGrow: 0, marginBottom: 3}}>
          MATL Interpreter
        </Typography>
        <Box sx={{ flexGrow: 1 }}></Box>
        <Box sx={{ flexGrow: 0}}>
          <FormControlLabel
            sx={{ marginRight: 0 }}
            labelPlacement="start"
            control={<Switch size="medium" checked={showDocumentation} onChange={(el) => setShowDocumentation(el.target.checked)}/>}
            label={<MenuBookIcon/>}
          />
        </Box>
      </Stack>
      <Grid container spacing={2} sx={{flexGrow: 0, display: "flex"}}>
        <Grid item xs={10}>
          <TextField
            id="code"
            label={`Code ${code.length ? `(${code.length} byte${code.length > 1 ? "s" : ""})` : ''}`}
            multiline
            autoFocus={true}
            value={code}
            onChange={(el) => setCode(el.target.value)}
            maxRows={Infinity}
            variant="outlined"
            sx={{display: "flex"}}
            InputProps={{style: {fontFamily: "monospace"}, endAdornment: <ExplainIconButton/>}}
          />
        </Grid>
        <Grid item xs={2}>
          <VersionSelect onChange={setVersion} value={version} versions={versions}/>
        </Grid>
        <Grid item xs={12}>
          <TextField
            id="inputs"
            label="Input Arguments"
            variant="outlined"
            multiline
            value={inputs}
            onChange={(el) => setInputs(el.target.value)}
            maxRows={Infinity}
            sx={{display: "flex"}}
            InputProps={{style: {fontFamily: "monospace"}, endAdornment: <PasteIconButton/>}}
          />
        </Grid>
        <Grid item xs={2}>
          <Stack direction="row" spacing={1}>
            <Button
              fullWidth
              variant='contained'
              disabled={!isConnected}
              onClick={async () => {
                setRunning(!running)

                if (!running && session) {
                  setOutput([])
                  setErrors([])
                  await onRun(code, inputs, version, session)
                }
              }}
              startIcon={running ? <CircularProgress size={14} color="inherit"/> : <PlayArrowIcon/>}
            >
              {
                running ? "Cancel" : "Run"
              }
            </Button>
            <Button variant='outlined' fullWidth startIcon={<ShareIcon/>}>Share</Button>
          </Stack>
        </Grid>
      </Grid>
      { showDocumentation && <DocumentationTable version={version}/>}
    </Box>
  )
}

// <InterpreterOutput running={running} output={output} errors={errors}/>
function App() {
  return (
    <Box sx={{display: 'flex'}}>
      <ButtonAppBar/>
      <Box component="main" sx={{p: 2, display: "flex", flexDirection: "column", height: "100vh", flexGrow: 1, width: 2 }}>
        <Toolbar/>
        <Interpreter/>
      </Box>
    </Box>
  )
}

export default App
