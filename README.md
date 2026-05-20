# RaptorCare 🦅
## Wildlife Rescue Station Management Platform

**Status**: 🚀 In Active Development  
**Version**: 0.1.0  
**Python**: 3.9+

---

## 🎯 Project Overview

**RaptorCare** is a comprehensive, offline-first management platform for wildlife rescue and rehabilitation stations, specifically designed for raptors (birds of prey). The system combines local client applications with a centralized server, LLM-powered AI recommendations, and full audit logging.

### Key Features

- ✅ **Offline-First Architecture**: Works offline on tablets/stations, syncs when connected
- 🤖 **AI-Powered Recommendations**: Ollama-based LLM for care and rehabilitation guidance
- 🗄️ **Patient Management**: Complete bird records with health tracking
- 📊 **Data Analytics**: Weight trends, recovery prognosis, anomaly detection
- 🔄 **Multi-Station Support**: Sync between multiple rescue centers
- 👥 **Role-Based Access**: Admin, Caretaker, Veterinarian, Researcher roles
- 🔐 **JWT Authentication**: Secure token-based auth
- 📱 **Mobile PWA**: Responsive web app for field use
- 🌍 **GIS Integration**: Location tracking for rescue data

---

## 📋 Core Modules

### 1. **Patient Management**
- Bird identification (internal ID, ring number, tag ID)
- Species, gender, age tracking
- Admission and release management
- Multi-status workflow (in treatment → ready for release → released/deceased)

### 2. **Medical Records**
- Daily health check entries
- Weight tracking and trends
- Medication management with dosage
- Parasite detection and lab results
- Injury documentation

### 3. **Feeding & Nutrition**
- Feeding logs with type, amount, time
- Appetite tracking
- Assisted feeding documentation

### 4. **AI & LLM Integration**
- Care recommendations from local Ollama LLM
- Rehabilitation prognosis prediction
- Health anomaly detection
- Weight trend analysis

### 5. **Documentation**
- Media uploads (photos, X-rays, PDFs)
- Timeline events (admission, surgery, release, death)
- Audit logging of all changes

### 6. **Synchronization**
- Offline queue management
- Conflict resolution (server-wins, client-wins, merge)
- Delta sync to minimize bandwidth
- Retry logic for failed syncs

---

## 🖥️ User Interfaces

- `station_ui/` — Offline-capable station app for data entry, local queueing and sync with the central server.
- `server_ui/` — Central dashboard for reviewing data from all stations, GPU status and research/LLM tools.

---

## 🏗️ Architecture
┌──────────────────��──────────────────────────────────────────┐ │ RaptorCare Ecosystem │ └─────────────────────────────────────────────────────────────┘

Station Clients (Offline-First) Central Server ┌──────────────────┐ ┌──────────────────┐ │ React Frontend │ │ FastAPI │ │ (PWA/Tablet) │ │ PostgreSQL │ │ │◄────Sync (REST)─────►│ Ollama LLM │ │ SQLite Cache │ │ GPU Inference │ │ Offline Queue │ │ │ └──────────────────┘ └──────────────────┘ │ │ └────────Auth & Data Exchange───────────┘ (JWT + HTTPS)


---

## 🔧 Tech Stack

### Backend
- **FastAPI**: Modern, async Python web framework
- **SQLAlchemy**: ORM for database management
- **PostgreSQL**: Central database
- **Ollama**: Local LLM inference engine
- **LangChain**: LLM orchestration
- **Python-jose**: JWT token management

### Frontend
- **React**: UI component library
- **Vite**: Build tooling
- **TanStack Query**: Server state management
- **WatermelonDB/PouchDB**: Local sync database

### DevOps
- **Proxmox**: Hypervisor (your setup)
- **LXC Containers**: Station hosts with GPU passthrough
- **Supervisor**: Process management
- **Docker**: Containerization (optional)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Node.js 16+
- Ollama (for LLM)
- GPU (T600 or GTX 1650 recommended)

### Server Setup

```bash
# 1. Clone repo
git clone https://github.com/RaptorConservationInitiative/RaptorCare.git
cd RaptorCare

# 2. Create venv
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Edit database URL, secret key, etc.

# 5. Initialize database
bash scripts/init_db.sh

# 6. Start server
uvicorn server.main:app --reload

### LLM Setup (Optional but Recommended)

# Install Ollama
bash scripts/setup_ollama.sh

# Start Ollama service
ollama serve

### Station Client Setup

cd station
npm install
npm run dev

📚 API Endpoints
Authentication

    POST /token - Get JWT access token
    GET /health - Health check

Patients (Birds)

    POST /birds - Create patient
    GET /birds - List all patients
    GET /birds/{bird_id} - Get patient details
    PATCH /birds/{bird_id} - Update patient

Health Records

    POST /birds/{bird_id}/health-records - Create daily check
    GET /birds/{bird_id}/health-records - Get history

Feeding Logs

    POST /birds/{bird_id}/feeding-logs - Log feeding
    GET /birds/{bird_id}/feeding-logs - Get feeding history

AI & LLM

    POST /ai/recommendations/{bird_id} - Get care recommendations
    POST /ai/prognosis/{bird_id} - Get rehabilitation prognosis

Sync

    POST /sync - Upload offline changes
    GET /sync/delta - Get server changes since last sync

🔐 Security

    ✅ JWT token-based authentication (HS256)
    ✅ bcrypt password hashing
    ✅ CORS middleware configured
    ✅ Role-based access control (RBAC)
    ✅ Audit logging of all database changes
    ⚠️ TODO: Rate limiting, CSRF protection, SSL/TLS enforcement

🐛 Known Issues & TODOs
High Priority

    Fix JWT token verification (currently missing token error)
    Implement actual bird CRUD operations
    Add health record creation/retrieval
    Complete sync endpoint implementation

Medium Priority

    Frontend React app
    Media/file upload handling
    GIS/map integration
    Statistical reporting

Low Priority

    Mobile app (native iOS/Android)
    RFID/QR code scanning
    Advanced LLM fine-tuning
    Multi-language support

    📖 Database Schema

See server/models.py for complete schema definition. Key tables:
Code

users
├── bird
│   ├── health_records
│   ├── feeding_logs
│   ├── medications
│   ├── media
│   └── timeline_events
├── stations
│   └── enclosures
├── audit_logs
└── sync_queue

🤝 Contributing

This is an active development project. Areas for contribution:

    Frontend Development: React/Vite UI
    Database Migration: Alembic migrations
    Testing: Unit & integration tests
    Documentation: README improvements
    DevOps: Docker/K8s setup

�� Support & Documentation

    Issues: GitHub Issues for bug reports
    Discussions: GitHub Discussions for feature ideas
    Email: (contact info TBD)

📄 License

(License to be determined)

🙏 Acknowledgments

Built for raptor conservation and wildlife rehabilitation excellence.

Last Updated: 2026-05-20
