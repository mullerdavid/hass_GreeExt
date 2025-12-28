"""Select platform for Gree extended swing modes."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_platform as ep
from homeassistant.components.gree.const import DOMAIN as GREE_DOMAIN
from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.gree.climate import GreeClimateEntity

_LOGGER = logging.getLogger(__name__)

DOMAIN = "gree_ext"

HORIZONTAL_SWING_OPTIONS = [
    "Default",
    "FullSwing",
    "Left",
    "LeftCenter",
    "Center",
    "RightCenter",
    "Right",
]

VERTICAL_SWING_OPTIONS = [
    "Default",
    "FullSwing",
    "FixedUpper",
    "FixedUpperMiddle",
    "FixedMiddle",
    "FixedLowerMiddle",
    "FixedLower",
    "SwingUpper",
    "SwingUpperMiddle",
    "SwingMiddle",
    "SwingLowerMiddle",
    "SwingLower",
]


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities: AddEntitiesCallback, discovery_info=None
):
    """Set up Gree extended select entities."""
    _LOGGER.info("Setting up Gree extended select platform")
    
    entities = []
    
    # Find all Gree climate entities
    for platform in ep.async_get_platforms(hass, GREE_DOMAIN):
        _LOGGER.debug(f"Found platform: {platform.domain}")
        if platform.domain == CLIMATE_DOMAIN:
            _LOGGER.info(f"Found Gree climate platform with {len(platform.entities)} entities")
            for entity_id, entity in platform.entities.items():
                if isinstance(entity, GreeClimateEntity):
                    _LOGGER.info(f"Creating select entities for {entity_id}")
                    # Create two select entities for each Gree climate
                    entities.append(GreeHorizontalSwingSelect(hass, entity))
                    entities.append(GreeVerticalSwingSelect(hass, entity))
    
    if entities:
        async_add_entities(entities)
        _LOGGER.info(f"Added {len(entities)} Gree swing select entities")
    else:
        _LOGGER.warning("No Gree climate entities found to create selects for")


class GreeSwingSelectBase(SelectEntity):
    """Base class for Gree swing select entities."""

    def __init__(self, hass: HomeAssistant, climate_entity: GreeClimateEntity):
        """Initialize the select."""
        self.hass = hass
        self._climate_entity = climate_entity
        self._attr_should_poll = False
        
        # Link to the same device as the climate entity
        self._attr_device_info = climate_entity.device_info
        
    async def async_added_to_hass(self):
        """When entity is added to hass."""
        # Listen to climate entity state changes to update our state
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
        self._attr_name = f"{climate_entity.name} Horizontal Swing"
        self._attr_icon = "mdi:arrow-left-right"
        
    @property
    def current_option(self) -> str:
        """Return the current selected option."""
        try:
            device = self._climate_entity.coordinator.device
            return device.horizontal_swing.name
        except (AttributeError, KeyError):
            return "Default"
    
    async def async_select_option(self, option: str):
        """Change the selected option."""
        await self.hass.services.async_call(
            DOMAIN,
            "set_swing_mode_ext",
            {
                "entity_id": [self._climate_entity.entity_id],
                "swing_mode_horizontal": option,
            },
        )


class GreeVerticalSwingSelect(GreeSwingSelectBase):
    """Select entity for vertical swing mode."""

    def __init__(self, hass: HomeAssistant, climate_entity: GreeClimateEntity):
        """Initialize the select."""
        super().__init__(hass, climate_entity)
        self._attr_options = VERTICAL_SWING_OPTIONS
        self._attr_unique_id = f"{climate_entity.unique_id}_vertical_swing"
        self._attr_name = f"{climate_entity.name} Vertical Swing"
        self._attr_icon = "mdi:arrow-up-down"
        
    @property
    def current_option(self) -> str:
        """Return the current selected option."""
        try:
            device = self._climate_entity.coordinator.device
            return device.vertical_swing.name
        except (AttributeError, KeyError):
            return "Default"
    
    async def async_select_option(self, option: str):
        """Change the selected option."""
        await self.hass.services.async_call(
            DOMAIN,
            "set_swing_mode_ext",
            {
                "entity_id": [self._climate_entity.entity_id],
                "swing_mode_vertical": option,
            },
        )