"""
The "Gree climate extension" custom component.

This component implements the different swing types not configurable with the built in climate.

Configuration:

To use the component you will need to add the following to your
configuration.yaml file.

gree_ext:
"""

import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN, GREE_DOMAIN, SERVICE_SET_SWING_MODE_EXT
from .service import async_set_swing_mode_ext

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config):
    """Setup our component."""

    # Set up the service
    @callback
    async def async_set_swing_mode_ext_callback(call):
        """Set swing mode extended."""
        await async_set_swing_mode_ext(hass, call)
	
    hass.services.async_register(DOMAIN, SERVICE_SET_SWING_MODE_EXT, async_set_swing_mode_ext_callback)

    # Set up the select platform
    hass.async_create_task(
        async_load_platform(hass, "select", DOMAIN, {}, config)
    )
    
    # Return boolean to indicate that initialization was successfully.
    return True
