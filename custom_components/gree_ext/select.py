import logging
import re

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_platform as ep
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.components.select import SelectEntity
from homeassistant.components.gree.climate import GreeClimateEntity
from greeclimate.device import HorizontalSwing, VerticalSwing
from .const import DOMAIN, GREE_DOMAIN, CLIMATE_DOMAIN, HORIZONTAL_SWING_OPTIONS, VERTICAL_SWING_OPTIONS
from .helpers import get_climate_base_name, set_entity_swing_mode

# Based on the PR by [Ian C.](https://github.com/ic-dev21). Thank you.

_LOGGER = logging.getLogger(__name__)

def _enum_name_to_option(name: str) -> str:
    """Convert enum names like FixedUpperMiddle to fixed_upper_middle."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    
def _option_to_enum_name(option: str) -> str:
    """Convert snake_case option keys to PascalCase enum names."""
    option = option[:1].upper() + option[1:]
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), option)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up Gree extended select entities from a config entry."""
    _LOGGER.info("Setting up Gree extended select platform")

    select_entities: dict[str, list] = {}

    async def add_selects_for_climate(climate_entity):
        """Create select entities for a Gree climate entity."""
        entity_id = climate_entity.entity_id
        if entity_id in select_entities:
            return
        entities_to_add = [
            GreeHorizontalSwingSelect(hass, climate_entity),
            GreeVerticalSwingSelect(hass, climate_entity),
        ]
        async_add_entities(entities_to_add)
        select_entities[entity_id] = entities_to_add
        _LOGGER.info(f"Creating select entities for {entity_id}")
        
    async def remove_selects_for_climate(entity_id: str):
        """Remove select entities for a given climate entity_id."""
        entities_to_remove = select_entities.pop(entity_id, None)
        if not entities_to_remove:
            return
        for entity in entities_to_remove:
            await entity.async_remove()
        _LOGGER.info(f"Removed select entities for {entity_id}")

    # Add existing devices at startup
    for platform in ep.async_get_platforms(hass, GREE_DOMAIN):
        if platform.domain == CLIMATE_DOMAIN:
            _LOGGER.info(f"Found Gree climate platform with {len(platform.entities)} entities")
            for entity in platform.entities.values():
                if isinstance(entity, GreeClimateEntity):
                    await add_selects_for_climate(entity)
    
    async def _find_live_gree_climate(entity_id: str) -> GreeClimateEntity | None:
        for platform in ep.async_get_platforms(hass, GREE_DOMAIN):
            if platform.domain != CLIMATE_DOMAIN:
                continue
            for live_entity in platform.entities.values():
                if (
                    isinstance(live_entity, GreeClimateEntity)
                    and live_entity.entity_id == entity_id
                ):
                    return live_entity
        return None

    # Handle device add/remove
    async def handle_device_event(event: Event[dr.EventDeviceRegistryUpdatedData]):
        """Handle devices being added, updated, or removed."""
        action = event.data.get("action")
        device_id = event.data.get("device_id")
        if not device_id:
            return

        ent_reg = er.async_get(hass)
        reg_entries = er.async_entries_for_device(ent_reg, device_id)

        climate_entity_ids = [
            entry.entity_id
            for entry in reg_entries
            if entry.domain == CLIMATE_DOMAIN and entry.platform == GREE_DOMAIN
        ]

        if action in ("create", "update"):
            for entity_id in climate_entity_ids:
                live_entity = await _find_live_gree_climate(entity_id)
                if live_entity is None:
                    _LOGGER.debug("Gree climate entity %s not live yet", entity_id)
                    continue
                await add_selects_for_climate(live_entity)

        elif action == "remove":
            for entity_id in climate_entity_ids:
                await remove_selects_for_climate(entity_id)

    hass.bus.async_listen(dr.EVENT_DEVICE_REGISTRY_UPDATED, handle_device_event)

class GreeSwingSelectBase(SelectEntity):
    """Base class for Gree swing select entities."""

    def __init__(self, hass: HomeAssistant, climate_entity: GreeClimateEntity):
        """Initialize the select."""
        self.hass = hass
        self._climate_entity = climate_entity
        self._attr_should_poll = False
        self._base_name = get_climate_base_name(climate_entity)
        # Link to the same device as the climate entity
        self._attr_device_info = climate_entity.device_info

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._climate_entity.coordinator.async_add_listener(
                self._handle_coordinator_update
            )
        )

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class GreeHorizontalSwingSelect(GreeSwingSelectBase):
    """Select entity for horizontal swing mode."""

    def __init__(self, hass: HomeAssistant, climate_entity: GreeClimateEntity):
        """Initialize the select."""
        super().__init__(hass, climate_entity)
        self._attr_options = HORIZONTAL_SWING_OPTIONS
        self._attr_unique_id = f"{climate_entity.unique_id}_horizontal_swing"
        self._attr_name = f"{self._base_name} Horizontal Swing"
        self._attr_icon = "mdi:arrow-left-right"
        self._attr_translation_key = "horizontal_swing"

    @property
    def current_option(self) -> str:
        return _option_to_enum_name(self._current_option())
        
    def _current_option(self) -> str:
        """Return the current selected option."""
        try:
            device = self._climate_entity.coordinator.device
            swing_value = device.horizontal_swing

            # This lets us show the enum name instead of the int value
            if isinstance(swing_value, int):
                swing_enum = HorizontalSwing(swing_value)
                current = swing_enum.name
            else:
                current = swing_value.name

            _LOGGER.debug(f"Horizontal swing for {self._climate_entity.entity_id}: {current}")
            return current
        except (AttributeError, ValueError, KeyError) as e:
            _LOGGER.warning(f"Error reading horizontal swing for {self._climate_entity.entity_id}: {type(e).__name__}: {e}")
            return "Default"

    async def async_select_option(self, option: str):
        await self._async_select_option(_option_to_enum_name(option))
        
    async def _async_select_option(self, option: str):
        """Change the selected option."""
        await set_entity_swing_mode(self._climate_entity, swing_mode_horizontal=option, logger=_LOGGER)


class GreeVerticalSwingSelect(GreeSwingSelectBase):
    """Select entity for vertical swing mode."""

    def __init__(self, hass: HomeAssistant, climate_entity: GreeClimateEntity):
        """Initialize the select."""
        super().__init__(hass, climate_entity)
        self._attr_options = VERTICAL_SWING_OPTIONS
        self._attr_unique_id = f"{climate_entity.unique_id}_vertical_swing"
        self._attr_name = f"{self._base_name} Vertical Swing"
        self._attr_icon = "mdi:arrow-up-down"
        self._attr_translation_key = "vertical_swing"

    @property
    def current_option(self) -> str:
        return _option_to_enum_name(self._current_option())
        
    def _current_option(self) -> str:
        """Return the current selected option."""
        try:
            device = self._climate_entity.coordinator.device
            swing_value = device.vertical_swing

            # This lets us show the enum name instead of the int value
            if isinstance(swing_value, int):
                swing_enum = VerticalSwing(swing_value)
                current = swing_enum.name
            else:
                current = swing_value.name

            _LOGGER.debug(f"Vertical swing for {self._climate_entity.entity_id}: {current}")
            return current
        except (AttributeError, ValueError, KeyError) as e:
            _LOGGER.warning(f"Error reading vertical swing for {self._climate_entity.entity_id}: {type(e).__name__}: {e}")
            return "Default"

    async def async_select_option(self, option: str):
        await self._async_select_option(_option_to_enum_name(option))
        
    async def _async_select_option(self, option: str):
        """Change the selected option."""
        await set_entity_swing_mode(self._climate_entity, swing_mode_vertical=option, logger=_LOGGER)
