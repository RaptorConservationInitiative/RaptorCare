"""
Synchronization logic for offline-first architecture
Handles queuing, conflict resolution, and bidirectional sync
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from server.models import SyncQueue, Bird, HealthRecord, FeedingLog
from server.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class SyncManager:
    """Manages offline sync queue and bidirectional synchronization"""

    def __init__(self, db: Session):
        self.db = db
        self.max_queue_size = settings.MAX_OFFLINE_QUEUE_SIZE

    # ========================================================================
    # ENQUEUE OPERATIONS
    # ========================================================================

    def enqueue_action(
        self,
        station_id: str,
        action: str,
        entity_type: str,
        entity_data: Dict
    ) -> bool:
        """
        Enqueue a local change for sync

        action: "create", "update", "delete"
        entity_type: "bird", "health_record", "feeding_log", "medication"
        """

        try:
            # Check queue size
            queue_size = self.db.query(SyncQueue).filter(
                SyncQueue.station_id == station_id,
                SyncQueue.sync_status == "pending"
            ).count()

            if queue_size >= self.max_queue_size:
                logger.warning(f"Sync queue full for station {station_id}")
                return False

            # Create queue entry
            queue_entry = SyncQueue(
                station_id=station_id,
                action=action,
                entity_type=entity_type,
                entity_data=json.dumps(entity_data),
                sync_status="pending"
            )

            self.db.add(queue_entry)
            self.db.commit()

            logger.info(f"Enqueued {action} {entity_type} for {station_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to enqueue action: {str(e)}")
            self.db.rollback()
            return False

    # ========================================================================
    # DEQUEUE & SYNC
    # ========================================================================

    def get_pending_actions(
        self,
        station_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get pending sync actions for a station"""

        try:
            pending = self.db.query(SyncQueue).filter(
                SyncQueue.station_id == station_id,
                SyncQueue.sync_status == "pending"
            ).limit(limit).all()

            return [
                {
                    "id": item.id,
                    "action": item.action,
                    "entity_type": item.entity_type,
                    "entity_data": json.loads(item.entity_data),
                    "queued_at": item.queued_at.isoformat()
                }
                for item in pending
            ]

        except Exception as e:
            logger.error(f"Failed to retrieve pending actions: {str(e)}")
            return []

    def mark_synced(self, queue_ids: List[int]) -> bool:
        """Mark actions as successfully synced"""

        try:
            self.db.query(SyncQueue).filter(
                SyncQueue.id.in_(queue_ids)
            ).update(
                {
                    SyncQueue.sync_status: "completed",
                    SyncQueue.synced_at: datetime.utcnow()
                },
                synchronize_session=False
            )
            self.db.commit()

            logger.info(f"Marked {len(queue_ids)} actions as synced")
            return True

        except Exception as e:
            logger.error(f"Failed to mark actions as synced: {str(e)}")
            self.db.rollback()
            return False

    def mark_sync_failed(self, queue_id: int, error: str) -> bool:
        """Mark action as failed sync with error details"""

        try:
            queue_entry = self.db.query(SyncQueue).filter(
                SyncQueue.id == queue_id
            ).first()

            if queue_entry:
                queue_entry.sync_status = "failed"
                # Retry up to 3 times
                retry_count = queue_entry.entity_data.count("\"retry_count\":")
                if retry_count < 3:
                    queue_entry.sync_status = "pending"
                    data = json.loads(queue_entry.entity_data)
                    data["retry_count"] = retry_count + 1
                    queue_entry.entity_data = json.dumps(data)

                self.db.commit()
                logger.warning(f"Marked queue {queue_id} as failed: {error}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to mark action as failed: {str(e)}")
            self.db.rollback()
            return False

    # ========================================================================
    # CONFLICT RESOLUTION
    # ========================================================================

    def detect_conflict(
        self,
        entity_type: str,
        entity_id: int,
        local_timestamp: datetime,
        server_timestamp: datetime
    ) -> bool:
        """Detect if a conflict exists (concurrent modification)"""

        # If server version is newer than local change, there's a conflict
        return server_timestamp > local_timestamp

    def resolve_conflict(
        self,
        entity_type: str,
        entity_id: int,
        local_data: Dict,
        server_data: Dict,
        strategy: str = "server-wins"  # or "client-wins", "merge"
    ) -> Dict:
        """
        Resolve conflicting changes

        Strategies:
        - server-wins: Keep server version
        - client-wins: Keep local version
        - merge: Merge changes (field-level)
        """

        if strategy == "server-wins":
            logger.info(f"Conflict resolved (server-wins) for {entity_type} {entity_id}")
            return server_data

        elif strategy == "client-wins":
            logger.info(f"Conflict resolved (client-wins) for {entity_type} {entity_id}")
            return local_data

        elif strategy == "merge":
            # Merge: prefer non-null/non-empty fields
            merged = server_data.copy()
            for key, value in local_data.items():
                if value is not None and value != "":
                    merged[key] = value
            logger.info(f"Conflict resolved (merge) for {entity_type} {entity_id}")
            return merged

        else:
            logger.warning(f"Unknown conflict resolution strategy: {strategy}")
            return server_data

    # ========================================================================
    # DELTA SYNC (INCREMENTAL)
    # ========================================================================

    def get_delta(
        self,
        station_id: str,
        since: Optional[datetime] = None
    ) -> Dict:
        """
        Get changes since last sync (delta)
        Used to minimize bandwidth for offline clients
        """

        if since is None:
            # Default: last 24 hours
            since = datetime.utcnow() - timedelta(hours=24)

        try:
            changes = {
                "birds": [],
                "health_records": [],
                "feeding_logs": [],
                "timestamp": datetime.utcnow().isoformat()
            }

            # New/updated birds
            birds = self.db.query(Bird).filter(
                Bird.station_id == station_id,
                Bird.updated_at >= since
            ).all()
            changes["birds"] = [
                {
                    "id": b.id,
                    "internal_id": b.internal_id,
                    "status": b.status.value,
                    "updated_at": b.updated_at.isoformat()
                }
                for b in birds
            ]

            # New health records
            health_records = self.db.query(HealthRecord).filter(
                HealthRecord.created_at >= since
            ).all()
            changes["health_records"] = [
                {
                    "id": hr.id,
                    "bird_id": hr.bird_id,
                    "created_at": hr.created_at.isoformat()
                }
                for hr in health_records
            ]

            # New feeding logs
            feeding_logs = self.db.query(FeedingLog).filter(
                FeedingLog.created_at >= since
            ).all()
            changes["feeding_logs"] = [
                {
                    "id": fl.id,
                    "bird_id": fl.bird_id,
                    "created_at": fl.created_at.isoformat()
                }
                for fl in feeding_logs
            ]

            logger.info(f"Generated delta for {station_id} since {since}")
            return changes

        except Exception as e:
            logger.error(f"Failed to generate delta: {str(e)}")
            return {"error": str(e)}

    # ========================================================================
    # CLEANUP
    # ========================================================================

    def cleanup_old_synced(self, days: int = 30) -> int:
        """Remove successfully synced items older than specified days"""

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            deleted = self.db.query(SyncQueue).filter(
                SyncQueue.sync_status == "completed",
                SyncQueue.synced_at < cutoff_date
            ).delete(synchronize_session=False)

            self.db.commit()

            logger.info(f"Cleaned up {deleted} old sync records")
            return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup old records: {str(e)}")
            self.db.rollback()
            return 0

    def get_queue_stats(self, station_id: str) -> Dict:
        """Get sync queue statistics"""

        try:
            total = self.db.query(SyncQueue).filter(
                SyncQueue.station_id == station_id
            ).count()

            pending = self.db.query(SyncQueue).filter(
                SyncQueue.station_id == station_id,
                SyncQueue.sync_status == "pending"
            ).count()

            completed = self.db.query(SyncQueue).filter(
                SyncQueue.station_id == station_id,
                SyncQueue.sync_status == "completed"
            ).count()

            failed = self.db.query(SyncQueue).filter(
                SyncQueue.station_id == station_id,
                SyncQueue.sync_status == "failed"
            ).count()

            return {
                "total": total,
                "pending": pending,
                "completed": completed,
                "failed": failed,
                "queue_utilization_percent": (pending / self.max_queue_size * 100) if self.max_queue_size > 0 else 0
            }

        except Exception as e:
            logger.error(f"Failed to get queue stats: {str(e)}")
            return {}
