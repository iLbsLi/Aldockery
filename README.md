# Aldockery

A Home Assistant custom integration for controlling Docker containers locally or over SSH.

## Features
- Add Docker hosts as Home Assistant integrations
- Keep device names host-style, such as `ORPI Docker` and `RASPI Docker`
- Create switches for container running state with friendly names like `cp-web`
- Create start, stop, and restart buttons per container with friendly names like `cp-web restart`
- Fresh recreated entities are intended to land on IDs like `switch.<container>_<host>_docker` and `button.<container>_<action>_<host>_docker`
- Use `suggested_object_id` to guide the initial object/entity IDs for fresh entries
- Add host-level reachable and container-count sensors
- Support include/exclude filters and protected containers
- Include services for rediscovery, testing connection, and pruning stale entities

## Install with HACS
1. Open HACS in Home Assistant.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add this repository URL.
4. Choose type **Integration**.
5. Install **Aldockery** from HACS.
6. Restart Home Assistant.
7. Go to **Settings → Devices & Services → Add Integration** and add **Aldockery**.

## Example setup
Use your own Docker host, SSH user, and SSH key path from your Home Assistant environment.

## Notes
- The current integration folder is `custom_components/aldockery_beta`.
- The displayed integration name is **Aldockery**.
- The current naming behavior is container-first in entity friendly names, while device names still include the host label.
