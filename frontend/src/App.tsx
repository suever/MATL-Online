import React from 'react'
import {useState, useEffect} from 'react'
import io from 'socket.io-client'
import AppBar from '@mui/material/AppBar'
import Alert from '@mui/material/Alert'
import Paper from '@mui/material/Paper'
import Box from '@mui/material/Box'
import Switch from '@mui/material/Switch'
import "./index.css"
import {createTheme, createMuiTheme, Theme, ThemeProvider} from '@mui/material/styles'
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
import ReactMarkdown from 'react-markdown'
import {useHotkeys} from 'react-hotkeys-hook'
import {ComponentsOverrides} from '@mui/material/styles/overrides'

interface SearchBarProps {
  value: string
  onChange: (newValue: string) => void
}

declare module '@mui/material/styles' {
    interface Components {
        MUIDataTable?: {
            styleOverrides?: ComponentsOverrides['MUIDataTable'];
        };
        
        MUIDataTableBody?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableBody'];
        };

        MUIDataTableBodyCell?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableBodyCell'];
        };

        MUIDataTableBodyRow?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableBodyRow'];
        };

        MUIDataTableFilter?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableFilter'];
        };

        MUIDataTableFilterList?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableFilterList'];
        };

        MUIDataTableFooter?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableFooter'];
        };

        MUIDataTableHead?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableHead'];
        };

        MUIDataTableHeadCell?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableHeadCell'];
        };

        MUIDataTableHeadRow?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableHeadRow'];
        };

        MUIDataTableJumpToPage?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableJumpToPage'];
        };

        MUIDataTablePagination?: {
            styleOverrides?: ComponentsOverrides['MUIDataTablePagination'];
        };

        MUIDataTableResize?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableResize'];
        };

        MUIDataTableSearch?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableSearch'];
        };

        MUIDataTableSelectCell?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableSelectCell'];
        };

        MUIDataTableToolbar?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableToolbar'];
        };

        MUIDataTableToolbarSelect?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableToolbarSelect'];
        };

        MUIDataTableViewCol?: {
            styleOverrides?: ComponentsOverrides['MUIDataTableViewCol'];
        };
    }
}

declare module '@mui/material/styles/overrides' {
    interface ComponentNameToClassKey {
        MUIDataTable: 'root' | 'caption' | 'responsiveBase' | 'liveAnnounce' | 'paper' | 'responsiveScroll' | 'tableRoot';

        MUIDataTableBody: 'root' | 'emptyTitle' | 'lastSimpleCell' | 'lastStackedCell';

        MUIDataTableBodyCell:
            | 'root'
            | 'cellHide'
            | 'cellStackedSmall'
            | 'responsiveStackedSmall'
            | 'responsiveStackedSmallParent'
            | 'simpleCell'
            | 'simpleHeader'
            | 'stackedCommon'
            | 'stackedCommonAlways'
            | 'stackedHeader'
            | 'stackedParent'
            | 'stackedParentAlways';

        MUIDataTableBodyRow: 'root' | 'hoverCursor' | 'responsiveSimple' | 'responsiveStacked';

        MUIDataTableFilter:
            | 'root'
            | 'checkbox'
            | 'checkboxFormControl'
            | 'checkboxFormControlLabel'
            | 'checkboxFormGroup'
            | 'checkboxIcon'
            | 'checkboxListTitle'
            | 'checked'
            | 'filtersSelected'
            | 'gridListTile'
            | 'header'
            | 'noMargin'
            | 'reset'
            | 'resetLink'
            | 'title';

        MUIDataTableFilterList: 'root' | 'chip';

        MUIDataTableFooter: 'root';

        MUIDataTableHead: 'main' | 'responsiveSimple' | 'responsiveStacked' | 'responsiveStackedAlways';

        MUIDataTableHeadCell:
            | 'root'
            | 'contentWrapper'
            | 'data'
            | 'dragCursor'
            | 'fixedHeader'
            | 'hintIconAlone'
            | 'hintIconWithSortIcon'
            | 'mypopper'
            | 'sortAction'
            | 'sortActive'
            | 'sortLabelRoot'
            | 'toolButton'
            | 'tooltip';

        MUIDataTableHeadRow: 'root';

        MUIDataTableJumpToPage: 'root' | 'caption' | 'input' | 'select' | 'selectIcon' | 'selectRoot';

        MUIDataTablePagination:
            | 'root'
            | '@media screen and (max-width: 400px)'
            | 'navContainer'
            | 'selectRoot'
            | 'tableCellContainer'
            | 'toolbar';

        MUIDataTableResize: 'root' | 'resizer';

        MUIDataTableSearch: 'clearIcon' | 'main' | 'searchIcon' | 'searchText';

        MUIDataTableSelectCell:
            | 'root'
            | 'checkboxRoot'
            | 'checked'
            | 'disabled'
            | 'expandDisabled'
            | 'expanded'
            | 'fixedHeader'
            | 'fixedLeft'
            | 'headerCell'
            | 'hide'
            | 'icon';

        MUIDataTableToolbar:
            | 'root'
            | '@media screen and (max-width: 480px)'
            | "[theme.breakpoints.down('sm')]"
            | "[theme.breakpoints.down('xs')]"
            | 'actions'
            | 'filterCloseIcon'
            | 'filterPaper'
            | 'fullWidthActions'
            | 'fullWidthLeft'
            | 'fullWidthRoot'
            | 'fullWidthTitleText'
            | 'icon'
            | 'iconActive'
            | 'left'
            | 'searchIcon'
            | 'titleRoot'
            | 'titleText';

        MUIDataTableToolbarSelect: 'root' | 'deleteIcon' | 'iconButton' | 'title';

        MUIDataTableViewCol:
            | 'root'
            | 'checkbox'
            | 'checkboxRoot'
            | 'checked'
            | 'formControl'
            | 'formGroup'
            | 'label'
            | 'title';
    }
}

/*
declare module '@mui/material/styles' {
  interface Components {
    MUIDataTable?: {
      styleOverrides?: ComponentsOverrides['MUIDataTable']
    }
  }
}

declare module '@mui/material/styles/overrides' {
  interface ComponentNameToClassKey {
    MUIDataTable: 'root' | 'caption' | 'liveAnnounce' | 'paper' | 'responsiveScroll' | 'tableRoot';
  }
}

declare module '@mui/material/styles' {
  interface Components {
    [key: string]: any //eslint-disable-line
  }
}
 */

const customTheme = createTheme({
  components: {
    /*
    MUIDataTableBodyCell: {
      styleOverrides: {
        root: {
          fontWeight: 'bold',
        },
      },
    },
     */
    MUIDataTable: {
      styleOverrides: {
        tableRoot: {
          height: "100%",
        },
        paper: {
          height: "calc(100% - 70px)",
          boxShadow: 'none',
        },
      }
    },
  }
})

function SearchBar(props: SearchBarProps) {

  const icon = props.value.length == 0 ? <SearchIcon/> : (
    <IconButton onClick={() => props.onChange("")}><ClearIcon/></IconButton>
  )

  return (
    <Stack direction="column" sx={{p: 1}}>
      <TextField
        value={props.value}
        onChange={(el) => {
          const value = el.target.value
          props.onChange(value)
        }}
        InputProps={{endAdornment: icon}}
      />
    </Stack>
  )
}

interface DocumentationTableProps {
  version: string
}

interface documentation {
  source: string,
  brief: string,
  arguments: string,
  description: string,
  searchText: string
}

function DocumentationTable(props: DocumentationTableProps) {
  const [value, setValue] = useState<string>("")
  const [data, setData] = useState<documentation[]>([])
  const [loading, setLoading] = useState<boolean>(false)

  const columns = [
    {
      name: "source",
      label: "Source",
      options: {
        customBodyRenderLite: (dataIndex: number): React.ReactNode => {
          const value = data[dataIndex].source
          return <span style={{fontFamily: "monospace", verticalAlign: "top"}}><strong>{value}</strong></span>
        }
      }
    },
    {
      name: "searchText",
      label: "Description",
      options: {
        customBodyRenderLite: (dataIndex: number): React.ReactNode => {
          const record = data[dataIndex]
          // value.replace('<strong>', '**')
          //value.replace('</strong>', '**')
          //return <ReactMarkdown>{value}</ReactMarkdown>
          return (
            <div style={{fontFamily: "monospace", fontSize: 12, whiteSpace: "pre-line"}}>
              <strong>{record.brief}</strong>
              {'\n' + record.arguments}
              <div dangerouslySetInnerHTML={{__html: record.description}}/>
            </div>
          )

          /*
          const parser = new DOMParser()
          const dom = parser.parseFromString(value, "text/html")

          const tags = dom.getElementsByTagName("strong")
          const tagCount = tags.length

          for (let k = 0; k < tagCount; k++) {
            const newElement = dom.createElement("pre")
            newElement.innerHTML = tags[0].innerHTML
            tags[0].replaceWith(newElement)
          }

          debugger //eslint-disable-line

          value = value.replace("<strong>", "<pre>").replace("</strong>", "</pre>")
          return <span>{value}</span>
           */
        }
      }
    }
  ]

  const fetchData = async (version: string) => {
    if (loading || data.length > 0) {
      return
    }

    setLoading(true)
    const response = await fetch(`http://localhost:5000/help/${version}`)
    const json = await response.json()

    // Add an aggregate field that contains all of the searchable info
    json.data.forEach((element: documentation) => {
      element.searchText = element.arguments + ' ' + element.brief + ' ' + element.description
    })

    setData(json.data)

    // const newData = json.data.map((element: documentation) => [element.source, element.description])
    // setData(newData)
    setLoading(false)

  }

  fetchData(props.version)

  return (
    <ThemeProvider theme={customTheme}>
      <MUIDataTable
        title={"Employee List"}
        data={data}
        columns={columns}
        options={{
          setTableProps: () => {
            return {style: {height: "200px"}}
          },
          download: false,
          tableBodyHeight: "100%",
          responsive: "standard",
          print: false,
          viewColumns: false,
          filter: false,
          pagination: false,
          searchAlwaysOpen: true,
          selectableRows: undefined,
        }}
      />
    </ThemeProvider>
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
    <Paper variant="outlined"
      sx={{
        p: 2,
        flexGrow: 1,
        whiteSpace: "pre",
        fontFamily: " monospace",
        fontSize: 14,
        marginLeft: 0,
        width: 1,
        overflow: "auto"
      }}>
      {props.output.join("\n")}
      {props.errors.length > 0 &&
        <Alert severity="error">
          {props.errors.join("\n")}
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
        sx={{flexGrow: 0}}
      >
        {
          props.versions.map((version) => {
            return (
              <MenuItem key={version.label} value={version.label}>{version.label}</MenuItem>
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

function PasteIconButton() {
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
    {"label": "22.7.4", "releaseDate": new Date()},
    {"label": "22.7.3", "releaseDate": new Date()}
  ]

  const [isConnected, setIsConnected] = useState<boolean>(socket.connected)
  const [code, setCode] = useState<string>(":t!")
  const [running, setRunning] = useState<boolean>(false)
  const [output, setOutput] = useState<string[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [version, setVersion] = useState<string>(versions[0].label)
  const [session, setSession] = useState<string | null>(null)
  const [inputs, setInputs] = useState<string>("120")
  const [showDocumentation, setShowDocumentation] = useState<boolean>(false)

  const runCode = async () => {
    if (running) {
      return
    }

    setRunning(true)
    setOutput([])
    setErrors([])

    await socket.emitWithAck('submit', {
      code,
      inputs,
      version,
      uid: session
    })
  }

  useHotkeys('ctrl+enter', runCode)

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

  return (
    <Box sx={{flexGrow: 1, height: 2, display: "flex", flexDirection: "column"}}>
      {/* Row containing the page title and documentation toggle */}
      <Stack direction="row" sx={{display: "flex", justifyContent: "space-between"}}>
        <Typography variant="h5" component="div" sx={{marginBottom: 3}}>
          MATL Interpreter
        </Typography>
        <FormControlLabel
          sx={{mr: 0}}
          labelPlacement="start"
          control={<Switch size="medium" checked={showDocumentation}
            onChange={(el) => setShowDocumentation(el.target.checked)}/>}
          label={<MenuBookIcon/>}
        />
      </Stack>
      {/* This is the horizontal row that contains the interpreter on the left and docs on the right */}
      <Box sx={{flexGrow: 1, display: "flex", flexDirection: "row", height: 2}}>
        {/* The code inputs, buttons, and output */}
        <Stack spacing={2} sx={{flexGrow: 1, flexBasis: "50%", width: 2, flexDirection: "column", maxHeight: 1}}>
          <Grid container spacing={2} sx={{mt: 0}}>
            <Grid item xs={9}>
              <TextField
                id="code"
                label={`Code ${code.length ? `(${code.length} byte${code.length > 1 ? "s" : ""})` : ''}`}
                multiline
                autoFocus={true}
                value={code}
                onChange={(el) => setCode(el.target.value)}
                maxRows={Infinity}
                variant="outlined"
                fullWidth
                InputProps={{style: {fontFamily: "monospace"}, endAdornment: <ExplainIconButton/>}}
              />
            </Grid>
            <Grid item xs={3}>
              <VersionSelect onChange={setVersion} value={version} versions={versions}/>
            </Grid>
          </Grid>
          <TextField
            id="inputs"
            label="Input Arguments"
            variant="outlined"
            multiline
            fullWidth
            value={inputs}
            onChange={(el) => setInputs(el.target.value)}
            maxRows={Infinity}
            InputProps={{style: {fontFamily: "monospace"}, endAdornment: <PasteIconButton/>}}
          />
          {/* Buttons for running the code and sharing*/}
          <Stack direction="row" spacing={1} sx={{width: showDocumentation ? 1 / 2 : 1 / 4}}>
            <Button
              variant='contained'
              disabled={!isConnected}
              onClick={runCode}
              sx={{minWidth: "9em"}}
              startIcon={running ? <CircularProgress size={14} color="inherit"/> : <PlayArrowIcon/>}
            >
              {
                running ? "Cancel" : "Run"
              }
            </Button>
            <Button
              variant='outlined'
              sx={{minWidth: "9em"}}
              startIcon={<ShareIcon/>}>
              Share
            </Button>
          </Stack>
          <Box sx={{
            whiteSpace: "pre",
            fontFamily: "monospace",
            overflow: "auto",
            flexGrow: 1,
            height: 2,
            width: 1,
            display: "flex"
          }}>
            <InterpreterOutput running={running} output={output} errors={errors}/>
          </Box>
        </Stack>
        {/* The documentation (if it exists)*/}
        {showDocumentation &&
          <Box sx={{flexGrow: 0, overflow: "auto", height: "100%", flexBasis: "50%", maxWidth: 600, marginLeft: 2}}>
            <DocumentationTable version={version}/>
          </Box>
        }
      </Box>
    </Box>
  )
}

function App() {
  return (
    <Box sx={{display: 'flex', flexDirection: "row"}}>
      <ButtonAppBar/>
      <Box component="main"
        sx={{p: 2, display: "flex", flexDirection: "column", flexGrow: 1, width: 2, height: "100vh"}}
      >
        <Toolbar/>
        <Interpreter/>
      </Box>
    </Box>
  )
}

export default App
