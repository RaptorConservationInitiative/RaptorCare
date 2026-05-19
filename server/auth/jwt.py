from jose import jwt
from datetime import datetime, timedelta

SECRET = "5aa4251a615748b4acdd1ba639953e127ac473415b78594285226cf9bbb20ea2"
ALGORITHM = "HS256"

def create_token(data):

    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=12)

    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def verify_token(token):

    return jwt.decode(
        token,
        SECRET,
        algorithms=[ALGORITHM]
    )
