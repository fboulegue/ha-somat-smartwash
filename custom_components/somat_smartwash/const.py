"""Constants for the Somat Smartwash integration."""

from datetime import timedelta

DOMAIN = "somat_smartwash"

# API Endpoints & Auth
GIGYA_API_KEY = "4_RQP-qYtwmABF5LyHL6A3Fg"
GIGYA_LOGIN_URL = "https://accounts.eu1.gigya.com/accounts.login"
GRAPHQL_URL = "https://app-api.somat-smartwash.com/v1/query"
PRODUCT_HEADER = "somat"
USER_AGENT = "GigyaSDK/iOS/4.0.0"

# Configuration Keys
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Update Interval (Cloud Polling)
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)

# Known Programs
PROGRAM_INTENSE = "intense"
PROGRAM_ECO = "eco"
PROGRAM_AUTO = "auto"
PROGRAM_STANDARD = "standard"

AVAILABLE_PROGRAMS = [
    PROGRAM_INTENSE,
    PROGRAM_ECO,
    PROGRAM_AUTO,
    PROGRAM_STANDARD,
]

# Attribute Keys
ATTR_DETERGENT_FILL_LEVEL = "detergent_fill_level"
ATTR_WASH_CYCLE_STATUS = "wash_cycle_status"
ATTR_BATTERY_LEVEL = "battery_level"
ATTR_REFILL_STATUS = "refill_status"
ATTR_PROGRAM = "program"
ATTR_WIFI_RSSI = "wifi_rssi"
ATTR_WATER_HARDNESS = "water_hardness"
ATTR_CONNECTION_STATUS = "connection_status"
ATTR_SETUP_STATUS = "setup_status"
ATTR_SERIAL_NUMBER = "serial_number"
