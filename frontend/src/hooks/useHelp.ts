import {Version} from "../components/VersionSelect"
import { useState, useEffect } from 'react'
import {documentation} from '../components/DocumentationTable'

const cache = new Map<string, documentation[]>()

const fetchHelp = async (version: Version) :  Promise<documentation[]> => {
  const response = await fetch(`http://localhost:5000/help/${version.label}`)
  const json  = await response.json()

  json.data.forEach((element: documentation) => {
    element.searchText = element.arguments + ' ' + element.brief + ' ' + element.description
  })

  return json.data
}

const useHelp = (version: Version) => {
  const [loading, setLoading] = useState<boolean>(false)
  const [data, setData] = useState<documentation[]>([])

  useEffect(() => {
    const fetchData = async() => {
      setLoading(true)

      // Retrieve the help data for this cache (if available)
      let helpData = cache.get(version.label)

      // Fetch data and populate the cache if it was missing
      if (helpData == null) {
        helpData = await fetchHelp(version)
        cache.set(version.label, helpData)
      }

      setData(helpData)
      setLoading(false)
    }

    fetchData()

  }, [version])

  return { loading, data }
}

export default useHelp
