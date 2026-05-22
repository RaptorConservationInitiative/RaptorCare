#!/bin/bash
# Database Initialization Script
# Setup PostgreSQL and create admin user

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$REPO_ROOT/venv/bin/python3"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3.12"
fi

echo "🗄️  RaptorCare Database Initialization"
echo "======================================"

echo "Checking PostgreSQL availability..."
if ! sudo -u postgres psql -c "SELECT 1" &> /dev/null; then
    echo "❌ PostgreSQL is not running or not installed"
    exit 1
fi

echo "Creating database if needed..."
sudo -u postgres psql -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'raptorcare_db') THEN
        CREATE DATABASE raptorcare_db OWNER raptorcare;
    END IF;
END$$;
SQL

echo "Creating tables..."

$PYTHON_BIN <<'EOF'
import sys
from pathlib import Path
repo_root = Path("$REPO_ROOT")
sys.path.insert(0, str(repo_root))

from server.database import init_db

try:
    init_db()
    print("✅ Database tables created")
except Exception as e:
    print(f"❌ Error: {e}")
    raise
EOF

echo "Creating admin user..."

$PYTHON_BIN <<'EOF'
import sys
from pathlib import Path
repo_root = Path("$REPO_ROOT")
sys.path.insert(0, str(repo_root))

from server.database import SessionLocal
from server.models import User
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()
try:
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        print("✅ Admin user already exists")
    else:
        admin_user = User(
            username="admin",
            email="admin@raptorcare.local",
            hashed_password=pwd_context.hash("admin123"),
            role="admin",
            is_active=True,
            created_at=datetime.now()
        )
        db.add(admin_user)
        db.commit()
        print("✅ Admin user created (username: admin, password: admin123)")
        print("⚠️  CHANGE THIS PASSWORD IN PRODUCTION!")
finally:
    db.close()
EOF

echo ""
echo "✅ Database initialized successfully!"
echo ""
echo "Next steps:"
echo "1. Update admin password: Change 'admin123' in production!"
echo "2. Create additional users as needed"
echo "3. Start the server with your virtualenv or via systemd" 
