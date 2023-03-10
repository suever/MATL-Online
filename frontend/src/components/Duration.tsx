import React from 'react'
import { useState } from 'react'
import Box from '@mui/material/Box'
import { useElapsedTime } from 'use-elapsed-time'
import Typography from '@mui/material/Typography'
import AccessTimeIcon from '@mui/icons-material/AccessTime'

interface DurationProps {
  running: boolean;
  precision?: number;
}

const defaultPrecision = 2

export default function Duration (props: DurationProps) {
  const [duration, setDuration] = useState<number>(0)
  const [running, setRunning] = useState<boolean>(false)

  const { reset } = useElapsedTime({
    isPlaying: props.running,
    onUpdate: (elapsed) => setDuration(elapsed),
  })

  // If the running state was changed...
  if (running !== props.running) {
    setRunning(props.running)

    // If this is a new run, then reset the elapsed time timer
    if (props.running) {
      reset()
    }
  }

  const precision = typeof props.precision === 'undefined' ? defaultPrecision : props.precision

  return (
    <Box sx={{ visibility: duration !== 0 ? "visible" : "hidden", alignItems: 'baseline', display: "flex"}}>
      <Typography color="text.secondary" sx={{ marginTop: "auto", marginBottom: -2, alignItems: 'baseline', justifyContent: 'flex-end'}}>
        <AccessTimeIcon fontSize="inherit"/> {duration.toFixed(precision)}s
      </Typography>
    </Box>
  )
}
