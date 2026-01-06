from homeassistant.components.gree.const import DOMAIN as gd
from homeassistant.components.climate.const import DOMAIN as cd
from greeclimate.device import HorizontalSwing, VerticalSwing

DOMAIN = "gree_ext"
GREE_DOMAIN = gd
CLIMATE_DOMAIN = cd

SIGNAL_NEW_GREE_DEVICE = DOMAIN + "_new_gree_device"

SERVICE_SET_SWING_MODE_EXT = "set_swing_mode_ext"

HORIZONTAL_SWING_OPTIONS = [e.name for e in sorted(HorizontalSwing, key=lambda x: x.value)]
VERTICAL_SWING_OPTIONS = [e.name for e in sorted(VerticalSwing, key=lambda x: x.value)]
