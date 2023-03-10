import React from 'react'
import { useState } from 'react'
import Box from '@mui/material/Box'
import Toolbar from '@mui/material/Toolbar'
import Header from "../components/Header"
import Navigation from "../components/Navigation"
import InterpreterPage from "./Interpreter"
import io from 'socket.io-client'
import { baseUrl} from "../utilities/api"

const socket = io(baseUrl())

const Root = () => {
  const [collapsed, setCollapsed] = useState<boolean>(true)

  return (
    <Box sx={{display: 'flex', flexDirection: "row"}}>
      <Box sx={{ height: "100vh"}}>
        <Header onMenuClick={() => setCollapsed(!collapsed)}/>
        <Navigation collapsed={collapsed}/>
      </Box>
      <Box component="main"
        sx={{p: 2, display: "flex", flexDirection: "column", flexGrow: 1, width: 2, height: "100vh"}}
      >
        <Toolbar/>
        <InterpreterPage socket={socket}/>
      </Box>
    </Box>
  )
}

export default Root
