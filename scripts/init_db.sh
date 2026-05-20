#!/bin/bash
# Setup initial database with admin user

set -e

VENV_PATH=${1:-.}

echo "🗄️  Initializing RaptorCare Database"
echo "===================================="

source $VENV_PATH/venv/bin/activate

# Create tables
echo "Creating database tables..."
python3 << 'EOF'
from server.database import init_db
init_db()
print("✅ Database tables created")
EOF

# Create admin user
echo "Creating admin user..."
python3 << 'EOF'
from server.database import SessionLocal
from server.models import User, UserRole
from server.auth import get_password_hash

db = SessionLocal()

# Check if admin exists
admin = db.query(User).filter(User.username == "admin").first()
if admin:
    print("⚠️  Admin user already exists")
else:
    admin_user = User(
        username="admin",
        email="admin@raptorcare.local",
        full_name="Administrator",
        role=UserRole.ADMIN,
        is_active=True
    )
    admin_user.set_password("changeme123")  # Change this!

    db.add(admin_user)
    db.commit()
    print("✅ Admin user created (username: admin, password: changeme123)")
    print("⚠️  IMPORTANT: Change the admin password immediately!")

db.close()
EOF

echo ""
echo "✅ Database initialization complete!"
echo ""
echo "Admin credentials:"
echo "  Username: admin"
echo "  Password: changeme123"
echo ""
echo "⚠️  Security: Change the admin password in production!"
