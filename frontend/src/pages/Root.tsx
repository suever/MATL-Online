import React from 'react'
import Box from '@mui/material/Box'
import Toolbar from '@mui/material/Toolbar'
import Header from "../components/Header"
import Navigation from "../components/Navigation"
import InterpreterPage from "./Interpreter"
import io from 'socket.io-client'

const socket = io('http://localhost:5000')

const Root = () => {
  const drawerWidth = 240

  return (
    <Box sx={{display: 'flex', flexDirection: "row"}}>
      <>
        <Header/>
        <Navigation width={drawerWidth}/>
      </>
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
