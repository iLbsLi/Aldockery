"""Constants for Aldockery."""
from __future__ import annotations

DOMAIN = "aldockery_beta"

CONF_NAME = "name"
CONF_MODE = "mode"
CONF_DOCKER_BIN = "docker_bin"
CONF_SSH_USER = "ssh_user"
CONF_SSH_HOST = "ssh_host"
CONF_SSH_KEY = "ssh_key"
CONF_SSH_PORT = "ssh_port"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_INCLUDE_PATTERNS = "include_patterns"
CONF_EXCLUDE_PATTERNS = "exclude_patterns"
CONF_PROTECTED_CONTAINERS = "protected_containers"

MODE_LOCAL = "local"
MODE_SSH = "ssh"

DEFAULT_NAME = "Docker Host"
DEFAULT_DOCKER_BIN = "docker"
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_SSH_PORT = 22

DATA_ENTRIES = "entries"
DATA_API = "api"
DATA_COORDINATOR = "coordinator"
DATA_ENTRY_NAME = "entry_name"
DATA_KNOWN_SWITCHES = "known_switches"
DATA_KNOWN_BUTTONS = "known_buttons"
DATA_KNOWN_SENSORS = "known_sensors"
DATA_KNOWN_BINARY_SENSORS = "known_binary_sensors"

SERVICE_START_CONTAINER = "start_container"
SERVICE_STOP_CONTAINER = "stop_container"
SERVICE_RESTART_CONTAINER = "restart_container"
SERVICE_REDISCOVER = "rediscover"
SERVICE_PRUNE_MISSING = "prune_missing"
SERVICE_TEST_CONNECTION = "test_connection"

PLATFORMS = ["switch", "button", "sensor", "binary_sensor"]
