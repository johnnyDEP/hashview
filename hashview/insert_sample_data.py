import os
import sys
from hashview import create_app
from hashview.models import db, Users, Jobs, Tasks, TaskGroups, Hashfiles, Rules, Wordlists, Customers, Agents, Settings, JobTasks, Hashes, HashfileHashes, HashNotifications
from flask_bcrypt import Bcrypt
from datetime import datetime

app = create_app()
bcrypt = Bcrypt(app)

# Helper to avoid duplicate inserts
def get_or_create(model, defaults=None, **kwargs):
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items())
        if defaults:
            params.update(defaults)
        instance = model(**params)
        db.session.add(instance)
        db.session.commit()
        return instance, True

with app.app_context():
    # Users
    admin_pw = bcrypt.generate_password_hash('adminpassword').decode('utf-8')
    admin, _ = get_or_create(Users, defaults={
        'first_name': 'Admin',
        'last_name': 'User',
        'password': admin_pw,
        'admin': True,
        'email_address': 'admin@example.com'
    }, email_address='admin@example.com')

    user_pw = bcrypt.generate_password_hash('userpassword').decode('utf-8')
    user, _ = get_or_create(Users, defaults={
        'first_name': 'Test',
        'last_name': 'User',
        'password': user_pw,
        'admin': False,
        'email_address': 'user@example.com'
    }, email_address='user@example.com')

    # Customers
    customer, _ = get_or_create(Customers, name='Test Customer')

    # Agents
    agent, _ = get_or_create(Agents, defaults={
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
    settings, _ = get_or_create(Settings, defaults={
        'retention_period': 30,
        'max_runtime_jobs': 24,
        'max_runtime_tasks': 12,
        'enabled_job_weights': True
    }, id=1)

    # Wordlists
    wordlist, _ = get_or_create(Wordlists, defaults={
        'name': 'rockyou.txt',
        'last_updated': datetime.utcnow(),
        'owner_id': admin.id,
        'type': 'static',
        'path': '/wordlists/rockyou.txt',
        'size': 1000000,
        'checksum': 'abc123'
    }, name='rockyou.txt')

    # Rules
    rule, _ = get_or_create(Rules, defaults={
        'name': 'best64.rule',
        'last_updated': datetime.utcnow(),
        'owner_id': admin.id,
        'path': '/rules/best64.rule',
        'size': 1024,
        'checksum': 'def456'
    }, name='best64.rule')

    # Hashfiles
    hashfile, _ = get_or_create(Hashfiles, defaults={
        'name': 'test_hashfile.txt',
        'uploaded_at': datetime.utcnow(),
        'runtime': 0,
        'customer_id': customer.id,
        'owner_id': admin.id
    }, name='test_hashfile.txt')

    # Hashes
    hash_entry, _ = get_or_create(Hashes, defaults={
        'sub_ciphertext': 'subhash1',
        'ciphertext': 'hash1',
        'hash_type': 0,
        'cracked': False,
        'recovered_at': None,
        'task_id': None,
        'recovered_by': None,
        'plaintext': None
    }, sub_ciphertext='subhash1')

    # HashfileHashes
    hashfilehash, _ = get_or_create(HashfileHashes, defaults={
        'hash_id': hash_entry.id,
        'username': 'testuser',
        'hashfile_id': hashfile.id
    }, hash_id=hash_entry.id, hashfile_id=hashfile.id)

    # Tasks
    task, _ = get_or_create(Tasks, defaults={
        'name': 'Test Task',
        'hc_attackmode': '0',
        'owner_id': admin.id,
        'wl_id': wordlist.id,
        'wl_id_2': None,
        'j_rule': None,
        'k_rule': None,
        'rule_id': rule.id,
        'hc_mask': None
    }, name='Test Task')

    # TaskGroups
    taskgroup, _ = get_or_create(TaskGroups, defaults={
        'name': 'Test Group',
        'owner_id': admin.id,
        'tasks': str(task.id)
    }, name='Test Group')

    # Jobs
    job, _ = get_or_create(Jobs, defaults={
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
    jobtask, _ = get_or_create(JobTasks, defaults={
        'job_id': job.id,
        'task_id': task.id,
        'priority': 3,
        'command': 'hashcat ...',
        'status': 'Not Started',
        'started_at': None,
        'agent_id': agent.id
    }, job_id=job.id, task_id=task.id)

    # HashNotifications
    hashnotif, _ = get_or_create(HashNotifications, defaults={
        'owner_id': admin.id,
        'hash_id': hash_entry.id,
        'method': 'email'
    }, owner_id=admin.id, hash_id=hash_entry.id)

    print("Sample data inserted.") 