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
   
Usage on UI:
1. Create a new button for example.

2. Set the action to Call Service.

![Screenshot1](docs/readme1.png)

3. Add target to the action. This can be an entity, a device, or an area (will control all the gree climates in the area).

![Screenshot2](docs/readme2.png)

4. Make the desired changes.

![Screenshot3](docs/readme3.png)
	

## Custom Component Installation

1. Copy the custom_components folder to your own hassio /config folder.

2. In your configuration.yaml add the following:
  
   ```yaml
   gree_ext:
   ```
   