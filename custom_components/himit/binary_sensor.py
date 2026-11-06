"""Binary sensor platform for Hi-Mit II — read-only status indicators."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .coordinator import HimitCoordinator
from .entity import HimitEntity
from .telemetry import binary_value


@dataclass(frozen=True)
class HimitBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a Hi-Mit II binary sensor."""
    field: str = ""
    experimental: bool = False


BINARY_SENSOR_DESCRIPTIONS: tuple[HimitBinarySensorDescription, ...] = (
    HimitBinarySensorDescription(
        key="a2w_running",
        translation_key="a2w_running",
        field="A2W_SW_ON",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:heat-pump",
    ),
)

# Present in a real cloud snapshot; meaning/polarity still needs event validation.
EXPERIMENTAL_BINARY_SENSOR_DESCRIPTIONS = tuple(
    HimitBinarySensorDescription(
        key=key,
        translation_key=key,
        field=field,
        experimental=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:flask-outline",
    )
    for key, name, field in (
        ("defrost_spaceheat", "Space heating defrost", "Defrost_Spaceheat_s"),
        ("defrost_dhw", "DHW defrost", "Defrost_DHW_s"),
        ("antifrozen_hp", "Heat pump frost protection", "Antifrozen_HP_s"),
        ("antifrozen_wp1_1", "Water pump frost protection 1", "1_Antifrozen_WP1_s"),
        ("antifrozen_wp1_2", "Water pump frost protection 2", "2_Antifrozen_WP1_s"),
        ("antifrozen_eh1", "Heater frost protection", "Antifrozen_EH1_s"),
        ("eco_mode", "ECO mode", "isECO"),
        ("night_mode", "Night mode", "isNightMode"),
        ("silent_mode", "Quiet mode", "isSilentMode"),
        ("electric_heating", "Electric heating flag", "isEleHeatingTurnon"),
        ("disinfection", "Disinfection flag", "isDisinfect"),
        ("anti_legionella", "Anti Legionella flag", "Anti_Legionella_s"),
        ("dhw_boost", "DHW boost flag", "DHW_Boost_s"),
        ("emergency_mode", "Emergency mode flag", "Emergency_Mode_s"),
    )
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HimitCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        HimitBinarySensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in (
            *BINARY_SENSOR_DESCRIPTIONS, *EXPERIMENTAL_BINARY_SENSOR_DESCRIPTIONS
        )
    ]
    async_add_entities(entities)


class HimitBinarySensor(HimitEntity, BinarySensorEntity):
    """A read-only binary status sensor for Hi-Mit II."""

    entity_description: HimitBinarySensorDescription

    def __init__(
        self,
        coordinator: HimitCoordinator,
        device_id: str,
        description: HimitBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        if self.entity_description.experimental:
            return binary_value(self._device_data.get(self.entity_description.field))
        return self._device_data.get(self.entity_description.field)

    @property
    def extra_state_attributes(self) -> dict | None:
        if not self.entity_description.experimental:
            return None
        return {
            "source_field": self.entity_description.field,
            "mapping_confidence": "experimental",
        }

    @property
    def available(self) -> bool:
        return (
            super().available
            and self._device_id in self.coordinator.data
            and self.is_on is not None
        )
