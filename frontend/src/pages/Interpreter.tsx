import React from 'react'
import { useState } from 'react'
import {Version} from "../components/VersionSelect"
import InterpreterComponent from "../components/Interpreter"
import DocumentationTable from "../components/DocumentationTable"
import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import FormControlLabel from '@mui/material/FormControlLabel'
import Switch from '@mui/material/Switch'
import MenuBookIcon from '@mui/icons-material/MenuBook'
import { Socket } from 'socket.io-client'

interface InterpreterProps {
  socket: Socket
}

const Interpreter = (props: InterpreterProps) => {
  const versions = [
    {"label": "22.7.4", "releaseDate": new Date()},
    {"label": "22.7.3", "releaseDate": new Date()},
    {"label": "20.2.1", "releaseDate": new Date()},
  ]
  const [version, setVersion] = useState<Version>(versions[0])
  const [showDocumentation, setShowDocumentation] = useState<boolean>(false)
  const [search, setSearch] = useState<string>("")

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
        <Box sx={{ flexGrow: 1, flexBasis: 0.5, width: 2}}>
          <InterpreterComponent socket={props.socket} version={version} versions={versions} onVersionChange={(v: Version) => setVersion(v)}/>
        </Box>
        {/* The documentation (if it exists)*/}
        {showDocumentation &&
          <Box sx={{flexGrow: 0, overflow: "auto", height: "100%", flexBasis: "50%", maxWidth: 600, marginLeft: 2}}>
            <DocumentationTable version={version} searchText={search} onSearchChange={setSearch}/>
          </Box>
        }
      </Box>
    </Box>
  )
}

export default Interpreter
