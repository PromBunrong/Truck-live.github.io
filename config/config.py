# config/config.py

import os

# Choose environment: "local" or "host"
ENVIRONMENT = os.getenv("APP_ENV", "local")

# Spreadsheet configuration
SPREADSHEET_ID = "1KMpaAiTMAlWsGxLZaqrWJfIXL8ynUt5i0nfsja7mXWs"

SHEET_GIDS = {
    'security': "1814716377",
    'driver': "2019928657",
    'status': "1969607654",
    'logistic': "1027892338"
}

REFRESH_INTERVAL_SECONDS = int(os.getenv("REFRESH_INTERVAL_SECONDS", 30))

# Cambodia timezone (UTC+7)
CAMBODIA_TZ = "Asia/Phnom_Penh"     # canonical tz name for Cambodia (UTC+07:00)
UTC_OFFSET = "+07:00"               # optional descriptive label

# Timezone auto-switch (keeps behavior explicit)
if ENVIRONMENT == "local":
    LOCAL_TZ = CAMBODIA_TZ
    DEBUG_MODE = True
else:
    LOCAL_TZ = CAMBODIA_TZ
    DEBUG_MODE = False
