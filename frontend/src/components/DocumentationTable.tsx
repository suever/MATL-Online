import React from 'react'
import { useState} from 'react'
import {createTheme, ThemeProvider} from '@mui/material/styles'
import MUIDataTable from "mui-datatables"
import { Version} from "./VersionSelect"

interface DocumentationTableProps {
  version: Version
}

const customTheme = createTheme({
  components: {
    MUIDataTable: {
      styleOverrides: {
        tableRoot: {
          height: "100%",
        },
        paper: {
          height: "calc(100% - 70px)",
          boxShadow: 'none',
        },
      }
    },
  }
})

interface documentation {
  source: string,
  brief: string,
  arguments: string,
  description: string,
  searchText: string
}

function DocumentationTable(props: DocumentationTableProps) {
  const [data, setData] = useState<documentation[]>([])
  const [loading, setLoading] = useState<boolean>(false)

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

  const fetchData = async (version: string) => {
    if (loading || data.length > 0) {
      return
    }

    setLoading(true)
    const response = await fetch(`http://localhost:5000/help/${version}`)
    const json = await response.json()

    // Add an aggregate field that contains all of the searchable info
    json.data.forEach((element: documentation) => {
      element.searchText = element.arguments + ' ' + element.brief + ' ' + element.description
    })

    setData(json.data)
    setLoading(false)

  }

  fetchData(props.version.label)

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
        }}
      />
    </ThemeProvider>
  )
}

export default DocumentationTable
