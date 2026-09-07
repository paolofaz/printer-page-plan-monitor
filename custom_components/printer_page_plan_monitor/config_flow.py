from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload
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
    DOMAIN,
    INTEGRATION_NAME,
)


def _validate(
    monthly: int,
    monthly_used: int,
    rollover_total: int,
    rollover_used: int,
    rollover_max: int,
) -> dict[str, str]:
    errors: dict[str, str] = {}
    if monthly_used > monthly:
        errors[CONF_MONTHLY_USED_TODAY] = "monthly_used_too_high"
    if rollover_used > rollover_total:
        errors[CONF_ROLLOVER_USED_TODAY] = "rollover_used_too_high"
    if rollover_total > rollover_max:
        errors[CONF_ROLLOVER_TOTAL_TODAY] = "rollover_total_too_high"
    return errors


class PagePlanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            monthly = int(user_input[CONF_MONTHLY_PAGES])
            monthly_used = int(user_input[CONF_MONTHLY_USED_TODAY])
            rollover_total = int(user_input[CONF_ROLLOVER_TOTAL_TODAY])
            rollover_used = int(user_input[CONF_ROLLOVER_USED_TODAY])
            rollover_max = int(user_input[CONF_ROLLOVER_MAX])
            errors = _validate(
                monthly,
                monthly_used,
                rollover_total,
                rollover_used,
                rollover_max,
            )
            if not errors:
                try:
                    client = LEDMPrinterClient(
                        async_get_clientsession(self.hass), user_input[CONF_HOST]
                    )
                    await client.async_get_data()
                except Exception:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(user_input[CONF_HOST].lower())
                    self._abort_if_unique_id_configured()
                    user_input[CONF_CONFIG_REVISION] = 1
                    return self.async_create_entry(title=INTEGRATION_NAME, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_RENEWAL_DAY, default=1): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=31)
                ),
                vol.Required(CONF_MONTHLY_PAGES, default=50): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                vol.Required(CONF_MONTHLY_USED_TODAY, default=0): vol.All(
                    vol.Coerce(int), vol.Range(min=0)
                ),
                vol.Required(CONF_ROLLOVER_TOTAL_TODAY, default=0): vol.All(
                    vol.Coerce(int), vol.Range(min=0)
                ),
                vol.Required(CONF_ROLLOVER_USED_TODAY, default=0): vol.All(
                    vol.Coerce(int), vol.Range(min=0)
                ),
                vol.Required(
                    CONF_ROLLOVER_MAX,
                    default=50 * DEFAULT_ROLLOVER_MULTIPLIER,
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return PagePlanOptionsFlow()


class PagePlanOptionsFlow(OptionsFlowWithReload):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            monthly = int(user_input[CONF_MONTHLY_PAGES])
            monthly_used = int(user_input[CONF_MONTHLY_USED_TODAY])
            rollover_total = int(user_input[CONF_ROLLOVER_TOTAL_TODAY])
            rollover_used = int(user_input[CONF_ROLLOVER_USED_TODAY])
            rollover_max = int(user_input[CONF_ROLLOVER_MAX])
            errors = _validate(
                monthly,
                monthly_used,
                rollover_total,
                rollover_used,
                rollover_max,
            )
            if not errors:
                user_input[CONF_CONFIG_REVISION] = int(
                    current.get(CONF_CONFIG_REVISION, 0)
                ) + 1
                return self.async_create_entry(data=user_input)

        old_monthly = int(current.get(CONF_MONTHLY_PAGES, 50))
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_RENEWAL_DAY,
                    default=int(current.get(CONF_RENEWAL_DAY, 1)),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
                vol.Required(
                    CONF_MONTHLY_PAGES,
                    default=old_monthly,
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Required(
                    CONF_MONTHLY_USED_TODAY,
                    default=int(current.get(CONF_MONTHLY_USED_TODAY, 0)),
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Required(
                    CONF_ROLLOVER_TOTAL_TODAY,
                    default=int(current.get(CONF_ROLLOVER_TOTAL_TODAY, 0)),
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Required(
                    CONF_ROLLOVER_USED_TODAY,
                    default=int(current.get(CONF_ROLLOVER_USED_TODAY, 0)),
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Required(
                    CONF_ROLLOVER_MAX,
                    default=int(
                        current.get(
                            CONF_ROLLOVER_MAX,
                            old_monthly * DEFAULT_ROLLOVER_MULTIPLIER,
                        )
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
