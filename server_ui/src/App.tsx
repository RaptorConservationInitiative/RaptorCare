import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

type GPUInfo = {
  device_id: number
  name: string
  total_memory_gb: number
  used_memory_gb: number
  free_memory_gb: number
  utilization_percent: number
}

type StationInfo = {
  station_id: string
  name: string
  location: string
  created_at: string
  updated_at: string
  sync_stats: {
    total: number
    pending: number
    completed: number
    failed: number
    queue_utilization_percent: number
  }
  gps_lat?: number
  gps_lon?: number
  contact_email?: string
  contact_phone?: string
}

type PatientInfo = {
  id: number
  internal_id: string
  species: string
  status: string
  station_id: string
  admission_date: string
  animal_class?: string
}

type CalendarEventInfo = {
  id: number
  title: string
  station_id: string
  bird_id?: number
  description?: string
  start_at: string
  end_at?: string
  all_day: boolean
  location?: string
}

type ResearchOutput = {
  research_text: string
  gpu_used?: number
  model?: string
}

function App() {
  const [serverUrl, setServerUrl] = useState('http://localhost:8000')
  const [token, setToken] = useState('')
  const [stations, setStations] = useState<StationInfo[]>([])
  const [selectedStation, setSelectedStation] = useState('station_001')
  const [selectedTab, setSelectedTab] = useState<'bird' | 'reptile' | 'mammal'>('bird')
  const [stationData, setStationData] = useState('No station data loaded yet.')
  const [patients, setPatients] = useState<PatientInfo[]>([])
  const [events, setEvents] = useState<CalendarEventInfo[]>([])
  const [gpuStatus, setGpuStatus] = useState<GPUInfo[] | null>(null)
  const [overviewReport, setOverviewReport] = useState<Record<string, any> | null>(null)
  const [researchResponse, setResearchResponse] = useState<string>('')
  const [researchGoal, setResearchGoal] = useState('Summarize this case and provide research questions.')
  const [researchNotes, setResearchNotes] = useState('')
  const [language, setLanguage] = useState('en')
  const [statusMessage, setStatusMessage] = useState('Ready')
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const leafletMapRef = useRef<L.Map | null>(null)
  const markerLayerRef = useRef<L.LayerGroup | null>(null)

  const headers: Record<string, string> = token
    ? {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    : { 'Content-Type': 'application/json' }

  useEffect(() => {
    if (!mapContainerRef.current || leafletMapRef.current) return

    const defaultIcon = L.icon({
      iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
    })
    L.Marker.prototype.options.icon = defaultIcon

    leafletMapRef.current = L.map(mapContainerRef.current, {
      center: [20, 0],
      zoom: 2,
      zoomControl: true,
      scrollWheelZoom: true,
    })

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(leafletMapRef.current)

    markerLayerRef.current = L.layerGroup().addTo(leafletMapRef.current)
  }, [])

  useEffect(() => {
    if (!leafletMapRef.current) return
    const selectedStationInfo = stations.find((station) => station.station_id === selectedStation)
    if (selectedStationInfo?.gps_lat != null && selectedStationInfo?.gps_lon != null) {
      leafletMapRef.current.flyTo([selectedStationInfo.gps_lat, selectedStationInfo.gps_lon], 12, {
        duration: 1.2,
      })
    }
  }, [selectedStation, stations])

  const fetchGpuStatus = async () => {
    if (!token) {
      setResearchResponse('Please provide a bearer token to fetch GPU status.')
      return
    }

    try {
      const response = await fetch(`${serverUrl}/research/gpu-status`, {
        headers,
      })
      if (!response.ok) {
        const text = await response.text()
        throw new Error(`${response.status} ${text}`)
      }
      const data = await response.json()
      setGpuStatus(data.gpus || [])
      setStatusMessage('GPU status loaded successfully.')
    } catch (error: any) {
      setGpuStatus(null)
      setStatusMessage(`GPU status fetch failed: ${error.message}`)
    }
  }

  const fetchStations = async () => {
    if (!token) {
      setStatusMessage('Please provide a bearer token to load stations.')
      return
    }

    try {
      const response = await fetch(`${serverUrl}/stations`, {
        headers,
      })
      if (!response.ok) {
        const text = await response.text()
        throw new Error(`${response.status} ${text}`)
      }

      const data = await response.json()
      const stationData = data.stations || []
      setStations(stationData)
      setStatusMessage('Station overview loaded.')
      if (stationData.length) {
        setSelectedStation(stationData[0].station_id)
      }
      updateStationMap(stationData)
    } catch (error: any) {
      setStatusMessage(`Failed to load stations: ${error.message}`)
    }
  }

  const fetchOverviewReport = async () => {
    if (!token) {
      setStatusMessage('Please provide a bearer token to load overview data.')
      return
    }

    try {
      const response = await fetch(`${serverUrl}/reports/overview`, {
        headers,
      })
      if (!response.ok) {
        const text = await response.text()
        throw new Error(`${response.status} ${text}`)
      }
      const data = await response.json()
      setOverviewReport(data)
      setStatusMessage('Overview report loaded.')
    } catch (error: any) {
      setOverviewReport(null)
      setStatusMessage(`Failed to load overview report: ${error.message}`)
    }
  }

  const handleTabChange = (tab: 'bird' | 'reptile' | 'mammal') => {
    setSelectedTab(tab)
    fetchPatients(selectedStation, tab)
    setStatusMessage(`Showing ${tab === 'bird' ? 'Bird' : tab === 'reptile' ? 'Reptile' : 'Mammal'} records.`)
  }

  const requestResearch = async (endpoint: string) => {
    if (!token) {
      setResearchResponse('Please provide a bearer token for research requests.')
      return
    }

    try {
      const response = await fetch(`${serverUrl}/research/${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          bird_data: {
            species: 'Peregrine Falcon',
            status: 'in_treatment',
            weight: 950,
            days_in_care: 6,
            injury: 'wing fracture',
          },
          health_history: [
            { date: '2026-05-18', metric: 'weight', value: 930, behavior: 'alert' },
            { date: '2026-05-19', metric: 'weight', value: 940, behavior: 'improving' },
          ],
          notes: researchNotes || researchGoal,
          research_goal: researchGoal,
        }),
      })
      if (!response.ok) {
        const text = await response.text()
        throw new Error(`${response.status} ${text}`)
      }
      const data: ResearchOutput = await response.json()
      setResearchResponse(data.research_text)
      setStatusMessage(`Research result returned from ${endpoint}.`)
    } catch (error: any) {
      setResearchResponse(`Request failed: ${error.message}`)
      setStatusMessage('Research request failed.')
    }
  }

  const fetchPatients = async (stationId?: string, animalClass?: string) => {
    if (!token) {
      setStatusMessage('Please provide a bearer token to fetch patient records.')
      return
    }

    try {
      const base = stationId
        ? `${serverUrl}/patients?station_id=${encodeURIComponent(stationId)}&limit=100`
        : `${serverUrl}/patients?limit=100`
      const path = animalClass ? `${base}&animal_class=${encodeURIComponent(animalClass)}` : base
      const response = await fetch(path, {
        headers,
      })
      if (!response.ok) {
        const text = await response.text()
        throw new Error(`${response.status} ${text}`)
      }
      const data = await response.json()
      setPatients(data.patients || data.birds || [])
      const count = data.patients?.length ?? data.birds?.length ?? 0
      setStatusMessage(`Loaded ${count} patient records.`)
    } catch (error: any) {
      setPatients([])
      setStatusMessage(`Failed to load patients: ${error.message}`)
    }
  }

  const fetchCalendarEvents = async (stationId: string) => {
    if (!token) {
      setStatusMessage('Please provide a bearer token to load calendar events.')
      return
    }

    try {
      const response = await fetch(`${serverUrl}/calendar/events?station_id=${encodeURIComponent(stationId)}`, {
        headers,
      })
      if (!response.ok) {
        const text = await response.text()
        throw new Error(`${response.status} ${text}`)
      }
      const data = await response.json()
      setEvents(data)
      setStatusMessage(`Loaded ${data.length} calendar events for ${stationId}.`)
    } catch (error: any) {
      setEvents([])
      setStatusMessage(`Failed to load calendar events: ${error.message}`)
    }
  }

  const loadStationData = () => {
    const station = stations.find((item) => item.station_id === selectedStation)
    if (!station) {
      setStationData('Select a station and load the station overview first.')
      return
    }

    setStationData(
      `Station ${station.station_id} (${station.name})\n` +
        `Location: ${station.location}\n` +
        `Queue pending: ${station.sync_stats.pending}\n` +
        `Queue completed: ${station.sync_stats.completed}\n` +
        `Queue failed: ${station.sync_stats.failed}\n` +
        `Utilization: ${station.sync_stats.queue_utilization_percent.toFixed(1)}%`
    )
  }

  const updateStationMap = (stationData: StationInfo[]) => {
    if (!markerLayerRef.current || !leafletMapRef.current) return
    markerLayerRef.current.clearLayers()
    const bounds: L.LatLngTuple[] = []

    stationData.forEach((station) => {
      if (station.gps_lat != null && station.gps_lon != null) {
        const marker = L.marker([station.gps_lat, station.gps_lon])
        marker.bindPopup(`<strong>${station.name}</strong><br/>${station.location}`)
        marker.on('click', () => {
          setSelectedStation(station.station_id)
          setStatusMessage(`Selected station ${station.name} from map.`)
        })
        marker.addTo(markerLayerRef.current!)
        bounds.push([station.gps_lat, station.gps_lon])
      }
    })

    if (bounds.length) {
      leafletMapRef.current.fitBounds(bounds, { padding: [32, 32], maxZoom: 12 })
    }
  }

  return (
    <div className="container">
      <header>
        <h1>RaptorCare Server Dashboard</h1>
        <p>Central control panel for station data, research tools, and GPU status.</p>
      </header>

      <section>
        <h2>Connection</h2>
        <div className="grid">
          <label>
            Server URL
            <input value={serverUrl} onChange={(e) => setServerUrl(e.target.value)} />
          </label>
          <label>
            Bearer Token
            <input value={token} onChange={(e) => setToken(e.target.value)} type="password" />
          </label>
          <label>
            UI Language
            <select value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="en">English</option>
              <option value="de">Deutsch</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
            </select>
          </label>
        </div>
      </section>

      <section>
        <h2>Overview Report</h2>
        <div className="grid">
          <button className="primary" onClick={fetchOverviewReport}>Load overview report</button>
        </div>
        {overviewReport ? (
          <div className="queue-list">
            <div className="queue-item">
              <strong>Total birds</strong>: {overviewReport.total_birds}
            </div>
            <div className="queue-item">
              <strong>Total stations</strong>: {overviewReport.total_stations}
            </div>
            <div className="queue-item">
              <strong>Total schedule events</strong>: {overviewReport.total_calendar_events}
            </div>
            <div className="queue-item">
              <strong>Total media files</strong>: {overviewReport.total_media_files}
            </div>
            <div className="queue-item">
              <strong>Animal class counts</strong>: {JSON.stringify(overviewReport.animal_class_counts)}
            </div>
          </div>
        ) : (
          <p>No overview loaded yet.</p>
        )}
      </section>

      <section>
        <h2>Station Overview</h2>
        <div className="grid">
          <button className="primary" onClick={fetchStations}>Refresh stations list</button>
          <label>
            Select station
            <select value={selectedStation} onChange={(e) => setSelectedStation(e.target.value)}>
              {stations.map((station) => (
                <option key={station.station_id} value={station.station_id}>
                  {station.station_id}
                </option>
              ))}
            </select>
          </label>
          <button className="primary" onClick={loadStationData}>Show station details</button>
          <button className="primary" onClick={() => fetchPatients(selectedStation)}>Load patients for selected station</button>
          <button className="primary" onClick={() => fetchCalendarEvents(selectedStation)}>Load schedule</button>
        </div>
        <pre>{stationData}</pre>
        {stations.some((item) => item.gps_lat !== undefined && item.gps_lon !== undefined) ? (
          <div className="map-card">
            <h3>Station map</h3>
            <div ref={mapContainerRef} className="leaflet-map" />
            <p>Click a marker to select a station and see its details.</p>
          </div>
        ) : (
          <p>No location data available for the selected station map.</p>
        )}
        <div className="queue-list">
          {stations.map((station) => (
            <div key={station.station_id} className="queue-item">
              <strong>{station.name}</strong>
              <p>ID: {station.station_id}</p>
              <p>Pending: {station.sync_stats.pending}</p>
              <p>Completed: {station.sync_stats.completed}</p>
              <p>Failed: {station.sync_stats.failed}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Patient List</h2>
        <div className="button-row">
          <button type="button" className={selectedTab === 'bird' ? 'primary' : 'secondary'} onClick={() => handleTabChange('bird')}>
            Birds
          </button>
          <button type="button" className={selectedTab === 'reptile' ? 'primary' : 'secondary'} onClick={() => handleTabChange('reptile')}>
            Reptiles
          </button>
          <button type="button" className={selectedTab === 'mammal' ? 'primary' : 'secondary'} onClick={() => handleTabChange('mammal')}>
            Mammals
          </button>
        </div>
        <button className="primary" onClick={() => fetchPatients(selectedStation, selectedTab)}>Refresh {selectedTab === 'bird' ? 'bird' : selectedTab === 'reptile' ? 'reptile' : 'mammal'} list</button>
        <div className="queue-list">
          {patients.map((patient) => (
            <div key={patient.id} className="queue-item">
              <strong>{patient.internal_id}</strong>
              <p>Type: {patient.animal_class ?? 'unknown'}</p>
              <p>Species: {patient.species}</p>
              <p>Status: {patient.status}</p>
              <p>Station: {patient.station_id}</p>
              <p>Admitted: {new Date(patient.admission_date).toLocaleDateString()}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Calendar / Schedule</h2>
        <button className="primary" onClick={() => fetchCalendarEvents(selectedStation)}>Refresh schedule</button>
        <div className="queue-list">
          {events.map((event) => (
            <div key={event.id} className="queue-item">
              <strong>{event.title}</strong>
              <p>Station: {event.station_id}</p>
              <p>Patient ID: {event.bird_id ?? 'n/a'}</p>
              <p>{new Date(event.start_at).toLocaleString()} {event.all_day ? '(all day)' : ''}</p>
              <p>Location: {event.location ?? 'Not specified'}</p>
              <p>{event.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>LLM Research Tools</h2>
        <div className="grid">
          <label>
            Research goal
            <textarea value={researchGoal} onChange={(e) => setResearchGoal(e.target.value)} rows={3} />
          </label>
          <label>
            Research notes / literature excerpt
            <textarea value={researchNotes} onChange={(e) => setResearchNotes(e.target.value)} rows={3} />
          </label>
        </div>
        <div className="button-row">
          <button onClick={() => requestResearch('summary')}>Generate case summary</button>
          <button onClick={() => requestResearch('hypotheses')}>Generate hypotheses</button>
          <button onClick={() => requestResearch('literature')}>Summarize literature</button>
        </div>
        <pre>{researchResponse}</pre>
      </section>

      <section>
        <h2>GPU Status</h2>
        <button className="primary" onClick={fetchGpuStatus}>Refresh GPU status</button>
        <p>{statusMessage}</p>
        <div className="gpu-list">
          {gpuStatus?.map((gpu) => (
            <div key={gpu.device_id} className="card">
              <h3>GPU {gpu.device_id}</h3>
              <p>{gpu.name}</p>
              <p>Memory: {gpu.used_memory_gb} / {gpu.total_memory_gb} GB</p>
              <p>Utilization: {gpu.utilization_percent}%</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default App
