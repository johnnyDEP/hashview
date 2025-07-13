from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import List, Optional
from datetime import datetime, timedelta

app = FastAPI(title="Generic Backend API")

# --- JWT Config ---
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# --- In-memory user store (placeholder) ---
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "hashed_password": pwd_context.hash("adminpass"),
        "disabled": False,
    }
}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

# --- User Management Endpoints ---
@app.post("/api/register")
def register_user(form: OAuth2PasswordRequestForm = Depends()):
    if form.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = {
        "username": form.username,
        "full_name": form.username.title(),
        "hashed_password": get_password_hash(form.password),
        "disabled": False,
    }
    fake_users_db[form.username] = user
    return {"msg": "User registered"}

@app.post("/api/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users", response_model=List[str])
def list_users(current_user: dict = Depends(get_current_user)):
    return list(fake_users_db.keys())

# --- Placeholder Data Endpoints ---
@app.get("/api/entity")
def get_entity():
    return {"message": "This is a generic entity endpoint."}

@app.get("/api/files")
def get_files(current_user: dict = Depends(get_current_user)):
    return [
        {"id": "file1", "name": "example.docx", "status": "processed", "uploaded": "2024-07-01"},
        {"id": "file2", "name": "report.pdf", "status": "pending", "uploaded": "2024-07-02"},
    ]

@app.get("/api/analytics")
def get_analytics(current_user: dict = Depends(get_current_user)):
    return {
        "total_files": 2,
        "processed": 1,
        "pending": 1,
        "last_run": "2024-07-02T12:00:00Z"
    }

@app.get("/api/system_status")
def get_system_status(current_user: dict = Depends(get_current_user)):
    return {
        "status": "ok",
        "services": [
            {"name": "backend", "status": "running"},
            {"name": "frontend", "status": "running"},
            {"name": "rabbitmq", "status": "running"},
            {"name": "postgres", "status": "running"},
            {"name": "elasticsearch", "status": "running"},
        ],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# TODO: Integrate protobuf models defined in proto_definitions.proto 