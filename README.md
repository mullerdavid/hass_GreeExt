# hass_GreeExt
Gree Extension for Home-Assistant built in integration

Allows setting different swing positions for the default Gree integration.

Usage:
   ```yaml
   service: gree_ext.set_swing_mode_ext
   target:
     entity_id: climate.eeeeffff
   data:
     swing_mode_vertical: FixedMiddle
   ```

## Custom Component Installation

1. Copy the custom_components folder to your own hassio /config folder.

2. In your configuration.yaml add the following:
  
   ```yaml
   gree_ext:
   ```
   