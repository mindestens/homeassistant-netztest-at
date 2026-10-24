"""Constants for the Netztest AT integration (unofficial, uses the RTR-Netztest)."""

from __future__ import annotations

import os

DOMAIN = "netztest_at"
VERSION = "1.0.0"

CONF_SCHEDULE_ENABLED = "schedule_enabled"
CONF_START_TIMES = "start_times"
CONF_RANDOM_DELAY = "random_delay"
CONF_PLAN_DOWNLOAD = "plan_download"
CONF_PLAN_UPLOAD = "plan_upload"
# The RTR client always reports terms_and_conditions_accepted=true, so the user must agree in the config flow.
CONF_ACCEPT_TERMS = "accept_rtr_terms"
TERMS_URL = "https://www.netztest.at/de/tc"

# No default test times: the user picks them during setup. Contract values are optional.
DEFAULT_SCHEDULE_ENABLED = True
DEFAULT_RANDOM_DELAY = 0
MAX_TESTS_PER_DAY = 24
MIN_GAP_MINUTES = 30
MAX_RANDOM_DELAY = 15

# RTR gives no country per server, only names/hosts like "RTR https 100G AT #1", "RTR Cov vie01",
# "vie1-httpv4.netztest.at" (Austria) vs. "RTR https DE", "... LJ", "AKOS ...", "CTU ...", "SIN", "US west".
AUSTRIA_SERVER_PATTERN = r"(\bAT\b|\bvie\d*\b|^vie\d*-)"
ISSUE_FOREIGN_SERVER = "foreign_server"

CONTROL_SERVER = "https://c01.netztest.at"
OPENTEST_API = "https://c01.netztest.at/RMBTStatisticServer/opentests/{uuid}"
RESULT_URL = "https://www.netztest.at/de/opentest?open_test_uuid={uuid}"

BIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
BIN_PATH = os.path.join(BIN_DIR, "rmbt-client")
# Statically linked RTR client, built by this repository's release workflow from the official RTR source.
RELEASE_URL = "https://github.com/mindestens/homeassistant-netztest-at/releases/download/v{version}/{name}"
BINARY_NAMES = {
    "x86_64": "rmbt-client-linux-x86_64",
    "amd64": "rmbt-client-linux-x86_64",
    "aarch64": "rmbt-client-linux-aarch64",
    "arm64": "rmbt-client-linux-aarch64",
}
CHECKSUM_FILE = "SHA256SUMS"

# A test takes ~30 s; abort a hanging client after this many seconds.
TEST_TIMEOUT = 180
# Before starting, wait (at most this long) while another speed-test program is running, so two
# measurements never share the line. Process names as shown by `pgrep -x` (max. 15 characters).
OTHER_SPEEDTEST_PROCESSES = ("speedtest", "speedtest.bin", "librespeed-cli", "iperf3", "iperf", "ndt7-client")
OTHER_SPEEDTEST_WAIT_MAX = 240

STORAGE_VERSION = 1

SERVICE_RUN_TEST = "run_test"
