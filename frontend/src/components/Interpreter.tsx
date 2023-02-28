import React from "react"
import { useState, useEffect } from 'react'
import { Socket } from 'socket.io-client'
import VersionSelect from "./VersionSelect"
import InterpreterOutput from "./InterpreterOutput"
import Stack from '@mui/material/Stack'
import Button from '@mui/material/Button'
import Grid from '@mui/material/Grid'
import Tooltip from '@mui/material/Tooltip'
import IconButton from '@mui/material/IconButton'
import TroubleshootIcon from '@mui/icons-material/Troubleshoot'
import ContentPasteIcon from '@mui/icons-material/ContentPaste'
import TextField from '@mui/material/TextField'
import {useHotkeys} from 'react-hotkeys-hook'
import CircularProgress from '@mui/material/CircularProgress'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import ShareIcon from '@mui/icons-material/Share'
import Box from '@mui/material/Box'
import { Version } from './VersionSelect'

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

interface InterpreterProps {
  socket: Socket;
  onVersionChange: (version: Version) => void;
  version: Version;
  versions: Version[];
}

const Interpreter = (props: InterpreterProps) => {
  const { socket } = props

  const [isConnected, setIsConnected] = useState<boolean>(socket.connected)
  const [code, setCode] = useState<string>(":t!")
  const [running, setRunning] = useState<boolean>(false)
  const [output, setOutput] = useState<string[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [session, setSession] = useState<string | null>(null)
  const [inputs, setInputs] = useState<string>("120")

  const version = props.version

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
      version: version.label,
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
    <Stack spacing={2} direction="column" sx={{ height: 1}}>
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
          <VersionSelect
            onChange={(value) => {
              props.onVersionChange && props.onVersionChange(value)
            }}
            value={version}
            versions={props.versions}
          />
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
      <Stack direction="row" spacing={1} sx={{width: 1 / 2 }}>
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
  )
}

export default Interpreter
