from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PagePlanConfigEntry
from .const import DOMAIN, INTEGRATION_NAME
from .coordinator import PagePlanCoordinator, PagePlanData


@dataclass(frozen=True, kw_only=True)
class PagePlanSensorDescription(SensorEntityDescription):
    value_fn: Callable[[PagePlanData], int | str | date | None]


SENSORS = (
    PagePlanSensorDescription(
        key="subscription_impressions",
        translation_key="subscription_impressions",
        native_unit_of_measurement="pages",
        icon="mdi:counter",
        value_fn=lambda d: d.printer.subscription_impressions,
    ),
    PagePlanSensorDescription(
        key="pages_used_cycle",
        translation_key="pages_used_cycle",
        native_unit_of_measurement="pages",
        icon="mdi:printer",
        value_fn=lambda d: d.pages_used_cycle,
    ),
    PagePlanSensorDescription(
        key="monthly_remaining",
        translation_key="monthly_remaining",
        native_unit_of_measurement="pages",
        icon="mdi:file-document-outline",
        value_fn=lambda d: d.monthly_remaining,
    ),
    PagePlanSensorDescription(
        key="rollover_remaining",
        translation_key="rollover_remaining",
        native_unit_of_measurement="pages",
        icon="mdi:archive-outline",
        value_fn=lambda d: d.rollover_remaining,
    ),
    PagePlanSensorDescription(
        key="total_remaining",
        translation_key="total_remaining",
        native_unit_of_measurement="pages",
        icon="mdi:file-document-multiple-outline",
        value_fn=lambda d: d.total_remaining,
    ),
    PagePlanSensorDescription(
        key="next_renewal",
        translation_key="next_renewal",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:calendar-refresh",
        value_fn=lambda d: d.next_renewal,
    ),
    PagePlanSensorDescription(
        key="ink_black",
        translation_key="ink_black",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:water-opacity",
        value_fn=lambda d: d.printer.ink_black,
    ),
    PagePlanSensorDescription(
        key="ink_cyan",
        translation_key="ink_cyan",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:water-opacity",
        value_fn=lambda d: d.printer.ink_cyan,
    ),
    PagePlanSensorDescription(
        key="ink_magenta",
        translation_key="ink_magenta",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:water-opacity",
        value_fn=lambda d: d.printer.ink_magenta,
    ),
    PagePlanSensorDescription(
        key="ink_yellow",
        translation_key="ink_yellow",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:water-opacity",
        value_fn=lambda d: d.printer.ink_yellow,
    ),
)


async def async_setup_entry(hass, entry: PagePlanConfigEntry, async_add_entities) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        PagePlanSensor(coordinator, entry, description) for description in SENSORS
    )


class PagePlanSensor(CoordinatorEntity[PagePlanCoordinator], SensorEntity):
    entity_description: PagePlanSensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=INTEGRATION_NAME,
            manufacturer="HP Inc.",
            model="Compatible LEDM printer",
        )

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if data is None or self.entity_description.key != "total_remaining":
            return None
        return {
            "monthly_plan": data.monthly_pages,
            "rollover_cap": data.rollover_max,
            "monthly_remaining": data.monthly_remaining,
            "rollover_remaining": data.rollover_remaining,
            "next_renewal": data.next_renewal.isoformat(),
            "renewal_uncertain": data.renewal_uncertain,
        }
