from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.state"


@dataclass
class BillingState:
    anchor_counter: int
    cycle_start: str
    next_renewal: str
    monthly_pages: int
    monthly_remaining_at_anchor: int
    rollover_remaining_at_anchor: int
    pages_used_cycle_at_anchor: int
    config_revision: int = 0
    last_counter: int | None = None
    last_update_date: str | None = None
    renewal_uncertain: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BillingState | None":
        if "anchor_counter" not in data:
            return None
        allowed = cls.__dataclass_fields__.keys()
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)


class BillingStore:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry_id}"
        )

    async def load(self) -> BillingState | None:
        data = await self._store.async_load()
        if not data:
            return None
        return BillingState.from_dict(data)

    async def save(self, state: BillingState) -> None:
        await self._store.async_save(asdict(state))

    async def delete(self) -> None:
        """Delete persisted billing state for a removed config entry."""
        await self._store.async_remove()
