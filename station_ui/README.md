# RaptorCare Station UI

Offline-first station interface for data entry and sync.

## Setup

```bash
cd station_ui
npm install
npm run dev
```

## Notes

- Uses local storage to simulate offline queue.
- Sync button posts to the server `/sync` endpoint.
- Intended for use on station hardware with occasional internet connectivity.
