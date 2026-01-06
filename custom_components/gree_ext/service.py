import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.gree.climate import GreeClimateEntity
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er, entity_platform as ep
from .const import GREE_DOMAIN, CLIMATE_DOMAIN
from .helpers import set_entity_swing_mode

_LOGGER = logging.getLogger(__name__)

async def async_set_swing_mode_ext(hass: HomeAssistant, call):
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
                if entity.entity_id in entity_id:
                    await set_entity_swing_mode(entity, swing_mode_horizontal, swing_mode_vertical, logger=_LOGGER)
