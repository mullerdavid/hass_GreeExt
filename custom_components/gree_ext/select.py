import logging

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_platform as ep
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.components.select import SelectEntity
from homeassistant.components.gree.climate import GreeClimateEntity
from greeclimate.device import HorizontalSwing, VerticalSwing
from .const import DOMAIN, GREE_DOMAIN, CLIMATE_DOMAIN, SERVICE_SET_SWING_MODE_EXT, HORIZONTAL_SWING_OPTIONS, VERTICAL_SWING_OPTIONS
from .helpers import get_climate_base_name, set_entity_swing_mode

# Based on the PR by [Ian C.](https://github.com/ic-dev21). Thank you.

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities: AddEntitiesCallback, discovery_info=None
):
    """Set up Gree extended select entities."""
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
    
    # Handle device add/remove
    async def handle_device_event(event: Event[dr.EventDeviceRegistryUpdatedData]):
        """Handle devices being added, updated, or removed."""
        action = event.data.get("action")
        did = event.data.get("device_id")
        if not did:
            return
        ent_reg = er.async_get(hass)
        for entity in er.async_entries_for_device(ent_reg,did):
            if not isinstance(entity, GreeClimateEntity):
                continue
            if action == "create":
                await add_selects_for_climate(entity)
            elif action == "remove":
                await remove_selects_for_climate(entity.entity_id)

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

    @property
    def current_option(self) -> str:
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

    @property
    def current_option(self) -> str:
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
        """Change the selected option."""
        await set_entity_swing_mode(self._climate_entity, swing_mode_vertical=option, logger=_LOGGER)
