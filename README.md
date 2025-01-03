# Philips-Airpurifier
For my Philips Airpurifier **AC3259/10** - Original from https://github.com/Kraineff/philips-airpurifier <br /><br />
Specifications for my purifier:
- Modes - Auto, Allergen and Bacteria/Virus mode. 
- Speeds: Sleep, 1, 2, 3 and Turbo. 
- **NOTE:** My purifier dont have humidity so I cant troubleshoot that. 

<br />I will try to keep this code Up-To-Date and fix whatever warnings and errors that I get from HA.

**BREAKING CHANGE:**<br />
Custom service philips_airpurifier.set_mode is replaced by fan.set_preset_mode service
fan.set_speed and fan.set_percentage no longer supported
Presets Night removed
PHILIPS_MODE_SLEEP renamed to PHILIPS_SPEED_SLEEP beacause its a speed and not a mode.

<br />
Modes for AC3259/10 is now fully supported.


## Installation:
Take the folder "philips_airpurifier" and place it in folder "custom_components". 
Restart.
Then copy the yaml down below and place it in configuration.yaml, save and restart. (Remember to change the ip-address to your Philips IP address).
Restart.
Finished.

If you like to have som extra sensors, for example like me to get an notification when its time to change filters. Check sensors-section down below.

## Usage:

```yaml
fan:
  platform: philips_airpurifier
  host: 192.168.0.17
```

## Configuration variables:

| Field    | Value                 | Necessity  | Description                  |
| -------- | --------------------- | ---------- | ---------------------------- |
| platform | `philips_airpurifier` | _Required_ | The platform name.           |
| host     | 192.168.0.17          | _Required_ | IP address of your Purifier. |
| name     | Philips Air Purifier  | Optional   | Name of the Fan.             |

---

## Services

The `philips_airpurifier` integration provides the following custom services:

### `philips_airpurifier.set_mode`

Set the device mode (if supported)

| Field     | Value               | Necessity  | Description                                                             |
| --------- | ------------------- | ---------- | ----------------------------------------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set mode                                     |
| mode      | `"Auto Mode"`       | _Required_ | One of "Auto Mode", "Allergen Mode", "Sleep Mode", "Bacteria", "Night". |

### `philips_airpurifier.set_function`

Set the device function (if supported)

| Field     | Value                             | Necessity  | Description                                               |
| --------- | --------------------------------- | ---------- | --------------------------------------------------------- |
| entity_id | `"fan.living_room"`               | _Required_ | Name(s) of the entities to set function                   |
| function  | `"Purification & Humidification"` | _Required_ | One of "Purification" or "Purification & Humidification". |

### `philips_airpurifier.set_target_humidity`

Set the device target humidity (if supported)

| Field     | Value               | Necessity  | Description                                    |
| --------- | ------------------- | ---------- | ---------------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set target humidity |
| humidity  | `40`                | _Required_ | One of 40, 50, 60                              |

### `philips_airpurifier.set_light_brightness`

Set the device light brightness

| Field     | Value               | Necessity  | Description                                                           |
| --------- | ------------------- | ---------- | --------------------------------------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set light brightness                       |
| level     | `50`                | _Required_ | One of 0, 25, 50, 75, 100. Turns off the display light if level is 0. |

### `philips_airpurifier.set_child_lock`

Set the device child lock on or off

| Field     | Value               | Necessity  | Description                               |
| --------- | ------------------- | ---------- | ----------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set child lock |
| lock      | `true`              | _Required_ | true or false                             |

### `philips_airpurifier.set_timer`

Set the device off time

| Field     | Value               | Necessity  | Description                              |
| --------- | ------------------- | ---------- | ---------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set off timer |
| hours     | `5`                 | _Required_ | Hours between 0 and 12                   |

### `philips_airpurifier.set_display_light`

Set the device display light on or off

| Field     | Value               | Necessity  | Description                                  |
| --------- | ------------------- | ---------- | -------------------------------------------- |
| entity_id | `"fan.living_room"` | _Required_ | Name(s) of the entities to set display light |
| light     | `true`              | _Required_ | true or false                                |


##Use !include in configuration.yaml
```yaml
template: !include templates.yaml
```

## Create sensors from fan.philips_airpurifier: (copy and paste to templates.yaml in config folder)

```yaml
  - sensor:
    - unique_id: "purifier_air_quality"
      name: "Air quality"
      state: >-
        {{ state_attr('fan.philips_airpurifier', 'pm25') }}
    - unique_id: "purifier_speed"
      name: "Speed"
      state: >-
        {{ state_attr('fan.philips_airpurifier', 'speed') }}
    - unique_id: "purifier_allergens"
      name: "Allergen index"
      state: >-
        {{ state_attr('fan.philips_airpurifier', 'allergen_index') }}
    - unique_id: "purifier_pre_filter"
      name: "Pre-filter"
      unit_of_measurement: 'Hrs'
      state: >-
        {{ state_attr('fan.philips_airpurifier', 'pre_filter') }}
    - unique_id: "purifier_carbon_filter"
      name: "Carbon filter"
      unit_of_measurement: 'Hrs'
      state: >-
        {{ state_attr('fan.philips_airpurifier', 'carbon_filter') }}
    - unique_id: "purifier_hepa_filter"
      name: "HEPA filter"
      unit_of_measurement: 'Hrs'
      state: >-
        {{ state_attr('fan.philips_airpurifier', 'hepa_filter') }}
    - unique_id: "purifier_brightness"
      name: "Brightness"
      unit_of_measurement: '%'
      state: >-
        {{ state_attr('fan.philips_airpurifier', 'light_brightness') }}
    - unique_id: "purifier_child_lock"
      name: "Child lock"
      state: >-
        {{ state_attr('fan.philips_airpurifier', 'child_lock') }}
```
