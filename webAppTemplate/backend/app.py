from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from models import Base  # Use absolute import for models.py
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException, status, Depends, Path
from models import User
from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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

# --- Database Config ---
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "appdb")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- Pydantic Schemas ---
class UserCreate(BaseModel):
    first_name: str = Field(..., max_length=20)
    last_name: str = Field(..., max_length=20)
    email_address: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email_address: EmailStr
    admin: bool
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    admin: bool | None = None

class AgentRead(BaseModel):
    id: int
    name: str
    status: str
    last_checkin: datetime | None
    class Config:
        from_attributes = True

class CustomerRead(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class TaskSummary(BaseModel):
    id: int
    name: str | None
    status: str
    agent_id: int | None
    recovered: int | None = None
    rate: float | None = None
    est: float | None = None
    control: bool | None = None
    class Config:
        from_attributes = True

class JobRead(BaseModel):
    id: int
    name: str
    status: str
    customer_id: int
    owner_id: int
    tasks: list[TaskSummary]
    class Config:
        from_attributes = True

class AnalyticsRead(BaseModel):
    status: int
    labels: list[str]
    values: list[int]

class TaskRead(BaseModel):
    id: int
    name: str
    hc_attackmode: str
    owner_id: int
    wl_id: int | None = None
    wl_id_2: int | None = None
    j_rule: str | None = None
    k_rule: str | None = None
    rule_id: int | None = None
    hc_mask: str | None = None
    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    name: str
    hc_attackmode: str
    wl_id: int | None = None
    wl_id_2: int | None = None
    j_rule: str | None = None
    k_rule: str | None = None
    rule_id: int | None = None
    hc_mask: str | None = None

class TaskGroupRead(BaseModel):
    id: int
    name: str
    owner_id: int
    tasks: list[int]
    class Config:
        from_attributes = True

class TaskGroupUpdate(BaseModel):
    tasks: list[int]

class WordlistRead(BaseModel):
    id: int
    name: str
    last_updated: datetime
    owner_id: int
    type: str | None = None
    path: str
    size: int
    checksum: str
    class Config:
        from_attributes = True

class RuleRead(BaseModel):
    id: int
    name: str
    last_updated: datetime
    owner_id: int
    path: str
    size: int
    checksum: str
    class Config:
        from_attributes = True

# --- Register User ---
@app.post("/api/register", response_model=UserRead)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    # Check if users table is empty
    result = await db.execute(select(User))
    users = result.scalars().all()
    is_first_user = len(users) == 0

    # If not first user, require authentication and admin
    if not is_first_user:
        token = None
        if request and "authorization" in request.headers:
            auth_header = request.headers["authorization"]
            if auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1]
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        current_user = await get_current_user_db(db, token)
        if not current_user.admin:
            raise HTTPException(status_code=403, detail="Only admins can register new users.")

    # Check for existing email
    result = await db.execute(select(User).where(User.email_address == user.email_address))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = get_password_hash(user.password)
    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email_address=user.email_address,
        password=hashed_pw,
        admin=is_first_user  # First user is admin, others are not by default
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# --- Login User (JWT) ---
@app.post("/api/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email_address == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

# --- Auth Dependency ---
async def get_current_user_db(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

# --- List Users ---
@app.get("/api/users", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

# --- Get User by ID ---
@app.get("/api/users/{user_id}", response_model=UserRead)
async def get_user(user_id: int = Path(..., gt=0), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# --- Update User ---
@app.put("/api/users/{user_id}", response_model=UserRead)
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    if user_update.last_name is not None:
        user.last_name = user_update.last_name
    if user_update.password is not None:
        user.password = get_password_hash(user_update.password)
    if user_update.admin is not None:
        user.admin = user_update.admin
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# --- Delete User ---
@app.delete("/api/users/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return None

# --- AGENTS ENDPOINT ---
@app.get("/api/agents", response_model=list[AgentRead])
async def list_agents(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    from models import Agent
    result = await db.execute(select(Agent))
    agents = result.scalars().all()
    return [
        AgentRead(
            id=a.id,
            name=a.name,
            status=a.status,
            last_checkin=a.last_checkin
        ) for a in agents
    ]

# --- CUSTOMERS ENDPOINT ---
@app.get("/api/customers", response_model=list[CustomerRead])
async def list_customers(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    from models import Customer
    result = await db.execute(select(Customer))
    customers = result.scalars().all()
    return [CustomerRead(id=c.id, name=c.name) for c in customers]

# --- JOBS ENDPOINT ---
@app.get("/api/jobs", response_model=list[JobRead])
async def list_jobs(status: str = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    from models import Job, JobTask, Task
    query = select(Job)
    if status:
        query = query.where(Job.status == status.capitalize())
    result = await db.execute(query)
    jobs = result.scalars().all()
    job_list = []
    for job in jobs:
        # Get job tasks
        task_result = await db.execute(select(JobTask).where(JobTask.job_id == job.id))
        job_tasks = task_result.scalars().all()
        tasks = []
        for jt in job_tasks:
            # Get task name
            task_name = None
            if jt.task_id:
                t_result = await db.execute(select(Task).where(Task.id == jt.task_id))
                t = t_result.scalar_one_or_none()
                if t:
                    task_name = t.name
            tasks.append(TaskSummary(
                id=jt.id,
                name=task_name,
                status=jt.status,
                agent_id=jt.agent_id,
                recovered=None,  # Extend if you add this field
                rate=None,
                est=None,
                control=(jt.status == 'Running')
            ))
        job_list.append(JobRead(
            id=job.id,
            name=job.name,
            status=job.status,
            customer_id=job.customer_id,
            owner_id=job.owner_id,
            tasks=tasks
        ))
    return job_list

# --- ANALYTICS ENDPOINT (dashboard cracked hashes per day) ---
@app.get("/api/analytics", response_model=AnalyticsRead)
async def dashboard_analytics(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    from models import Hash
    from sqlalchemy import func
    days = 7
    labels = []
    values = []
    now = datetime.utcnow()
    for i in range(days-1, -1, -1):
        day_start = now - timedelta(days=i)
        day_start = day_start.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)
        label = day_start.strftime('%a')
        count_result = await db.execute(
            select(func.count()).select_from(Hash).where(
                Hash.cracked == True,
                Hash.recovered_at >= day_start,
                Hash.recovered_at <= day_end
            )
        )
        count = count_result.scalar_one()
        labels.append(label)
        values.append(count)
    return AnalyticsRead(status=200, labels=labels, values=values)

# --- TASKS ENDPOINT ---
@app.get("/api/tasks", response_model=list[TaskRead])
async def list_tasks(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    from models import Task
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    return [TaskRead.from_orm(t) for t in tasks]

@app.post("/api/tasks", response_model=TaskRead)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    # Only allow owner or admin
    if not current_user.admin and current_user.id != task.owner_id:
        raise HTTPException(status_code=403, detail="Not authorized to create task for this owner.")

    # Validate attack mode and required fields
    mode = str(task.hc_attackmode)
    if mode == '0':  # Straight (Wordlist + Rules)
        if not task.wl_id or not task.name:
            raise HTTPException(status_code=400, detail="Wordlist and name required for attack mode 0.")
    elif mode == '1':  # Combinator
        if not task.wl_id or not task.wl_id_2 or not task.name:
            raise HTTPException(status_code=400, detail="Wordlist, second wordlist, and name required for attack mode 1.")
    elif mode == '3':  # Mask
        if not task.hc_mask or not task.name:
            raise HTTPException(status_code=400, detail="Mask and name required for attack mode 3.")
    elif mode in ['6', '7']:  # Hybrid
        if not task.wl_id or not task.hc_mask or not task.name:
            raise HTTPException(status_code=400, detail="Wordlist, mask, and name required for attack mode 6/7.")
    else:
        raise HTTPException(status_code=400, detail="Unsupported attack mode.")

    from models import Task
    db_task = Task(
        name=task.name,
        hc_attackmode=task.hc_attackmode,
        owner_id=current_user.id,
        wl_id=task.wl_id,
        wl_id_2=task.wl_id_2,
        j_rule=task.j_rule,
        k_rule=task.k_rule,
        rule_id=task.rule_id,
        hc_mask=task.hc_mask
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return TaskRead.from_orm(db_task)

@app.put("/api/tasks/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    from models import Task
    result = await db.execute(select(Task).where(Task.id == task_id))
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not (current_user.admin or current_user.id == db_task.owner_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
    # Validate attack mode and required fields
    mode = str(task.hc_attackmode)
    if mode == '0':  # Straight (Wordlist + Rules)
        if not task.wl_id or not task.name:
            raise HTTPException(status_code=400, detail="Wordlist and name required for attack mode 0.")
    elif mode == '1':  # Combinator
        if not task.wl_id or not task.wl_id_2 or not task.name:
            raise HTTPException(status_code=400, detail="Wordlist, second wordlist, and name required for attack mode 1.")
    elif mode == '3':  # Mask
        if not task.hc_mask or not task.name:
            raise HTTPException(status_code=400, detail="Mask and name required for attack mode 3.")
    elif mode in ['6', '7']:  # Hybrid
        if not task.wl_id or not task.hc_mask or not task.name:
            raise HTTPException(status_code=400, detail="Wordlist, mask, and name required for attack mode 6/7.")
    else:
        raise HTTPException(status_code=400, detail="Unsupported attack mode.")
    # Update fields
    db_task.name = task.name
    db_task.hc_attackmode = task.hc_attackmode
    db_task.wl_id = task.wl_id
    db_task.wl_id_2 = task.wl_id_2
    db_task.j_rule = task.j_rule
    db_task.k_rule = task.k_rule
    db_task.rule_id = task.rule_id
    db_task.hc_mask = task.hc_mask
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return TaskRead.from_orm(db_task)

@app.get("/api/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    from models import Task
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskRead.from_orm(task)

@app.delete("/api/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    from models import Task, JobTask, TaskGroup
    # Find the task
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not (current_user.admin or current_user.id == task.owner_id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")
    # Prevent deletion if assigned to any job
    jobtask_result = await db.execute(select(JobTask).where(JobTask.task_id == task_id))
    if jobtask_result.scalars().first():
        raise HTTPException(status_code=400, detail="Cannot delete: Task is assigned to a job")
    # Prevent deletion if assigned to any task group
    group_result = await db.execute(select(TaskGroup))
    for group in group_result.scalars().all():
        if group.tasks and str(task_id) in [tid.strip() for tid in group.tasks.split(',')]:
            raise HTTPException(status_code=400, detail="Cannot delete: Task is assigned to a task group")
    await db.delete(task)
    await db.commit()
    return None

@app.get("/api/task-groups", response_model=list[TaskGroupRead])
async def list_task_groups(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    from models import TaskGroup
    result = await db.execute(select(TaskGroup))
    groups = result.scalars().all()
    def parse_tasks(tasks_str):
        if not tasks_str:
            return []
        return [int(t) for t in tasks_str.split(',') if t.strip().isdigit()]
    return [TaskGroupRead(
        id=g.id,
        name=g.name,
        owner_id=g.owner_id,
        tasks=parse_tasks(g.tasks)
    ) for g in groups]

@app.put("/api/task-groups/{group_id}", response_model=TaskGroupRead)
async def update_task_group(
    group_id: int,
    update: TaskGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_db)
):
    from models import TaskGroup
    result = await db.execute(select(TaskGroup).where(TaskGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Task group not found")
    if not (current_user.admin or current_user.id == group.owner_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this group")
    # Update tasks as comma-separated string
    group.tasks = ','.join(str(tid) for tid in update.tasks)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    def parse_tasks(tasks_str):
        if not tasks_str:
            return []
        return [int(t) for t in tasks_str.split(',') if t.strip().isdigit()]
    return TaskGroupRead(
        id=group.id,
        name=group.name,
        owner_id=group.owner_id,
        tasks=parse_tasks(group.tasks)
    )

@app.get("/api/wordlists", response_model=list[WordlistRead])
async def list_wordlists(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    from models import Wordlist
    result = await db.execute(select(Wordlist))
    wordlists = result.scalars().all()
    return [WordlistRead.from_orm(w) for w in wordlists]

@app.get("/api/rules", response_model=list[RuleRead])
async def list_rules(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    from models import Rule
    result = await db.execute(select(Rule))
    rules = result.scalars().all()
    return [RuleRead.from_orm(r) for r in rules]

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