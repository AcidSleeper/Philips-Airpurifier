"""Support for Phillips Air Purifiers and Humidifiers."""

import json
import logging
import random
from typing import Any, Optional
import urllib.request

import voluptuous as vol

from homeassistant.components.fan import (
    FanEntity,
    PLATFORM_SCHEMA,
    SUPPORT_PRESET_MODE,
)

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
)

import homeassistant.helpers.config_validation as cv

from .crypto import (
    G,
    P,
    aes_decrypt,
    decrypt,
    encrypt,
)

from .const import *

__version__ = '0.3.5'

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

AIRPURIFIER_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(SERVICE_ATTR_ENTITY_ID): cv.entity_ids}
)

SERVICE_SET_FUNCTION_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_FUNCTION): vol.In(FUNCTION_MAP.values())}
)

SERVICE_SET_TARGET_HUMIDITY_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(SERVICE_ATTR_HUMIDITY):
            vol.All(vol.Coerce(int), vol.In(TARGET_HUMIDITY_LIST))
    }
)

SERVICE_SET_LIGHT_BRIGHTNESS_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(SERVICE_ATTR_BRIGHTNESS_LEVEL):
            vol.All(vol.Coerce(int), vol.In(LIGHT_BRIGHTNESS_LIST))
    }
)

SERVICE_SET_CHILD_LOCK_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_CHILD_LOCK): cv.boolean}
)

SERVICE_SET_TIMER_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(SERVICE_ATTR_TIMER_HOURS): vol.All(
            vol.Coerce(int),
            vol.Number(scale=0),
            vol.Range(min=0, max=12)
        )
    }
)

SERVICE_SET_DISPLAY_LIGHT_SCHEMA = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(SERVICE_ATTR_DISPLAY_LIGHT): cv.boolean}
)

AIR_PURIFIER_SERVICES = {
    SERVICE_SET_FUNCTION: SERVICE_SET_FUNCTION_SCHEMA,
    SERVICE_SET_TARGET_HUMIDITY: SERVICE_SET_TARGET_HUMIDITY_SCHEMA,
    SERVICE_SET_LIGHT_BRIGHTNESS: SERVICE_SET_LIGHT_BRIGHTNESS_SCHEMA,
    SERVICE_SET_CHILD_LOCK: SERVICE_SET_CHILD_LOCK_SCHEMA,
    SERVICE_SET_TIMER: SERVICE_SET_TIMER_SCHEMA,
    SERVICE_SET_DISPLAY_LIGHT: SERVICE_SET_DISPLAY_LIGHT_SCHEMA,
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the philips_airpurifier platform."""
    device = PhilipsAirPurifierFan(hass, config)

    if DATA_PHILIPS_FANS not in hass.data:
        hass.data[DATA_PHILIPS_FANS] = []

    hass.data[DATA_PHILIPS_FANS].append(device)

    add_entities(hass.data[DATA_PHILIPS_FANS])

    def service_handler(service):
        entity_ids = service.data.get(SERVICE_ATTR_ENTITY_ID)

        # Params to set to method handler. Drop entity_id.
        params = {
            key: value for key, value in service.data.items() if key != SERVICE_ATTR_ENTITY_ID
        }

        if entity_ids:
            devices = [
                device
                for device in hass.data[DATA_PHILIPS_FANS]
                if device.entity_id in entity_ids
            ]
        else:
            devices = hass.data[DATA_PHILIPS_FANS]

        for device in devices:
            # Use the same method name as the service name.
            # Assumes that if there's a service "set_mode", device will have a "set_mode" method.
            if not hasattr(device, service.service):
                continue
            getattr(device, service.service)(**params)

    for service, schema in AIR_PURIFIER_SERVICES.items():
        hass.services.register(DOMAIN, service, service_handler, schema=schema)


class PhilipsAirPurifierFan(FanEntity):
    """philips_aurpurifier fan entity."""

    def __init__(self, hass, config):
        self.hass = hass
        self._host = config[CONF_HOST]
        self._name = config[CONF_NAME]

        self._unique_id = None
        self._available = False
        self._state = None
        self._model = None
        self._session_key = None

        self._fan_speed = None
        self._fan_preset_mode = None

        self._pre_filter = None
        self._wick_filter = None
        self._carbon_filter = None
        self._hepa_filter = None

        self._pm25 = None
        self._humidity = None
        self._target_humidity = None
        self._allergen_index = None
        self._temperature = None
        self._function = None
        self._light_brightness = None
        self._display_light = None
        self._used_index = None
        self._water_level = None
        self._child_lock = None
        self._timer = None
        self._timer_remaining = None

        self.update()

    ### Update Fan attributes ###

    def update(self):
        """Fetch state from device."""
        try:
            self._update_filters()
            self._update_state()
            self._update_model()
            self._available = True
        except Exception:
            self._available = False

    def _update_filters(self):
        url = 'http://{}/di/v1/products/1/fltsts'.format(self._host)
        filters = self._get(url)
        self._pre_filter = filters['fltsts0']
        if 'wicksts' in filters:
            self._wick_filter = filters['wicksts']
        self._carbon_filter = filters['fltsts2']
        self._hepa_filter = filters['fltsts1']

    def _update_model(self):
        url = 'http://{}/di/v1/products/0/firmware'.format(self._host)
        firmware = self._get(url)
        if PHILIPS_MODEL_NAME in firmware:
            self._model = firmware[PHILIPS_MODEL_NAME]

        url = 'http://{}/di/v1/products/0/wifi'.format(self._host)
        wifi = self._get(url)
        if PHILIPS_MAC_ADDRESS in wifi:
            self._unique_id = wifi[PHILIPS_MAC_ADDRESS]

    def _update_state(self):
        url = 'http://{}/di/v1/products/1/air'.format(self._host)
        self._assign_philips_states(self._get(url))
    
    def _assign_philips_states(self, data: dict) -> None:
        if PHILIPS_POWER in data:
            self._state = 'on' if data[PHILIPS_POWER] == '1' else 'off'
        if PHILIPS_PM25 in data:
            self._pm25 = data[PHILIPS_PM25]
        if PHILIPS_HUMIDITY in data:
            self._humidity = data[PHILIPS_HUMIDITY]
        if PHILIPS_TARGET_HUMIDITY in data:
            self._target_humidity = data[PHILIPS_TARGET_HUMIDITY]
        if PHILIPS_ALLERGEN_INDEX in data:
            self._allergen_index = data[PHILIPS_ALLERGEN_INDEX]
        if PHILIPS_TEMPERATURE in data:
            self._temperature = data[PHILIPS_TEMPERATURE]
        if PHILIPS_FUNCTION in data:
            func = data[PHILIPS_FUNCTION]
            self._function = FUNCTION_MAP.get(func, func)
        if PHILIPS_MODE in data:
            mode = data[PHILIPS_MODE]
            self._fan_preset_mode = MODE_MAP.get(mode, mode)
        if PHILIPS_SPEED in data:
            speed = data[PHILIPS_SPEED]
            speed = SPEED_MAP.get(speed, speed)
            if self._fan_preset_mode == PHILIPS_MODE_MANUAL:
                if speed != PHILIPS_SPEED_OFF:
                    self._fan_speed = speed
                self._fan_preset_mode = self._fan_speed
        if PHILIPS_LIGHT_BRIGHTNESS in data:
            self._light_brightness = data[PHILIPS_LIGHT_BRIGHTNESS]
        if PHILIPS_DISPLAY_LIGHT in data:
            display_light = data[PHILIPS_DISPLAY_LIGHT]
            self._display_light = DISPLAY_LIGHT_MAP.get(
                display_light, display_light)
        if PHILIPS_USED_INDEX in data:
            ddp = data[PHILIPS_USED_INDEX]
            self._used_index = USED_INDEX_MAP.get(ddp, ddp)
        if PHILIPS_WATER_LEVEL in data:
            self._water_level = data[PHILIPS_WATER_LEVEL]
        if PHILIPS_CHILD_LOCK in data:
            self._child_lock = data[PHILIPS_CHILD_LOCK]
        if PHILIPS_TIMER in data:
            self._timer = data[PHILIPS_TIMER]
        if PHILIPS_TIMER_REMAINING in data:
            self._timer_remaining = data[PHILIPS_TIMER_REMAINING]

    ### Properties ###

    @property
    def is_on(self):
        return self._state is 'on'

    @property
    def state(self):
        """Return device state."""
        return self._state

    @property
    def available(self):
        """Return True when state is known."""
        return self._available

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def icon(self):
        """Return the default icon for the device."""
        return DEFAULT_ICON

    @property
    def preset_mode(self) -> str:
        """Return the current preset_mode. One of the values in preset_modes or None if no preset is active."""
        return self._fan_preset_mode

    @property
    def preset_modes(self) -> list:
        """Get the list of available preset_modes. This is an arbitrary list of str and should not contain any speeds."""
        return SUPPORTED_PRESET_LIST

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_PRESET_MODE

    def turn_on(self, speed: Optional[str] = None, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        """Turn on the fan."""
        if preset_mode is not None:
            self.set_preset_mode(preset_mode, True)
        else:
            values = {PHILIPS_POWER: '1'}
            self.set_values(values)

    def turn_off(self, **kwargs) -> None:
        """Turn off the fan."""
        values = {PHILIPS_POWER: '0'}
        self.set_values(values)

    def set_preset_mode(self, preset_mode: str, turn_on: bool = False) -> None:
        """Set the preset mode of the fan."""
        values = {}
        if turn_on:
            values.update({PHILIPS_POWER: '1'})
        if preset_mode == self._fan_preset_mode:
            """Nothing to change"""
        elif preset_mode in SPEED_MAP.values():
            self._fan_speed = preset_mode
            philips_speed = self._find_key(SPEED_MAP, preset_mode)
            values.update({PHILIPS_MODE: PHILIPS_MODE_MANUAL, PHILIPS_SPEED: philips_speed})
        elif preset_mode in MODE_MAP.values():
            philips_mode = self._find_key(MODE_MAP, preset_mode)
            values.update({PHILIPS_MODE: philips_mode})
        else:
            _LOGGER.warning("Unsupported preset %s", preset_mode)

        if values:
            self.set_values(values)

    def set_function(self, function: str):
        """Set the function of the fan."""
        if function == self._function:
            return

        philips_function = self._find_key(FUNCTION_MAP, function)
        self.set_values({PHILIPS_FUNCTION: philips_function})

    def set_target_humidity(self, humidity: int):
        """Set the target humidity of the fan."""
        if humidity == self._target_humidity:
            return

        self.set_values({PHILIPS_TARGET_HUMIDITY: humidity})

    def set_light_brightness(self, level: int):
        """Set the light brightness of the fan."""
        if level == self._light_brightness:
            return

        values = {}
        values[PHILIPS_LIGHT_BRIGHTNESS] = level
        values[PHILIPS_DISPLAY_LIGHT] = self._find_key(
            DISPLAY_LIGHT_MAP, level != 0)
        self.set_values(values)

    def set_child_lock(self, lock: bool):
        """Set the child lock of the fan."""
        if lock == self._child_lock:
            return

        self.set_values({PHILIPS_CHILD_LOCK: lock})

    def set_timer(self, hours: int):
        """Set the off timer of the fan."""

        self.set_values({PHILIPS_TIMER: hours})

    def set_display_light(self, light: bool):
        """Set the display light of the fan."""
        if light == self._display_light:
            return

        light = self._find_key(DISPLAY_LIGHT_MAP, light)
        self.set_values({PHILIPS_DISPLAY_LIGHT: light})

    @property
    def extra_state_attributes(self):
        """Extra information to store in the state machine. It needs to be information that further explains the state, it should not be static information like firmware version."""
        attr = {}

        if self._model is not None:
            attr[ATTR_MODEL] = self._model
        if self._function is not None:
            attr[ATTR_FUNCTION] = self._function
        if self._used_index is not None:
            attr[ATTR_USED_INDEX] = self._used_index
        if self._pm25 is not None:
            attr[ATTR_PM25] = self._pm25
        if self._allergen_index is not None:
            attr[ATTR_ALLERGEN_INDEX] = self._allergen_index
        if self._temperature is not None:
            attr[ATTR_TEMPERATURE] = self._temperature
        if self._humidity is not None:
            attr[ATTR_HUMIDITY] = self._humidity
        if self._target_humidity is not None:
            attr[ATTR_TARGET_HUMIDITY] = self._target_humidity
        if self._water_level is not None:
            attr[ATTR_WATER_LEVEL] = self._water_level
        if self._light_brightness is not None:
            attr[ATTR_LIGHT_BRIGHTNESS] = self._light_brightness
        if self._display_light is not None:
            attr[ATTR_DISPLAY_LIGHT] = self._display_light
        if self._child_lock is not None:
            attr[ATTR_CHILD_LOCK] = self._child_lock
        if self._timer is not None:
            attr[ATTR_TIMER] = self._timer
        if self._timer_remaining is not None:
            attr[ATTR_TIMER_REMAINGING_MINUTES] = self._timer_remaining
        if self._pre_filter is not None:
            attr[ATTR_PRE_FILTER] = self._pre_filter
        if self._wick_filter is not None:
            attr[ATTR_WICK_FILTER] = self._wick_filter
        if self._carbon_filter is not None:
            attr[ATTR_CARBON_FILTER] = self._carbon_filter
        if self._hepa_filter is not None:
            attr[ATTR_HEPA_FILTER] = self._hepa_filter

        return attr

    ### Other methods ###

    def set_values(self, values):
        """Update device state."""
        body = encrypt(values, self._session_key)
        url = 'http://{}/di/v1/products/1/air'.format(self._host)
        req = urllib.request.Request(url=url, data=body, method='PUT')
        with urllib.request.urlopen(req) as response:
            resp = response.read()
            resp = decrypt(resp.decode('ascii'), self._session_key)
            self._assign_philips_states(json.loads(resp))
            self.schedule_update_ha_state()

    def _get_key(self):
        # pylint: disable=invalid-name
        url = 'http://{}/di/v1/products/0/security'.format(self._host)
        a = random.getrandbits(256)
        A = pow(G, a, P)
        data = json.dumps({'diffie': format(A, 'x')})
        data_enc = data.encode('ascii')
        req = urllib.request.Request(url=url, data=data_enc, method='PUT')
        with urllib.request.urlopen(req) as response:
            resp = response.read().decode('ascii')
            dh = json.loads(resp)
        key = dh['key']
        B = int(dh['hellman'], 16)
        s = pow(B, a, P)
        s_bytes = s.to_bytes(128, byteorder='big')[:16]
        session_key = aes_decrypt(bytes.fromhex(key), s_bytes)
        self._session_key = session_key[:16]

    def _get_once(self, url):
        with urllib.request.urlopen(url) as response:
            resp = response.read()
            resp = decrypt(resp.decode('ascii'), self._session_key)
            return json.loads(resp)

    def _get(self, url):
        try:
            return self._get_once(url)
        except Exception:
            self._get_key()
            return self._get_once(url)

    def _find_key(self, value_map, search_value):
        if search_value in value_map.values():
            return [key for key, value in value_map.items() if value == search_value][0]

        return None