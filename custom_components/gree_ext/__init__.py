"""
The "Gree climate extension" custom component.

This component implements the different swing types not configurable with the built in climate.

Configuration:

To use the component you will need to add the following to your
configuration.yaml file.

gree_ext:
"""

import logging

from homeassistant.core import callback
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er, entity_platform as ep
from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.gree.const import DOMAIN as GREE_DOMAIN
from homeassistant.components.gree.climate import GreeClimateEntity
from greeclimate.device import HorizontalSwing, VerticalSwing

_LOGGER = logging.getLogger(__name__)

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "gree_ext"


async def async_setup(hass, config):
    """Setup our component."""
	
    @callback
    async def async_set_swing_mode_ext(call):
        """Set swing mode extended."""
        swing_mode_horizontal = call.data.get("swing_mode_horizontal", None)
        swing_mode_vertical = call.data.get("swing_mode_vertical", None)
        area_id = call.data.get("area_id", [])
        device_id = call.data.get("device_id", [])
        entity_id = call.data.get("entity_id", [])
        dev_reg = dr.async_get(hass)
        ent_reg = er.async_get(hass)
        for aid in area_id:
            for dev in dr.async_entries_for_area(dev_reg,aid):
                if dev.id not in device_id:
                    device_id.append(dev.id)
        for did in device_id:
            for ent in er.async_entries_for_device(ent_reg,did):
                if ent.entity_id not in entity_id:
                    entity_id.append(ent.entity_id)
        for platform in ep.async_get_platforms(hass, GREE_DOMAIN):
            if platform.domain == CLIMATE_DOMAIN:
                for eid, entity in platform.entities.items():
                    if entity.entity_id in entity_id and isinstance(entity, GreeClimateEntity):
                        _LOGGER.warning( "Setting switng mode for entity (%s) to %s/%s", entity.entity_id, str(swing_mode_horizontal), str(swing_mode_vertical))
                        greeclimate = entity.coordinator.device
                        if swing_mode_horizontal:
                            try:
                                greeclimate.horizontal_swing = HorizontalSwing[swing_mode_horizontal]
                            except KeyError:
                                _LOGGER.debug("Invalid swing_mode_horizontal mode: %s", swing_mode_horizontal)
                        if swing_mode_vertical:
                            try:
                                greeclimate.vertical_swing = VerticalSwing[swing_mode_vertical]
                            except KeyError:
                                _LOGGER.debug("Invalid swing_mode_vertical mode: %s", swing_mode_vertical)
                        await greeclimate.push_state_update()
                        entity.async_write_ha_state()
	
    hass.services.async_register(DOMAIN, 'set_swing_mode_ext', async_set_swing_mode_ext)
    
    # Return boolean to indicate that initialization was successfully.
    return True
