from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import LEDMPrinterClient
from .const import (
    CONF_CONFIG_REVISION,
    CONF_HOST,
    CONF_MONTHLY_PAGES,
    CONF_MONTHLY_USED_TODAY,
    CONF_RENEWAL_DAY,
    CONF_ROLLOVER_MAX,
    CONF_ROLLOVER_TOTAL_TODAY,
    CONF_ROLLOVER_USED_TODAY,
    DEFAULT_ROLLOVER_MULTIPLIER,
    PLATFORMS,
)
from .coordinator import PagePlanCoordinator
from .storage import BillingStore


@dataclass
class RuntimeData:
    coordinator: PagePlanCoordinator


type PagePlanConfigEntry = ConfigEntry[RuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: PagePlanConfigEntry) -> bool:
    data = {**entry.data, **entry.options}
    monthly = int(data[CONF_MONTHLY_PAGES])
    rollover_max = int(
        data.get(CONF_ROLLOVER_MAX, monthly * DEFAULT_ROLLOVER_MULTIPLIER)
    )

    client = LEDMPrinterClient(async_get_clientsession(hass), data[CONF_HOST])
    store = BillingStore(hass, entry.entry_id)
    coordinator = PagePlanCoordinator(
        hass,
        entry,
        client,
        store,
        monthly_pages=monthly,
        renewal_day=int(data[CONF_RENEWAL_DAY]),
        monthly_used_today=int(data[CONF_MONTHLY_USED_TODAY]),
        rollover_total_today=int(data[CONF_ROLLOVER_TOTAL_TODAY]),
        rollover_used_today=int(data[CONF_ROLLOVER_USED_TODAY]),
        rollover_max=rollover_max,
        config_revision=int(data.get(CONF_CONFIG_REVISION, 1)),
    )
    await coordinator.async_initialize()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = RuntimeData(coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PagePlanConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: PagePlanConfigEntry) -> None:
    """Remove persisted state when the config entry is deleted."""
    await BillingStore(hass, entry.entry_id).delete()
