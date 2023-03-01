import MUIDataTable from "mui-datatables"
import React from 'react'
import useHelp from "../hooks/useHelp"
import { Version} from "./VersionSelect"
import {createTheme, ThemeProvider} from '@mui/material/styles'

interface DocumentationTableProps {
  onSearchChange?: (search: string) => void
  searchText?: string | null
  version: Version
}

const customTheme = createTheme({
  components: {
    MUIDataTable: {
      styleOverrides: {
        paper: {
          height: "calc(100% - 70px)",
          boxShadow: 'none',
        },
      }
    },
  }
})

export interface documentation {
  source: string,
  brief: string,
  arguments: string,
  description: string,
  searchText: string
}

function DocumentationTable(props: DocumentationTableProps) {
  const { data } = useHelp(props.version)

  const columns = [
    {
      name: "source",
      label: "Source",
      options: {
        customBodyRenderLite: (dataIndex: number): React.ReactNode => {
          const value = data[dataIndex].source
          return <span style={{fontFamily: "monospace", verticalAlign: "top"}}><strong>{value}</strong></span>
        }
      }
    },
    {
      name: "searchText",
      label: "Description",
      options: {
        customBodyRenderLite: (dataIndex: number): React.ReactNode => {
          const record = data[dataIndex]
          return (
            <div style={{fontFamily: "monospace", fontSize: 12, whiteSpace: "pre-line"}}>
              <strong>{record.brief}</strong>
              {'\n' + record.arguments}
              <div dangerouslySetInnerHTML={{__html: record.description}}/>
            </div>
          )
        }
      }
    }
  ]

  return (
    <ThemeProvider theme={customTheme}>
      <MUIDataTable
        title={"Employee List"}
        data={data}
        columns={columns}
        options={{
          download: false,
          tableBodyHeight: "100%",
          responsive: "standard",
          print: false,
          viewColumns: false,
          filter: false,
          pagination: false,
          searchAlwaysOpen: true,
          selectableRows: undefined,
          searchText: props.searchText || '',
          onSearchChange: (s: string | null) => {
            props.onSearchChange && props.onSearchChange(s || "")
          }
        }}
      />
    </ThemeProvider>
  )
}

export default DocumentationTable
