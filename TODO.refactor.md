# Hashview Refactor TODO List

**Goal:** Migrate all features from the legacy Hashview monolith to a modern, modular architecture using the webAppTemplate (React frontend + Python API backend).

---

## Milestone 1: Preparation & Analysis
- [ ] Review and document all Hashview features, models, and routes
- [ ] Review webAppTemplate backend and frontend structure
- [ ] Identify missing infrastructure (DB, auth, file uploads, etc.)
- [ ] Set up a new git branch for the refactor

---

## Milestone 2: Backend Foundation
- [ ] Set up Python backend in `webAppTemplate/backend/`
- [ ] Define database models (users, agents, jobs, hashfiles, etc.)
- [ ] Set up database migrations (Alembic or Flask-Migrate)
- [ ] Implement authentication (JWT/session)
- [ ] Implement basic CRUD API endpoints for all core resources
- [ ] Write simple backend tests (e.g., pytest, curl)

---

## Milestone 3: Frontend Foundation
- [ ] Set up React frontend in `webAppTemplate/frontend/`
- [ ] Implement routing and navigation
- [ ] Implement authentication flow (login, logout, registration)
- [ ] Create basic page structure for all major features
- [ ] Write simple frontend tests (e.g., login/logout works)

---

## Milestone 4: Core Feature Migration
- [ ] Agents: API endpoints + React UI
- [ ] Hashfiles: Upload/download endpoints + UI
- [ ] Jobs & Tasks: Orchestration logic + UI
- [ ] Rules & Wordlists: Management endpoints + UI
- [ ] Analytics: Reporting endpoints + UI
- [ ] Notifications: API + UI
- [ ] Customers: Multi-tenancy endpoints + UI
- [ ] Settings: API + UI
- [ ] Setup flows: Initial admin/config setup
- [ ] File upload/download logic (backend & frontend)
- [ ] Real-time updates (WebSockets or polling)
- [ ] Write tests for each feature as implemented

---

## Milestone 5: Data Migration
- [ ] Plan and script migration of existing data to new schema
- [ ] Test data migration on staging environment

---

## Milestone 6: Infrastructure & Deployment
- [ ] Update Dockerfiles and docker-compose for new structure
- [ ] Update k8s and deployment scripts
- [ ] Set up CI/CD for new stack
- [ ] Manual and automated end-to-end testing

---

## Milestone 7: Documentation & Rollout
- [ ] Update README and user/admin docs
- [ ] Document migration/upgrade process
- [ ] Roll out to production
- [ ] Monitor and address issues

---

**At each major milestone:**
- [ ] Run a simple test to ensure changes work
- [ ] Commit changes to git with a clear message 