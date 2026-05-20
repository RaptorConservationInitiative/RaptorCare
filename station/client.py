"""
RaptorCare Station Client - Local Application with Offline Sync
"""

import sqlite3
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StationClient:
    """Local station client with offline-first capability"""

    def __init__(self, station_id: str, server_url: str = "http://localhost:8000"):
        self.station_id = station_id
        self.server_url = server_url
        self.db_path = f"/var/lib/raptorcare/station_{station_id}.db"
        self.init_local_db()

    def init_local_db(self):
        """Initialize SQLite database for offline cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Local cache tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS birds (
                id INTEGER PRIMARY KEY,
                internal_id TEXT UNIQUE,
                species TEXT,
                status TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY,
                bird_id INTEGER,
                weight_grams REAL,
                behavior TEXT,
                recorded_at TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                station_id TEXT NOT NULL,
                bird_id INTEGER,
                description TEXT,
                start_at TIMESTAMP NOT NULL,
                end_at TIMESTAMP,
                all_day INTEGER DEFAULT 0,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                entity_type TEXT,
                entity_data TEXT,
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"✅ Local database initialized: {self.db_path}")

    def create_bird_local(self, bird_data: Dict) -> bool:
        """Create bird record locally (offline)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO birds (internal_id, species, status)
                VALUES (?, ?, ?)
            """, (
                bird_data.get("internal_id"),
                bird_data.get("species"),
                "in_treatment"
            ))

            # Queue for sync
            cursor.execute("""
                INSERT INTO sync_queue (action, entity_type, entity_data)
                VALUES (?, ?, ?)
            """, (
                "create",
                "bird",
                json.dumps(bird_data)
            ))

            conn.commit()
            conn.close()

            logger.info(f"✅ Bird {bird_data.get('internal_id')} created locally and queued for sync")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create bird locally: {str(e)}")
            return False

    def record_health_check(self, bird_id: int, health_data: Dict) -> bool:
        """Record daily health check (offline)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO health_records (bird_id, weight_grams, behavior, recorded_at)
                VALUES (?, ?, ?, ?)
            """, (
                bird_id,
                health_data.get("weight_grams"),
                health_data.get("behavior"),
                datetime.now().isoformat()
            ))

            # Queue for sync
            cursor.execute("""
                INSERT INTO sync_queue (action, entity_type, entity_data)
                VALUES (?, ?, ?)
            """, (
                "create",
                "health_record",
                json.dumps({
                    "bird_id": bird_id,
                    **health_data
                })
            ))

            conn.commit()
            conn.close()

            logger.info(f"✅ Health check recorded for bird {bird_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to record health check: {str(e)}")
            return False

    def create_calendar_event_local(self, event_data: Dict) -> bool:
        """Create a local calendar event and queue it for sync."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO calendar_events (
                    title, station_id, bird_id, description, start_at, end_at, all_day, location
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data.get("title"),
                self.station_id,
                event_data.get("bird_id"),
                event_data.get("description"),
                event_data.get("start_at"),
                event_data.get("end_at"),
                1 if event_data.get("all_day") else 0,
                event_data.get("location"),
            ))

            cursor.execute("""
                INSERT INTO sync_queue (action, entity_type, entity_data)
                VALUES (?, ?, ?)
            """, (
                "create",
                "calendar_event",
                json.dumps(event_data)
            ))

            conn.commit()
            conn.close()

            logger.info(f"✅ Calendar event '{event_data.get('title')}' created locally")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create calendar event locally: {str(e)}")
            return False

    def sync_with_server(self, token: str) -> Dict:
        """Sync offline queue with server"""
        try:
            # Get pending sync items
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, action, entity_type, entity_data
                FROM sync_queue
                WHERE synced = 0
            """)

            pending = cursor.fetchall()
            conn.close()

            if not pending:
                logger.info("No pending items to sync")
                return {"success": True, "synced_count": 0}

            # Prepare sync payload
            actions = [
                {
                    "id": p[0],
                    "action": p[1],
                    "entity_type": p[2],
                    "data": json.loads(p[3])
                }
                for p in pending
            ]

            payload = {
                "station_id": self.station_id,
                "actions": actions,
                "timestamp": datetime.now().isoformat()
            }

            # Send to server
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(
                f"{self.server_url}/sync",
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                # Mark as synced
                synced_ids = [p[0] for p in pending]
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(f"""
                    UPDATE sync_queue
                    SET synced = 1
                    WHERE id IN ({','.join('?' * len(synced_ids))})
                """, synced_ids)

                conn.commit()
                conn.close()

                logger.info(f"✅ Synced {len(synced_ids)} items with server")
                return {
                    "success": True,
                    "synced_count": len(synced_ids),
                    "server_response": result
                }
            else:
                logger.error(f"❌ Sync failed: {response.status_code}")
                return {"success": False, "error": response.text}

        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️  Server unreachable (offline mode): {str(e)}")
            return {"success": False, "error": "Server unreachable", "offline": True}
        except Exception as e:
            logger.error(f"❌ Sync error: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_pending_syncs(self) -> List[Dict]:
        """Get list of pending items waiting to sync"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, action, entity_type, queued_at
                FROM sync_queue
                WHERE synced = 0
            """)

            pending = cursor.fetchall()
            conn.close()

            return [
                {
                    "id": p[0],
                    "action": p[1],
                    "entity_type": p[2],
                    "queued_at": p[3]
                }
                for p in pending
            ]

        except Exception as e:
            logger.error(f"Failed to get pending syncs: {str(e)}")
            return []

# Example usage
if __name__ == "__main__":
    client = StationClient("station_001")

    # Offline: Create bird
    client.create_bird_local({
        "internal_id": "WF-2026-001",
        "species": "peregrine_falcon",
        "estimated_age": "juvenile"
    })

    # Offline: Record health
    client.record_health_check(1, {
        "weight_grams": 850,
        "behavior": "Alert, good appetite"
    })

    # Check pending
    pending = client.get_pending_syncs()
    print(f"Pending syncs: {len(pending)}")

    # When online: Sync with server
    # result = client.sync_with_server("your_jwt_token")
    # print(result)
