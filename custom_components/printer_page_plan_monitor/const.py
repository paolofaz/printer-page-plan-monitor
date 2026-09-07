DOMAIN = "printer_page_plan_monitor"
PLATFORMS = ["sensor"]

INTEGRATION_NAME = "Printer Page Plan Monitor for HP Instant Ink"

CONF_HOST = "host"
CONF_RENEWAL_DAY = "renewal_day"
CONF_MONTHLY_PAGES = "monthly_pages"
CONF_MONTHLY_USED_TODAY = "monthly_used_today"
CONF_ROLLOVER_TOTAL_TODAY = "rollover_total_today"
CONF_ROLLOVER_USED_TODAY = "rollover_used_today"
CONF_ROLLOVER_MAX = "rollover_max"
CONF_CONFIG_REVISION = "config_revision"

DEFAULT_SCAN_INTERVAL = 120
DEFAULT_ROLLOVER_MULTIPLIER = 3

PRODUCT_USAGE_PATH = "/DevMgmt/ProductUsageDyn.xml"
