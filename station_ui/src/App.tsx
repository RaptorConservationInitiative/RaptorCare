import { useEffect, useState } from 'react'

type QueueItem = {
  id: string
  action: string
  entity_type: string
  data: Record<string, any>
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
  const [birdSpecies, setBirdSpecies] = useState('peregrine_falcon')
  const [healthBirdId, setHealthBirdId] = useState(1)
  const [healthWeight, setHealthWeight] = useState(0)
  const [healthBehavior, setHealthBehavior] = useState('')

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
        status: 'in_treatment',
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
    </div>
  )
}

export default App
