import asyncio
from app import engine, AsyncSessionLocal
from models import User, Agent, Customer, Hashfile, Rule, Wordlist, Task, TaskGroup, Job, JobTask, Hash, HashfileHash, JobNotification, HashNotification, Setting
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from datetime import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_or_create(session, model, defaults=None, **kwargs):
    result = await session.execute(select(model).filter_by(**kwargs))
    instance = result.scalar_one_or_none()
    if instance:
        return instance, False
    params = dict(kwargs)
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    return instance, True

async def main():
    async with AsyncSessionLocal() as session:
        # Users
        admin_pw = get_password_hash('adminpassword')
        admin, _ = await get_or_create(session, User, defaults={
            'first_name': 'Admin',
            'last_name': 'User',
            'password': admin_pw,
            'admin': True,
            'email_address': 'admin@example.com'
        }, email_address='admin@example.com')

        user_pw = get_password_hash('userpassword')
        user, _ = await get_or_create(session, User, defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'password': user_pw,
            'admin': False,
            'email_address': 'user@example.com'
        }, email_address='user@example.com')

        # Customers
        customer, _ = await get_or_create(session, Customer, name='Test Customer')

        # Agents
        agent, _ = await get_or_create(session, Agent, defaults={
            'name': 'Agent1',
            'src_ip': '127.0.0.1',
            'uuid': 'agent-uuid-1',
            'status': 'Idle',
            'hc_status': '{}',
            'last_checkin': datetime.utcnow(),
            'benchmark': 'N/A',
            'cpu_count': 4,
            'gpu_count': 1
        }, name='Agent1')

        # Settings
        settings, _ = await get_or_create(session, Setting, defaults={
            'retention_period': 30,
            'max_runtime_jobs': 24,
            'max_runtime_tasks': 12,
            'enabled_job_weights': True
        }, id=1)

        # Wordlists
        wordlist, _ = await get_or_create(session, Wordlist, defaults={
            'name': 'rockyou.txt',
            'last_updated': datetime.utcnow(),
            'owner_id': admin.id,
            'type': 'static',
            'path': '/wordlists/rockyou.txt',
            'size': 1000000,
            'checksum': 'abc123'
        }, name='rockyou.txt')

        # Rules
        rule, _ = await get_or_create(session, Rule, defaults={
            'name': 'best64.rule',
            'last_updated': datetime.utcnow(),
            'owner_id': admin.id,
            'path': '/rules/best64.rule',
            'size': 1024,
            'checksum': 'def456'
        }, name='best64.rule')

        # Hashfiles
        hashfile, _ = await get_or_create(session, Hashfile, defaults={
            'name': 'test_hashfile.txt',
            'uploaded_at': datetime.utcnow(),
            'runtime': 0,
            'customer_id': customer.id,
            'owner_id': admin.id
        }, name='test_hashfile.txt')

        # Hashes
        hash_entry, _ = await get_or_create(session, Hash, defaults={
            'sub_ciphertext': 'subhash1',
            'ciphertext': 'hash1',
            'hash_type': 0,
            'cracked': False,
            'plaintext': None
        }, sub_ciphertext='subhash1')

        # HashfileHashes
        hashfilehash, _ = await get_or_create(session, HashfileHash, defaults={
            'hash_id': hash_entry.id,
            'username': 'testuser',
            'hashfile_id': hashfile.id
        }, hash_id=hash_entry.id, hashfile_id=hashfile.id)

        # Tasks
        task, _ = await get_or_create(session, Task, defaults={
            'name': 'Test Task',
            'hc_attackmode': '0',
            'owner_id': admin.id,
            'wl_id': None,
            'rule_id': rule.id,
            'hc_mask': None
        }, name='Test Task')

        # TaskGroups
        taskgroup, _ = await get_or_create(session, TaskGroup, defaults={
            'name': 'Test Group',
            'owner_id': admin.id,
            'tasks': str(task.id)
        }, name='Test Group')

        # Jobs
        job, _ = await get_or_create(session, Job, defaults={
            'name': 'Test Job',
            'priority': 3,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'queued_at': None,
            'status': 'Queued',
            'started_at': None,
            'ended_at': None,
            'hashfile_id': hashfile.id,
            'customer_id': customer.id,
            'owner_id': admin.id
        }, name='Test Job')

        # JobTasks
        jobtask, _ = await get_or_create(session, JobTask, defaults={
            'job_id': job.id,
            'task_id': task.id,
            'priority': 3,
            'command': 'hashcat ...',
            'status': 'Not Started',
            'started_at': None,
            'agent_id': agent.id
        }, job_id=job.id, task_id=task.id)

        # HashNotifications
        hashnotif, _ = await get_or_create(session, HashNotification, defaults={
            'owner_id': admin.id,
            'hash_id': hash_entry.id,
            'method': 'email'
        }, owner_id=admin.id, hash_id=hash_entry.id)

        # --- Additional Sample Data for Dashboard Testing ---
        # Add a running job
        running_job, _ = await get_or_create(session, Job, defaults={
            'name': 'Running Job',
            'priority': 2,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'queued_at': datetime.utcnow(),
            'status': 'Running',
            'started_at': datetime.utcnow(),
            'ended_at': None,
            'hashfile_id': hashfile.id,
            'customer_id': customer.id,
            'owner_id': admin.id
        }, name='Running Job')

        # Add job tasks for running job
        running_task, _ = await get_or_create(session, Task, defaults={
            'name': 'Running Task',
            'hc_attackmode': '0',
            'owner_id': admin.id,
            'wl_id': wordlist.id,
            'rule_id': rule.id,
            'hc_mask': None
        }, name='Running Task')
        completed_task, _ = await get_or_create(session, Task, defaults={
            'name': 'Completed Task',
            'hc_attackmode': '0',
            'owner_id': admin.id,
            'wl_id': wordlist.id,
            'rule_id': rule.id,
            'hc_mask': None
        }, name='Completed Task')
        queued_task, _ = await get_or_create(session, Task, defaults={
            'name': 'Queued Task',
            'hc_attackmode': '0',
            'owner_id': admin.id,
            'wl_id': wordlist.id,
            'rule_id': rule.id,
            'hc_mask': None
        }, name='Queued Task')

        await get_or_create(session, JobTask, defaults={
            'job_id': running_job.id,
            'task_id': running_task.id,
            'priority': 2,
            'command': 'hashcat ...',
            'status': 'Running',
            'started_at': datetime.utcnow(),
            'agent_id': agent.id
        }, job_id=running_job.id, task_id=running_task.id)
        await get_or_create(session, JobTask, defaults={
            'job_id': running_job.id,
            'task_id': completed_task.id,
            'priority': 2,
            'command': 'hashcat ...',
            'status': 'Completed',
            'started_at': datetime.utcnow(),
            'agent_id': agent.id
        }, job_id=running_job.id, task_id=completed_task.id)
        await get_or_create(session, JobTask, defaults={
            'job_id': running_job.id,
            'task_id': queued_task.id,
            'priority': 2,
            'command': 'hashcat ...',
            'status': 'Queued',
            'started_at': None,
            'agent_id': None
        }, job_id=running_job.id, task_id=queued_task.id)

        # Add cracked hashes for chart data (last 7 days)
        for i in range(7):
            day = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
            recovered_at = day.replace(day=day.day - i)
            cracked_hash, _ = await get_or_create(session, Hash, defaults={
                'sub_ciphertext': f'subhash_cracked_{i}',
                'ciphertext': f'hash_cracked_{i}',
                'hash_type': 0,
                'cracked': True,
                'recovered_at': recovered_at,
                'task_id': running_task.id,
                'recovered_by': admin.id,
                'plaintext': f'plain{i}'
            }, sub_ciphertext=f'subhash_cracked_{i}')

        print("Sample data inserted (with running/completed/queued jobs and cracked hashes for dashboard testing).")

if __name__ == "__main__":
    asyncio.run(main()) 