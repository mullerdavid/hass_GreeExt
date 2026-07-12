"""The "Gree climate extension" custom component."""

import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, SERVICE_SET_SWING_MODE_EXT
from .service import async_set_swing_mode_ext

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gree Climate Extension from a config entry."""

    @callback
    async def async_set_swing_mode_ext_callback(call):
        """Set swing mode extended."""
        await async_set_swing_mode_ext(hass, call)

    hass.services.async_register(DOMAIN, SERVICE_SET_SWING_MODE_EXT, async_set_swing_mode_ext_callback)

    await hass.config_entries.async_forward_entry_setups(entry, ["select"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(DOMAIN, SERVICE_SET_SWING_MODE_EXT)
    return await hass.config_entries.async_unload_platforms(entry, ["select"])
