"""Constants for the Insite Energy integration."""

DOMAIN = "insite_energy"
DEFAULT_SCAN_INTERVAL = 15  # minutes

BASE_URL = "https://my.insite-energy.co.uk"
LOGIN_URL = f"{BASE_URL}/Account/Login"
DETAILS_URL = f"{BASE_URL}/Customer/Details"

ATTR_CREDIT_BALANCE = "credit_balance"
ATTR_HOT_WATER_USAGE = "hot_water_usage"
ATTR_LAST_UPDATED = "last_updated"
