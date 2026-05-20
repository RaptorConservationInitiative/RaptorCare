import { useState } from 'react'

type GPUInfo = {
  device_id: number
  name: string
  total_memory_gb: number
  used_memory_gb: number
  free_memory_gb: number
  utilization_percent: number
}

type ResearchOutput = {
  research_text: string
  gpu_used?: number
  model?: string
}

function App() {
  const [serverUrl, setServerUrl] = useState('http://localhost:8000')
  const [token, setToken] = useState('')
  const [stationId, setStationId] = useState('station_001')
  const [gpuStatus, setGpuStatus] = useState<GPUInfo[] | null>(null)
  const [researchResponse, setResearchResponse] = useState<string>('')
  const [researchGoal, setResearchGoal] = useState('Summarize this case and provide research questions.')
  const [researchNotes, setResearchNotes] = useState('')
  const [selectedStation, setSelectedStation] = useState('station_001')
  const [stationData, setStationData] = useState('No station data loaded yet.')

  const headers = token
    ? {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    : { 'Content-Type': 'application/json' }

  const fetchGpuStatus = async () => {
    try {
      const response = await fetch(`${serverUrl}/research/gpu-status`, {
        headers,
      })
      const data = await response.json()
      setGpuStatus(data.gpus || [])
    } catch (error) {
      setGpuStatus(null)
      setResearchResponse(`GPU status fetch failed: ${error}`)
    }
  }

  const requestResearch = async (endpoint: string) => {
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
    const data: ResearchOutput = await response.json()
    setResearchResponse(data.research_text)
  }

  const loadStationData = () => {
    setStationData(`Station ${selectedStation} data is not available in this prototype.`)
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
        </div>
      </section>

      <section>
        <h2>Station Overview</h2>
        <div className="grid">
          <label>
            Select station
            <select value={selectedStation} onChange={(e) => setSelectedStation(e.target.value)}>
              <option value="station_001">station_001</option>
              <option value="station_002">station_002</option>
              <option value="station_003">station_003</option>
            </select>
          </label>
          <button className="primary" onClick={loadStationData}>Load station data</button>
        </div>
        <pre>{stationData}</pre>
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
