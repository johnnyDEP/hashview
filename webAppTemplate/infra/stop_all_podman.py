#!/usr/bin/env python3
import subprocess


def stop_all_podman_containers():
    try:
        # Get all running container IDs
        result = subprocess.run(['podman', 'ps', '-q'], capture_output=True, text=True, check=True)
        container_ids = result.stdout.strip().split('\n')
        container_ids = [cid for cid in container_ids if cid]
        if not container_ids:
            print('No running podman containers found.')
            return
        print(f'Stopping {len(container_ids)} podman containers...')
        stop_result = subprocess.run(['podman', 'stop'] + container_ids, capture_output=True, text=True)
        print(stop_result.stdout)
        if stop_result.stderr:
            print('Errors:', stop_result.stderr)
        print('All containers stopped.')
    except subprocess.CalledProcessError as e:
        print('Error running podman command:', e)
        print('Output:', e.output)

if __name__ == '__main__':
    stop_all_podman_containers() 