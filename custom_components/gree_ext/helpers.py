
from logging import Logger
from homeassistant.components.gree.climate import GreeClimateEntity
from greeclimate.device import HorizontalSwing, VerticalSwing

def get_climate_base_name(climate_entity: GreeClimateEntity):
    # Get a better name - use the device name from coordinator if entity name is None
    base_name = climate_entity.name
    if base_name is None or base_name == "None":
        try:
            # Try to get name from the device info
            if climate_entity.device_info and "name" in climate_entity.device_info:
                base_name = climate_entity.device_info["name"]
            else:
                # Fallback to coordinator device name
                base_name = climate_entity.coordinator.device.device_info.name
        except (AttributeError, KeyError):
            # Last resort - use entity_id
            base_name = climate_entity.entity_id.replace("climate.", "").replace("_", " ").title()
    return base_name

async def set_entity_swing_mode(entity: GreeClimateEntity, swing_mode_horizontal: str|None = None, swing_mode_vertical: str|None = None, logger: Logger|None = None):
    if isinstance(entity, GreeClimateEntity):
        if logger:
            logger.info( f"Setting swing mode for entity ({entity.entity_id}) to {str(swing_mode_horizontal)}/{str(swing_mode_vertical)}")
        greeclimate = entity.coordinator.device
        if swing_mode_horizontal:
            try:
                greeclimate.horizontal_swing = HorizontalSwing[swing_mode_horizontal]
            except KeyError:
                if logger:
                    logger.warning(f"Invalid swing_mode_horizontal mode: {swing_mode_horizontal}")
        if swing_mode_vertical:
            try:
                greeclimate.vertical_swing = VerticalSwing[swing_mode_vertical]
            except KeyError:
                if logger:
                    logger.warning(f"Invalid swing_mode_vertical mode: {swing_mode_vertical}")
        await greeclimate.push_state_update()
        entity.async_write_ha_state()
    else:
        if logger:
            logger.warning(f"Invalid entity: {str(entity)} ({type(entity).__name__ })")

