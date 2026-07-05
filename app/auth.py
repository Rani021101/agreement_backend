from fastapi import APIRouter
from fastapi import HTTPException
import os
from jose import jwt
from .db import get_connection
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=8)

    to_encode.update(
        {"exp": expire}
    )

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )



class Login(BaseModel):
    emp_id: str
    password: str

@router.post("/login")
def login(data: Login):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT emp_id,name,password
        FROM users
        WHERE emp_id=%s
        """,
        (data.emp_id,)
    )

    user = cur.fetchone()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if user[2] != data.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "emp_id": user[0],
        "name": user[1]
    })

    return {
        "token": token,
        "emp_id": user[0],
        "name": user[1]
    }


from fastapi import Header, HTTPException
from jose import jwt, JWTError

def verify_token(
    authorization: str = Header(None)
):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing token"
        )

    token = authorization.replace(
        "Bearer ",
        ""
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )