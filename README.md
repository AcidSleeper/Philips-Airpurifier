# Philips-Airpurifier
For my Philips Airpurifier AC3259/10 - Original from https://github.com/Kraineff/philips-airpurifier


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
