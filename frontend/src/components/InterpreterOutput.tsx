import React from 'react'
import Alert from '@mui/material/Alert'
import Paper from '@mui/material/Paper'

interface InterpreterOutputProps {
  running: boolean;
  output: string[];
  errors: string[];
}

const InterpreterOutput = (props: InterpreterOutputProps) => {
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

export default InterpreterOutput
