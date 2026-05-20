import { useEffect, useState } from 'react'

type QueueItem = {
  id: string
  action: string
  entity_type: string
  data: Record<string, any>
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
}

const STORAGE_KEY = 'raptorcare_station_queue'

function loadQueue(): QueueItem[] {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return []
  try {
    return JSON.parse(raw)
  } catch {
    return []
  }
}

function saveQueue(queue: QueueItem[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(queue))
}

function App() {
  const [stationId, setStationId] = useState('station_001')
  const [serverUrl, setServerUrl] = useState('http://localhost:8000')
  const [token, setToken] = useState('')
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [syncResult, setSyncResult] = useState<string>('')
  const [statusMessage, setStatusMessage] = useState('Ready')
  const [birdInternalId, setBirdInternalId] = useState('')
  const [birdAnimalClass, setBirdAnimalClass] = useState('bird')
  const [birdSpecies, setBirdSpecies] = useState('peregrine_falcon')
  const [healthBirdId, setHealthBirdId] = useState(1)
  const [healthWeight, setHealthWeight] = useState(0)
  const [healthBehavior, setHealthBehavior] = useState('')
  const [stations, setStations] = useState<StationInfo[]>([])
  const [stationDetails, setStationDetails] = useState('No station data loaded yet.')

  useEffect(() => {
    setQueue(loadQueue())
  }, [])

  useEffect(() => {
    saveQueue(queue)
  }, [queue])

  const addQueueItem = (item: QueueItem) => {
    setQueue((prev) => [...prev, item])
    setStatusMessage(`Queued ${item.action} ${item.entity_type}`)
  }

  const createBird = () => {
    if (!birdInternalId) {
      setStatusMessage('Please enter an internal ID.')
      return
    }

    addQueueItem({
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      action: 'create',
      entity_type: 'bird',
      data: {
        internal_id: birdInternalId,
        species: birdSpecies,
      },
    })

    setBirdInternalId('')
    setStatusMessage('Bird saved locally and queued for sync.')
  }

  const recordHealth = () => {
    addQueueItem({
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      action: 'create',
      entity_type: 'health_record',
      data: {
        bird_id: healthBirdId,
        weight_grams: healthWeight,
        behavior: healthBehavior,
        recorded_at: new Date().toISOString(),
      },
    })

    setHealthBehavior('')
    setStatusMessage('Health record stored locally.')
  }

  const createCalendarEvent = () => {
    if (!calendarTitle || !calendarDate) {
      setStatusMessage('Please provide a title and date for the calendar event.')
      return
    }

    const startAt = `${calendarDate}T${calendarTime}:00Z`

    addQueueItem({
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      action: 'create',
      entity_type: 'calendar_event',
      data: {
        title: calendarTitle,
        description: calendarNotes,
        start_at: startAt,
        end_at: startAt,
        all_day: false,
        location: calendarLocation,
        bird_id: healthBirdId,
      },
    })

    setCalendarTitle('')
    setCalendarNotes('')
    setCalendarLocation('')
    setStatusMessage('Calendar event saved locally and queued for sync.')
  }

  const syncWithServer = async () => {
    if (!token) {
      setStatusMessage('Please provide a bearer token to sync.')
      return
    }

    const payload = {
      station_id: stationId,
      actions: queue,
      timestamp: new Date().toISOString(),
    }

    try {
      const response = await fetch(`${serverUrl}/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(`${response.status} ${text}`)
      }

      const result = await response.json()
      setSyncResult(JSON.stringify(result, null, 2))
      setQueue([])
      setStatusMessage('Sync completed successfully.')
    } catch (error: any) {
      setStatusMessage(`Offline sync failed: ${error.message}`)
    }
  }

  const loadStations = async () => {
    if (!token) {
      setStatusMessage('Please provide a bearer token to load stations.')
      return
    }

    try {
      const response = await fetch(`${serverUrl}/stations`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(`${response.status} ${text}`)
      }

      const data = await response.json()
      setStations(data.stations || [])
      setStatusMessage('Loaded station list from server.')
    } catch (error: any) {
      setStatusMessage(`Failed to load stations: ${error.message}`)
    }
  }

  const showStationDetails = (station_id: string) => {
    const station = stations.find((s) => s.station_id === station_id)
    if (!station) {
      setStationDetails('Selected station not found in loaded list.')
      return
    }

    setStationDetails(
      `Station ${station.station_id} (${station.name})\nLocation: ${station.location}\nPending: ${station.sync_stats.pending}\nCompleted: ${station.sync_stats.completed}\nFailed: ${station.sync_stats.failed}\nQueue utilization: ${station.sync_stats.queue_utilization_percent.toFixed(1)}%`
    )
  }

  return (
    <div className="container">
      <header>
        <h1>RaptorCare Station UI</h1>
        <p>Offline-first station interface with sync queue and remote sync support.</p>
      </header>

      <section>
        <h2>Connection</h2>
        <div className="grid">
          <label>
            Station ID
            <input value={stationId} onChange={(e) => setStationId(e.target.value)} />
          </label>
          <label>
            Server URL
            <input value={serverUrl} onChange={(e) => setServerUrl(e.target.value)} />
          </label>
          <label>
            Bearer Token
            <input value={token} onChange={(e) => setToken(e.target.value)} type="password" />
          </label>
          <button className="primary" onClick={loadStations}>Load stations from server</button>
        </div>
      </section>

      <section>
        <h2>Offline Actions</h2>
        <div className="grid">
          <div className="card">
            <h3>Create Bird Record</h3>
            <label>
              Internal ID
              <input value={birdInternalId} onChange={(e) => setBirdInternalId(e.target.value)} />
            </label>
            <label>
              Species
              <input value={birdSpecies} onChange={(e) => setBirdSpecies(e.target.value)} />
            </label>
            <button onClick={createBird}>Save locally</button>
          </div>

          <div className="card">
            <h3>Record Health Check</h3>
            <label>
              Bird ID
              <input
                type="number"
                value={healthBirdId}
                onChange={(e) => setHealthBirdId(Number(e.target.value))}
              />
            </label>
            <label>
              Weight (g)
              <input
                type="number"
                value={healthWeight}
                onChange={(e) => setHealthWeight(Number(e.target.value))}
              />
            </label>
            <label>
              Behavior
              <input value={healthBehavior} onChange={(e) => setHealthBehavior(e.target.value)} />
            </label>
            <button onClick={recordHealth}>Store health check</button>
          </div>

          <div className="card">
            <h3>Schedule Calendar Event</h3>
            <label>
              Title
              <input value={calendarTitle} onChange={(e) => setCalendarTitle(e.target.value)} />
            </label>
            <label>
              Date
              <input type="date" value={calendarDate} onChange={(e) => setCalendarDate(e.target.value)} />
            </label>
            <label>
              Time
              <input type="time" value={calendarTime} onChange={(e) => setCalendarTime(e.target.value)} />
            </label>
            <label>
              Location
              <input value={calendarLocation} onChange={(e) => setCalendarLocation(e.target.value)} />
            </label>
            <label>
              Notes
              <textarea value={calendarNotes} onChange={(e) => setCalendarNotes(e.target.value)} />
            </label>
            <button onClick={createCalendarEvent}>Add calendar event</button>
          </div>
        </div>
      </section>

      <section>
        <h2>Sync</h2>
        <button className="primary" onClick={syncWithServer}>Sync with server</button>
        <p>Status: {statusMessage}</p>
        <h3>Last server response</h3>
        <pre>{syncResult}</pre>
      </section>

      <section>
        <h2>Pending Queue</h2>
        <p>Items in queue: {queue.length}</p>
        <div className="queue-list">
          {queue.map((item) => (
            <div key={item.id} className="queue-item">
              <strong>{item.entity_type}</strong> · {item.action}
              <pre>{JSON.stringify(item.data, null, 2)}</pre>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Loaded Stations</h2>
        <div className="queue-list">
          {stations.map((station) => (
            <div key={station.station_id} className="queue-item">
              <strong>{station.name}</strong>
              <p>ID: {station.station_id}</p>
              <p>Pending: {station.sync_stats.pending} / Total: {station.sync_stats.total}</p>
              <button onClick={() => showStationDetails(station.station_id)}>Show details</button>
            </div>
          ))}
        </div>
        <pre>{stationDetails}</pre>
      </section>
    </div>
  )
}

export default App
