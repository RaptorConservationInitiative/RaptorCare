# RaptorCare Server UI

Central dashboard for station monitoring, research tools, and GPU status.

## Setup

```bash
cd server_ui
npm install
npm run dev
```

## Notes

- Uses the server's research endpoints to query GPU status and LLM research tools.
- Token-based auth is supported via Bearer token input.
- This is a prototype UI for central management and research workflows.
