const refreshStatus = document.getElementById('refreshStatus')
const syncButton = document.getElementById('syncButton')
const scanButton = document.getElementById('scanButton')
const statusOutput = document.getElementById('statusOutput')
const scanOutput = document.getElementById('scanOutput')
const serverUrlInput = document.getElementById('serverUrl')
const tokenInput = document.getElementById('token')

refreshStatus.addEventListener('click', async () => {
  const serverUrl = serverUrlInput.value.trim()
  try {
    const response = await fetch(`${serverUrl}/health`)
    const data = await response.json()
    statusOutput.textContent = JSON.stringify(data, null, 2)
  } catch (err) {
    statusOutput.textContent = `Unable to reach server: ${err}`
  }
})

syncButton.addEventListener('click', () => {
  alert('Sync logic is available in the full station app; this is a mobile placeholder.')
})

scanButton.addEventListener('click', () => {
  scanOutput.textContent = 'QR/RFID scan placeholder: use the station web UI for now.'
})

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').then(
      () => console.log('Service worker registered'),
      (err) => console.error('Service worker failed', err)
    )
  })
}
