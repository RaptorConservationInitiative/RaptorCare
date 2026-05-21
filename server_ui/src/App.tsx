import { useState } from 'react'

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

type BirdInfo = {
  id: number
  internal_id: string
  species: string
  status: string
  station_id: string
  admission_date: string
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
  const [stationData, setStationData] = useState('No station data loaded yet.')
  const [birds, setBirds] = useState<BirdInfo[]>([])
  const [events, setEvents] = useState<CalendarEventInfo[]>([])
  const [gpuStatus, setGpuStatus] = useState<GPUInfo[] | null>(null)
  const [overviewReport, setOverviewReport] = useState<Record<string, any> | null>(null)
  const [researchResponse, setResearchResponse] = useState<string>('')
  const [researchGoal, setResearchGoal] = useState('Summarize this case and provide research questions.')
  const [researchNotes, setResearchNotes] = useState('')
  const [language, setLanguage] = useState('en')
  const [statusMessage, setStatusMessage] = useState('Ready')

  const headers = token
    ? {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    : { 'Content-Type': 'application/json' }

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
      setStations(data.stations || [])
      setStatusMessage('Station overview loaded.')
      if (data.stations?.length) {
        setSelectedStation(data.stations[0].station_id)
      }
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

  const fetchBirds = async (stationId?: string) => {
    if (!token) {
      setStatusMessage('Please provide a bearer token to fetch bird records.')
      return
    }

    try {
      const path = stationId
        ? `${serverUrl}/birds?station_id=${encodeURIComponent(stationId)}&limit=100`
        : `${serverUrl}/birds?limit=100`
      const response = await fetch(path, {
        headers,
      })
      if (!response.ok) {
        const text = await response.text()
        throw new Error(`${response.status} ${text}`)
      }
      const data = await response.json()
      setBirds(data.birds || [])
      setStatusMessage(`Loaded ${data.birds?.length ?? 0} bird records.`)
    } catch (error: any) {
      setBirds([])
      setStatusMessage(`Failed to load birds: ${error.message}`)
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
          <button className="primary" onClick={() => fetchBirds(selectedStation)}>Load birds for selected station</button>
          <button className="primary" onClick={() => fetchCalendarEvents(selectedStation)}>Load schedule</button>
        </div>
        <pre>{stationData}</pre>
        {stations.find((item) => item.station_id === selectedStation)?.gps_lat !== undefined ? (
          <div className="map-card">
            <h3>Selected station location</h3>
            <iframe
              title="Station map"
              width="100%"
              height="350"
              src={`https://www.openstreetmap.org/export/embed.html?bbox=${(stations.find((item) => item.station_id === selectedStation)?.gps_lon ?? 0) - 0.01}%2C${(stations.find((item) => item.station_id === selectedStation)?.gps_lat ?? 0) - 0.01}%2C${(stations.find((item) => item.station_id === selectedStation)?.gps_lon ?? 0) + 0.01}%2C${(stations.find((item) => item.station_id === selectedStation)?.gps_lat ?? 0) + 0.01}&layer=mapnik&marker=${stations.find((item) => item.station_id === selectedStation)?.gps_lat ?? 0}%2C${stations.find((item) => item.station_id === selectedStation)?.gps_lon ?? 0}`}
            />
          </div>
        ) : (
          <p>No location data available for the selected station.</p>
        )}
        <div className="queue-list">
          {stations.map((station) => (
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
        <button className="primary" onClick={() => fetchBirds(selectedStation)}>Refresh patient list</button>
        <div className="queue-list">
          {birds.map((bird) => (
            <div key={bird.id} className="queue-item">
              <strong>{bird.internal_id}</strong>
              <p>Species: {bird.species}</p>
              <p>Status: {bird.status}</p>
              <p>Station: {bird.station_id}</p>
              <p>Admitted: {new Date(bird.admission_date).toLocaleDateString()}</p>
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
              <p>Bird ID: {event.bird_id ?? 'n/a'}</p>
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
