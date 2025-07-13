# Hashview Feature, Model, and Route Inventory

## Features (from README & TODO)
- User authentication & management (admin, last login, password reset, profile)
- Agents (remote workers) management (approve, monitor, check-in, version, status)
- Hashfiles upload & management (per customer, per job, cracked/uncracked stats)
- Jobs & tasks orchestration (priority, status, scheduling, grouping, command building)
- Rules & wordlists management (upload, edit, dynamic/static, checksum, size)
- Analytics & reporting (per customer, per hashfile, top passwords, crack rate, graphs)
- Notifications (email, push, job/hash notifications, status updates)
- Customers (multi-tenancy, per-customer jobs/hashfiles)
- Settings & setup flows (retention, max runtime, job weights, admin setup)
- Search (by hash, user, password)
- File upload/download (hashfiles, wordlists, rules)
- Real-time updates (agent check-in, job/task progress)
- UI: Home, dashboard, collapsible jobs, modals, forms, profile, etc.

---

## Database Models (from models.py)
- **Users**: id, name, email, password, admin, pushover, last login, api key, relationships to wordlists, rules, jobs, tasks, taskgroups
- **Settings**: retention, max runtimes, job weights
- **Jobs**: id, name, priority, status, timestamps, hashfile, customer, owner
- **JobTasks**: job, task, priority, command, status, agent
- **Customers**: id, name
- **Hashfiles**: id, name, uploaded, runtime, customer, owner
- **HashfileHashes**: hash, username, hashfile
- **Agents**: id, name, IP, uuid, status, hc_status, checkin, benchmark, cpu/gpu count
- **Rules**: id, name, updated, owner, path, size, checksum
- **Wordlists**: id, name, updated, owner, type, path, size, checksum
- **Tasks**: id, name, attackmode, owner, wl_id, rule_id, mask
- **TaskGroups**: id, name, owner, tasks
- **Hashes**: id, sub_ciphertext, ciphertext, hash_type, cracked, plaintext
- **JobNotifications**: owner, job, method
- **HashNotifications**: owner, hash, method

---

## Routes/Endpoints (from routes.py)
- **Main**: `/` (dashboard/home)
- **Users**: `/login`, `/users`, `/profile`
- **Agents**: `/agents`
- **Hashfiles**: `/hashfiles`
- **Jobs**: `/jobs`
- **Tasks**: `/tasks`
- **Task Groups**: `/task_groups`
- **Rules**: `/rules`
- **Wordlists**: `/wordlists`
- **Analytics**: `/analytics`
- **Notifications**: `/notifications`
- **Customers**: `/customers`
- **Settings**: `/settings`
- **Search**: `/search`
- **API**: `/v1/rules`, `/v1/wordlists`, `/v1/jobs/<id>`, `/v1/search`, etc.
- **Setup**: `/setup` (initial admin/config) 