from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data

from . import PagePlanConfigEntry

TO_REDACT = {"host"}


async def async_get_config_entry_diagnostics(hass, entry: PagePlanConfigEntry):
    coordinator = entry.runtime_data.coordinator
    state = coordinator.state
    data = coordinator.data
    return {
        "config": async_redact_data({**entry.data, **entry.options}, TO_REDACT),
        "polling_seconds": int(coordinator.update_interval.total_seconds()),
        "state": None if state is None else {
            "anchor_counter": state.anchor_counter,
            "cycle_start": state.cycle_start,
            "next_renewal": state.next_renewal,
            "monthly_pages": state.monthly_pages,
            "monthly_remaining_at_anchor": state.monthly_remaining_at_anchor,
            "rollover_remaining_at_anchor": state.rollover_remaining_at_anchor,
            "pages_used_cycle_at_anchor": state.pages_used_cycle_at_anchor,
            "last_counter": state.last_counter,
            "last_update_date": state.last_update_date,
            "renewal_uncertain": state.renewal_uncertain,
            "config_revision": state.config_revision,
        },
        "current": None if data is None else {
            "subscription_impressions": data.printer.subscription_impressions,
            "pages_used_cycle": data.pages_used_cycle,
            "monthly_remaining": data.monthly_remaining,
            "rollover_remaining": data.rollover_remaining,
            "total_remaining": data.total_remaining,
            "next_renewal": data.next_renewal.isoformat(),
            "ink_black": data.printer.ink_black,
            "ink_cyan": data.printer.ink_cyan,
            "ink_magenta": data.printer.ink_magenta,
            "ink_yellow": data.printer.ink_yellow,
        },
    }
