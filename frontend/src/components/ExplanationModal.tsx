import React from 'react'
import { useState } from 'react'
import Modal from '@mui/material/Modal'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

interface ExplanationModalProps {
  explanation: string
  open: boolean
  onClose?: () => void;
}

const style = {
  position: 'absolute' as const,
  top: '50%',
  left: '50%',
  maxHeight: "50vh",
  overflow: "auto",
  padding: 50,
  transform: 'translate(-50%, -50%)',
  backgroundColor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
}

function ExplanationModal(props: ExplanationModalProps) {
  const handleClose = () => {
    if (props.onClose) {
      props.onClose()
    }
  }

  return (
    <Modal open={props.open} onClose={handleClose}>
      <Box sx={style}>
        <Typography id="modal-modal-title" variant="h6">
          Explanation
        </Typography>
        <Typography sx={{ fontFamily: "monospace", whiteSpace: "pre"}}>
          {props.explanation}
        </Typography>
      </Box>
    </Modal>
  )
}

export default ExplanationModal

