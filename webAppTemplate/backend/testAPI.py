#!/usr/bin/env python3
import requests
from rich.console import Console
from rich.table import Table
from rich import box
import argparse
import sys

# --- Argument Parsing ---
def parse_args():
    parser = argparse.ArgumentParser(description="Test Hashview API endpoints.")
    parser.add_argument('--email', type=str, default='admin@example.com', help='User email for login')
    parser.add_argument('--password', type=str, default='adminpassword', help='User password for login')
    parser.add_argument('--api-url', type=str, default='http://localhost:8000/api', help='Base API URL')
    parser.add_argument('--group', type=str, nargs='+', default=['all'], choices=['users', 'agents', 'jobs', 'customers', 'analytics', 'tasks', 'task-groups', 'wordlists', 'rules', 'all'], help='API group(s) to test')
    return parser.parse_args()

args = parse_args()
API_URL = args.api_url.rstrip('/')
EMAIL = args.email
PASSWORD = args.password
GROUPS = set(args.group)
if 'all' in GROUPS:
    GROUPS = {'users', 'agents', 'jobs', 'customers', 'analytics', 'tasks', 'task-groups', 'wordlists', 'rules'}

console = Console()
results = []
user_id = None
jwt_token = None
headers = {}

# --- User Auth ---
def register_and_login():
    global user_id, jwt_token, headers
    # Register user
    try:
        r = requests.post(f"{API_URL}/register", json={
            "first_name": "Test",
            "last_name": "User",
            "email_address": EMAIL,
            "password": PASSWORD
        })
        user_id = r.json().get("id")
        results.append(["Register", r.status_code, r.json()])
    except Exception as e:
        results.append(["Register", "ERR", str(e)])
    # Login user
    try:
        r = requests.post(f"{API_URL}/login", data={
            "username": EMAIL,
            "password": PASSWORD
        })
        jwt_token = r.json().get("access_token")
        results.append(["Login", r.status_code, r.json()])
    except Exception as e:
        results.append(["Login", "ERR", str(e)])
    if jwt_token:
        headers.update({"Authorization": f"Bearer {jwt_token}"})

# --- User API Tests ---
def test_users():
    # List users
    try:
        r = requests.get(f"{API_URL}/users", headers=headers)
        results.append(["List Users", r.status_code, r.json()])
        list_users_response = r.json()
    except Exception as e:
        results.append(["List Users", "ERR", str(e)])
        list_users_response = []
    # If user_id is None, try to get it from the list users response
    global user_id
    if user_id is None:
        try:
            for u in list_users_response:
                if u.get("email_address") == EMAIL:
                    user_id = u.get("id")
                    break
        except Exception:
            pass
    # Get user by ID
    try:
        r = requests.get(f"{API_URL}/users/{user_id}", headers=headers)
        results.append(["Get User", r.status_code, r.json()])
    except Exception as e:
        results.append(["Get User", "ERR", str(e)])
    # Update user
    try:
        r = requests.put(f"{API_URL}/users/{user_id}", headers=headers, json={
            "first_name": "Updated",
            "last_name": "User"
        })
        results.append(["Update User", r.status_code, r.json()])
    except Exception as e:
        results.append(["Update User", "ERR", str(e)])
    # Delete user
    try:
        r = requests.delete(f"{API_URL}/users/{user_id}", headers=headers)
        results.append(["Delete User", r.status_code, r.text])
    except Exception as e:
        results.append(["Delete User", "ERR", str(e)])

# --- Agents API Tests ---
def test_agents():
    try:
        r = requests.get(f"{API_URL}/agents", headers=headers)
        results.append(["List Agents", r.status_code, r.json()])
    except Exception as e:
        results.append(["List Agents", "ERR", str(e)])

# --- Jobs API Tests ---
def test_jobs():
    try:
        r = requests.get(f"{API_URL}/jobs", headers=headers)
        results.append(["List Jobs", r.status_code, r.json()])
    except Exception as e:
        results.append(["List Jobs", "ERR", str(e)])
    for status in ["running", "queued"]:
        try:
            r = requests.get(f"{API_URL}/jobs?status={status}", headers=headers)
            results.append([f"List Jobs ({status})", r.status_code, r.json()])
        except Exception as e:
            results.append([f"List Jobs ({status})", "ERR", str(e)])

# --- Customers API Tests ---
def test_customers():
    try:
        r = requests.get(f"{API_URL}/customers", headers=headers)
        results.append(["List Customers", r.status_code, r.json()])
    except Exception as e:
        results.append(["List Customers", "ERR", str(e)])

# --- Analytics API Tests ---
def test_analytics():
    try:
        r = requests.get(f"{API_URL}/analytics", headers=headers)
        results.append(["Dashboard Analytics", r.status_code, r.json()])
    except Exception as e:
        results.append(["Dashboard Analytics", "ERR", str(e)])

# --- Tasks API Tests ---
def test_tasks():
    # List tasks
    try:
        r = requests.get(f"{API_URL}/tasks", headers=headers)
        try:
            json_data = r.json()
        except Exception as e:
            print("Raw response from /tasks:", r.text)
            raise
        results.append(["List Tasks", r.status_code, json_data])
        tasks_response = json_data
    except Exception as e:
        results.append(["List Tasks", "ERR", str(e)])
        tasks_response = []
    # Get first task by ID if any
    if isinstance(tasks_response, list) and tasks_response:
        task_id = tasks_response[0].get("id")
        if task_id is not None:
            try:
                r = requests.get(f"{API_URL}/tasks/{task_id}", headers=headers)
                results.append([f"Get Task {task_id}", r.status_code, r.json()])
            except Exception as e:
                results.append([f"Get Task {task_id}", "ERR", str(e)])

def test_task_groups():
    # List task groups
    try:
        r = requests.get(f"{API_URL}/task-groups", headers=headers)
        results.append(["List Task Groups", r.status_code, r.json()])
        groups = r.json()
    except Exception as e:
        results.append(["List Task Groups", "ERR", str(e)])
        groups = []
    # Update first group (if any)
    if isinstance(groups, list) and groups:
        group = groups[0]
        group_id = group.get("id")
        orig_tasks = group.get("tasks", [])
        # Try updating to empty, then restore
        try:
            r = requests.put(f"{API_URL}/task-groups/{group_id}", json={"tasks": []}, headers=headers)
            results.append([f"Update Task Group {group_id} (empty)", r.status_code, r.json()])
        except Exception as e:
            results.append([f"Update Task Group {group_id} (empty)", "ERR", str(e)])
        # Restore original tasks
        try:
            r = requests.put(f"{API_URL}/task-groups/{group_id}", json={"tasks": orig_tasks}, headers=headers)
            results.append([f"Restore Task Group {group_id}", r.status_code, r.json()])
        except Exception as e:
            results.append([f"Restore Task Group {group_id}", "ERR", str(e)])

def test_wordlists():
    try:
        r = requests.get(f"{API_URL}/wordlists", headers=headers)
        results.append(["List Wordlists", r.status_code, r.json()])
    except Exception as e:
        results.append(["List Wordlists", "ERR", str(e)])

def test_rules():
    try:
        r = requests.get(f"{API_URL}/rules", headers=headers)
        results.append(["List Rules", r.status_code, r.json()])
    except Exception as e:
        results.append(["List Rules", "ERR", str(e)])

# --- Main ---
if __name__ == '__main__':
    register_and_login()
    if 'users' in GROUPS:
        test_users()
    if 'agents' in GROUPS:
        test_agents()
    if 'jobs' in GROUPS:
        test_jobs()
    if 'customers' in GROUPS:
        test_customers()
    if 'analytics' in GROUPS:
        test_analytics()
    if 'tasks' in GROUPS:
        test_tasks()
    if 'task-groups' in GROUPS:
        test_task_groups()
    if 'wordlists' in GROUPS:
        test_wordlists()
    if 'rules' in GROUPS:
        test_rules()
    # Print results
    table = Table(title="API Test Results", box=box.SIMPLE_HEAVY)
    table.add_column("Step", style="bold")
    table.add_column("Status Code", style="cyan")
    table.add_column("Response", style="magenta")
    for step, status, resp in results:
        if not isinstance(resp, str):
            resp_str = str(resp)
        else:
            resp_str = resp
        table.add_row(step, str(status), resp_str)
    console.print(table) 
