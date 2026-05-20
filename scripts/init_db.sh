#!/bin/bash
# Database Initialization Script
# Setup PostgreSQL and create admin user

set -e

echo "🗄️  RaptorCare Database Initialization"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if PostgreSQL is running
if ! sudo -u postgres psql -c "SELECT 1" &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL is not running${NC}"
    exit 1
fi

echo -e "${YELLOW}Creating database...${NC}"
sudo -u postgres psql -c "CREATE DATABASE raptorcare_db OWNER raptorcare" 2>/dev/null || echo "Database already exists"

echo -e "${YELLOW}Creating tables...${NC}"

# Create tables using Python
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/raptorcare')

from server.database import init_db
from server.models import User, Bird, HealthRecord, FeedingLog, Station

try:
    init_db()
    print("✅ Database tables created")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF

echo -e "${YELLOW}Creating admin user...${NC}"

# Create admin user
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/raptorcare')

from server.database import SessionLocal
from server.models import User
from passlib.context import CryptContext
from datetime import datetime

db = SessionLocal()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Check if admin exists
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

db.close()
EOF

echo ""
echo -e "${GREEN}✅ Database initialized successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Update admin password: Change 'admin123' in production!"
echo "2. Create additional users as needed"
echo "3. Start the server: sudo systemctl start raptorcare"
echo ""
