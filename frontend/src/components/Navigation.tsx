import React from 'react'
import MenuBookIcon from '@mui/icons-material/MenuBook'
import BarChartIcon from '@mui/icons-material/BarChart'
import HistoryIcon from '@mui/icons-material/History'
import CodeIcon from '@mui/icons-material/Code'
import SchoolIcon from '@mui/icons-material/School'
import HelpIcon from '@mui/icons-material/Help'
import Box from '@mui/material/Box'
import Drawer from '@mui/material/Drawer'
import Toolbar from '@mui/material/Toolbar'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'

const navigationOptions = [
  {
    label: "Interpreter",
    icon: <CodeIcon/>,
    selected: true
  },
  {
    label: "Documentation",
    icon: <MenuBookIcon/>
  },
  {
    label: "Examples",
    icon: <SchoolIcon/>,
  },
  {
    label: "History",
    icon: <HistoryIcon/>
  },
  {
    label: "Analytics",
    icon: <BarChartIcon/>
  },
  {
    label: "Help",
    icon: <HelpIcon/>
  }
]

interface NavigationProps {
  width: number;
}

const Navigation = (props: NavigationProps) => {
  return (
    <Drawer
      variant='persistent'
      open={true}
      sx={{
        width: props.width,
        flexShrink: 0
      }}
    >
      <Toolbar/>
      <Box sx={{overflow: 'auto', width: props.width}}>
        <List>
          {
            navigationOptions.map((option) => {
              return (
                <ListItem key={option.label} disablePadding selected={option.selected == true}>
                  <ListItemButton>
                    <ListItemIcon>
                      {option.icon}
                    </ListItemIcon>
                    <ListItemText primary={option.label}>
                      {option.label}
                    </ListItemText>
                  </ListItemButton>
                </ListItem>
              )
            })

          }
        </List>
      </Box>
    </Drawer>
  )
}

export default Navigation
