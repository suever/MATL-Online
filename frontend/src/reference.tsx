import React from "react"
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CssBaseline from '@mui/material/CssBaseline'
import Paper from '@mui/material/Paper'

export default function App() {
  return (
    <>
      <CssBaseline/>
      <Box sx={{display: "flex", flexDirection: "column", height: "100vh"}}>
        <Box sx={{display: "flex", flexDirection: "row", border: "1px solid #F00" }}>
          <Button sx={{ flexGrow: 1, border: "1px solid #0F0" }}>Button 1</Button>
          <Button sx={{ flexGrow: 1, border: "1px solid #0F0" }}>Button 2</Button>
        </Box>
        <Box sx={{ flexGrow: 1, border: "1px solid #000", backgroundColor: "red", overflow: "auto"}}>
          <Paper variant="outlined" sx={{ p: 2, whiteSpace: "pre", fontFamily: "monospace", height: 1, overflow: "auto"}}>
            {
              [...Array(125).keys()].map((value) => `${value}\n`)
            }
          </Paper>
        </Box>
      </Box>
    </>
  )
}
