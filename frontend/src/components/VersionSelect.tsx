import React from 'react'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'

export interface Version {
  label: string
  releaseDate: Date
}

interface VersionSelectProps {
  onChange: (value: Version) => void;
  value: Version;
  versions: Version[];
}

function VersionSelect(props: VersionSelectProps) {

  const labels = props.versions.map((v) => v.label)
  const currentIndex = labels.indexOf(props.value.label)

  return (
    <FormControl fullWidth>
      <InputLabel id="version">Version</InputLabel>
      <Select
        labelId="version"
        id="version"
        label="Version"
        onChange={(el) => {
          const index  = parseInt(el.target.value.toString())
          props.onChange(props.versions[index])
        }}
        value={currentIndex}
        sx={{flexGrow: 0}}
      >
        {
          props.versions.map((version, id: number) => {
            return (
              <MenuItem key={version.label} value={id}>{version.label}</MenuItem>
            )
          })

        }
      </Select>
    </FormControl>
  )
}

export default VersionSelect
