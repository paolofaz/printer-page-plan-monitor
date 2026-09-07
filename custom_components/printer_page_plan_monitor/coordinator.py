from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .client import LEDMPrinterClient, PrinterData
from .const import DEFAULT_SCAN_INTERVAL, INTEGRATION_NAME
from .storage import BillingState, BillingStore

_LOGGER = logging.getLogger(__name__)


@dataclass
class PagePlanData:
    printer: PrinterData
    pages_used_cycle: int
    monthly_remaining: int
    rollover_remaining: int
    total_remaining: int
    next_renewal: date
    monthly_pages: int
    rollover_max: int
    renewal_uncertain: bool


def _today() -> date:
    return dt_util.now().date()


def _next_date_for_day(from_date: date, day: int) -> date:
    year, month = from_date.year, from_date.month
    candidate = date(year, month, min(day, monthrange(year, month)[1]))
    if candidate <= from_date:
        month += 1
        if month == 13:
            month = 1
            year += 1
        candidate = date(year, month, min(day, monthrange(year, month)[1]))
    return candidate


class PagePlanCoordinator(DataUpdateCoordinator[PagePlanData]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: LEDMPrinterClient,
        store: BillingStore,
        monthly_pages: int,
        renewal_day: int,
        monthly_used_today: int,
        rollover_total_today: int,
        rollover_used_today: int,
        rollover_max: int,
        config_revision: int,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=INTEGRATION_NAME,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=entry,
        )
        self.client = client
        self.store = store
        self.monthly_pages = monthly_pages
        self.renewal_day = renewal_day
        self.monthly_used_today = monthly_used_today
        self.rollover_total_today = rollover_total_today
        self.rollover_used_today = rollover_used_today
        self.rollover_max = rollover_max
        self.config_revision = config_revision
        self.state: BillingState | None = None

    async def _new_anchor(self, printer: PrinterData) -> None:
        today = _today()
        rollover_remaining = max(0, self.rollover_total_today - self.rollover_used_today)
        self.state = BillingState(
            anchor_counter=printer.subscription_impressions,
            cycle_start=today.isoformat(),
            next_renewal=_next_date_for_day(today, self.renewal_day).isoformat(),
            monthly_pages=self.monthly_pages,
            monthly_remaining_at_anchor=max(
                0, self.monthly_pages - self.monthly_used_today
            ),
            rollover_remaining_at_anchor=rollover_remaining,
            pages_used_cycle_at_anchor=(
                self.monthly_used_today + self.rollover_used_today
            ),
            config_revision=self.config_revision,
            last_counter=printer.subscription_impressions,
            last_update_date=today.isoformat(),
            renewal_uncertain=False,
        )
        await self.store.save(self.state)

    async def async_initialize(self) -> None:
        self.state = await self.store.load()
        if self.state is not None and self.state.config_revision == self.config_revision:
            return
        printer = await self.client.async_get_data()
        await self._new_anchor(printer)

    def _balances_for_counter(self, current_counter: int) -> tuple[int, int, int]:
        assert self.state is not None
        delta = max(0, current_counter - self.state.anchor_counter)
        monthly_consumed = min(delta, self.state.monthly_remaining_at_anchor)
        monthly_remaining = max(
            0, self.state.monthly_remaining_at_anchor - monthly_consumed
        )
        rollover_consumed = max(0, delta - monthly_consumed)
        rollover_remaining = max(
            0, self.state.rollover_remaining_at_anchor - rollover_consumed
        )
        pages_used_cycle = self.state.pages_used_cycle_at_anchor + delta
        return pages_used_cycle, monthly_remaining, rollover_remaining

    async def _roll_cycle_at_counter(
        self, boundary_counter: int, uncertain: bool
    ) -> None:
        assert self.state is not None
        today = _today()
        next_renewal = date.fromisoformat(self.state.next_renewal)
        _, monthly_remaining, rollover_remaining = self._balances_for_counter(
            boundary_counter
        )
        new_rollover = min(
            self.rollover_max, rollover_remaining + monthly_remaining
        )

        cycle_start = next_renewal
        candidate = _next_date_for_day(next_renewal, self.renewal_day)
        while today >= candidate:
            new_rollover = min(
                self.rollover_max, new_rollover + self.monthly_pages
            )
            cycle_start = candidate
            candidate = _next_date_for_day(candidate, self.renewal_day)
            uncertain = True

        self.state = BillingState(
            anchor_counter=boundary_counter,
            cycle_start=cycle_start.isoformat(),
            next_renewal=candidate.isoformat(),
            monthly_pages=self.monthly_pages,
            monthly_remaining_at_anchor=self.monthly_pages,
            rollover_remaining_at_anchor=new_rollover,
            pages_used_cycle_at_anchor=0,
            config_revision=self.config_revision,
            last_counter=boundary_counter,
            last_update_date=today.isoformat(),
            renewal_uncertain=uncertain,
        )
        await self.store.save(self.state)

    async def _roll_before_fetch_if_needed(self) -> None:
        assert self.state is not None
        today = _today()
        next_renewal = date.fromisoformat(self.state.next_renewal)
        if today < next_renewal:
            return

        boundary_counter = self.state.last_counter
        uncertain = False
        if boundary_counter is None:
            boundary_counter = self.state.anchor_counter
            uncertain = True
        if self.state.last_update_date:
            last_date = date.fromisoformat(self.state.last_update_date)
            if last_date < next_renewal - timedelta(days=1):
                uncertain = True
        else:
            uncertain = True

        await self._roll_cycle_at_counter(boundary_counter, uncertain)

    async def _async_update_data(self) -> PagePlanData:
        try:
            if self.state is None:
                await self.async_initialize()
            assert self.state is not None

            await self._roll_before_fetch_if_needed()
            printer = await self.client.async_get_data()
            assert self.state is not None

            if printer.subscription_impressions < self.state.anchor_counter:
                _LOGGER.warning(
                    "Page counter decreased from %s to %s; re-anchoring without changing balances",
                    self.state.anchor_counter,
                    printer.subscription_impressions,
                )
                used, monthly_remaining, rollover_remaining = self._balances_for_counter(
                    self.state.last_counter or self.state.anchor_counter
                )
                self.state.anchor_counter = printer.subscription_impressions
                self.state.monthly_remaining_at_anchor = monthly_remaining
                self.state.rollover_remaining_at_anchor = rollover_remaining
                self.state.pages_used_cycle_at_anchor = used

            used, monthly_remaining, rollover_remaining = self._balances_for_counter(
                printer.subscription_impressions
            )
            self.state.last_counter = printer.subscription_impressions
            self.state.last_update_date = _today().isoformat()
            await self.store.save(self.state)

            return PagePlanData(
                printer=printer,
                pages_used_cycle=used,
                monthly_remaining=monthly_remaining,
                rollover_remaining=rollover_remaining,
                total_remaining=monthly_remaining + rollover_remaining,
                next_renewal=date.fromisoformat(self.state.next_renewal),
                monthly_pages=self.monthly_pages,
                rollover_max=self.rollover_max,
                renewal_uncertain=self.state.renewal_uncertain,
            )
        except Exception as err:
            raise UpdateFailed(str(err)) from err
