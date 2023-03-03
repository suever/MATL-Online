import React from 'react'
import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import RadioGroup from '@mui/material/RadioGroup'
import Radio from '@mui/material/Radio'
import FormControlLabel from '@mui/material/FormControlLabel'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import TextField from '@mui/material/TextField'
import Stack from '@mui/material/Stack'
import Button from '@mui/material/Button'
import { nestedArraysTo2DArray, multiLineStringToArray} from "../utilities/strings"

interface InputPasteDialogProps {
  onApply?: (value: string) => void
  onClose?: () => void
  open: boolean
}

enum PasteInputType {
  Array,
  String,
}

const placeholders =  new Map<PasteInputType, string>([
  [PasteInputType.Array, "[[1, 2, 3], [4, 5, 6]]"],
  [PasteInputType.String, "Multi-line\nString"],
])

function InputPasteDialog(props: InputPasteDialogProps) {
  const [input, setInput] = useState<string>("")
  const [inputType, setInputType] = useState<PasteInputType>(PasteInputType.Array)

  const handleApply = () => {
    const transformed = inputType == PasteInputType.Array ?
      nestedArraysTo2DArray(input) :
      multiLineStringToArray(input)

    // Transform the data per the rules
    if (props.onApply && transformed !== '') {
      props.onApply(transformed)
    }

    handleClose()
  }

  const handleClose = () => {
    setInput('')
    props.onClose && props.onClose()
  }
  const placeholder = placeholders.get(inputType)

  return (
    <Dialog open={props.open} onClose={handleClose}>
      <DialogTitle>Paste Input Argument</DialogTitle>
      <DialogContent sx={{p: 4, minWidth: 500, overflow: "auto"}}>
        <Stack direction="column" spacing={2}>
          <TextField
            autoFocus
            id="input"
            fullWidth
            multiline
            value={input}
            placeholder={placeholder}
            onChange={(el) => setInput(el.target.value)}
            minRows={6}
            InputProps={{
              style: { fontFamily: "monospace", whiteSpace: "nowrap", overflowWrap: "normal", overflowX: "auto"}
            }}
          />
          <RadioGroup row value={inputType} onChange={(el) => setInputType(parseInt(el.target.value))}>
            <FormControlLabel value={PasteInputType.Array} control={<Radio/>} label="Python Array"/>
            <FormControlLabel value={PasteInputType.String} control={<Radio/>} label="Multi-line String"/>
          </RadioGroup>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button onClick={handleApply}>Apply</Button>
      </DialogActions>
    </Dialog>
  )
}

export default InputPasteDialog
