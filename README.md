# Aldockery

A Home Assistant custom integration for controlling Docker containers locally or over SSH.

## What it does
- Adds Docker hosts as Home Assistant integrations
- Creates switches for container running state
- Creates start / stop / restart buttons per container
- Adds host-level reachable and container-count sensors
- Supports include/exclude filters and protected containers
- Includes services for rediscovery, testing connection, and pruning stale entities

## Install in HACS as a custom repository
1. Put this repository on GitHub as a **public** repository.
2. In Home Assistant, open **HACS**.
3. Open the **three-dot menu** and choose **Custom repositories**.
4. Add your GitHub repo URL.
5. Choose type **Integration**.
6. Install **Aldockery** from HACS.
7. Restart Home Assistant.
8. Go to **Settings -> Devices & Services -> Add Integration** and add **Aldockery**.

## Notes
- The internal domain is `aldockery_beta` so it can coexist with earlier private builds.
- Update `custom_components/aldockery_beta/manifest.json` to replace `ilbsli` in `documentation` and `issue_tracker` after you create the GitHub repo.

## First entry example
- name: `orpi`
- mode: `ssh`
- docker_bin: `docker`
- scan_interval: `30`
- ssh_user: `ilbsli`
- ssh_host: `192.168.0.23`
- ssh_key: `/config/ssh/orpi_sync_key`
- ssh_port: `22`
