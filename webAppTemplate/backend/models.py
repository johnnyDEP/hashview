from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base(cls=AsyncAttrs)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(20), nullable=False)
    last_name = Column(String(20), nullable=False)
    email_address = Column(String(50), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    admin = Column(Boolean, nullable=False, default=False)
    pushover_app_id = Column(String(50))
    pushover_user_key = Column(String(50))
    last_login_utc = Column(DateTime, default=datetime.utcnow)
    api_key = Column(String(60))
    # Relationships (define as needed)

class Agent(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    src_ip = Column(String(15), nullable=False)
    uuid = Column(String(60), nullable=False)
    status = Column(String(20), nullable=False)
    hc_status = Column(Text)
    last_checkin = Column(DateTime)
    benchmark = Column(String(20))
    cpu_count = Column(Integer)
    gpu_count = Column(Integer)

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)

class Hashfile(Base):
    __tablename__ = 'hashfiles'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    runtime = Column(Integer, default=0)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)

class Rule(Base):
    __tablename__ = 'rules'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    path = Column(String(256), nullable=False)
    size = Column(Integer, default=0)
    checksum = Column(String(64), nullable=False)

class Wordlist(Base):
    __tablename__ = 'wordlists'
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String(7))
    path = Column(String(245), nullable=False)
    size = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=False)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    hc_attackmode = Column(String(25), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    wl_id = Column(Integer)
    rule_id = Column(Integer)
    hc_mask = Column(String(50))

class TaskGroup(Base):
    __tablename__ = 'taskgroups'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    tasks = Column(String(256), nullable=False)

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    priority = Column(Integer, nullable=False, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    queued_at = Column(DateTime)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    hashfile_id = Column(Integer, ForeignKey('hashfiles.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)

class JobTask(Base):
    __tablename__ = 'jobtasks'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    priority = Column(Integer, nullable=False, default=3)
    command = Column(String(1024))
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime)
    agent_id = Column(Integer, ForeignKey('agents.id'))

class Hash(Base):
    __tablename__ = 'hashes'
    id = Column(Integer, primary_key=True)
    sub_ciphertext = Column(String(32), nullable=False)
    ciphertext = Column(String(16383), nullable=False)
    hash_type = Column(Integer, nullable=False)
    cracked = Column(Boolean, nullable=False)
    plaintext = Column(String(256))

class HashfileHash(Base):
    __tablename__ = 'hashfilehashes'
    id = Column(Integer, primary_key=True)
    hash_id = Column(Integer, ForeignKey('hashes.id'), nullable=False)
    username = Column(String(256))
    hashfile_id = Column(Integer, ForeignKey('hashfiles.id'), nullable=False)

class JobNotification(Base):
    __tablename__ = 'jobnotifications'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    method = Column(String(6), nullable=False)

class HashNotification(Base):
    __tablename__ = 'hashnotifications'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    hash_id = Column(Integer, ForeignKey('hashes.id'), nullable=False)
    method = Column(String(6), nullable=False)

class Setting(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    retention_period = Column(Integer)
    max_runtime_jobs = Column(Integer)
    max_runtime_tasks = Column(Integer)
    enabled_job_weights = Column(Boolean, default=False) 