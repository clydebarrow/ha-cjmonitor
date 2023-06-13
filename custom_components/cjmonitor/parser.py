"""Parser for CJ Monitor BLE advertisements.

MIT License applies.
"""
from __future__ import annotations

import logging
import struct

from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import SensorLibrary
from const import CJ_MANUF_ID

_LOGGER = logging.getLogger(__name__)

MODELS = [4350, 4351]


def mulaw_to_value(mudata):
    """Convert a mu-law encoded value to linear."""
    position = ((mudata & 0xF0) >> 4) + 5
    return ((1 << position) | ((mudata & 0xF) << (position - 4)) | (1 << (position - 5))) - 33


class CJMonBLEData(BluetoothData):
    """Data update for CJ Monitor Bluetooth devices."""

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Update from BLE advertisement data."""
        _LOGGER.debug("Parsing CJMon BLE advertisement data: %s", service_info)
        manufacturer_data = service_info.manufacturer_data

        if not manufacturer_data:
            return

        data = manufacturer_data[CJ_MANUF_ID]
        if not data:
            return
        msg_length = len(data)
        if msg_length < 6:
            return
        (model, temp, hum, light) = struct.Struct("<HhBB").unpack(data[0:6])
        if model not in MODELS:
            return
        _LOGGER.debug("Parsing CJMonitor BLE advertisement data: %s", data)
        self.set_device_manufacturer("Control-J")
        local_name = service_info.name
        self.set_device_name(local_name)
        self.update_predefined_sensor(SensorLibrary.TEMPERATURE__CELSIUS, temp / 10.0)
        self.update_predefined_sensor(SensorLibrary.HUMIDITY__PERCENTAGE, hum)
        self.update_predefined_sensor(SensorLibrary.LIGHT__LIGHT_LUX, mulaw_to_value(light))
        self.set_device_type(f"CJMon-{model}")
        if msg_length == 10:
            (battery, pressure, bits) = struct.Struct("<BHB").unpack(data[6:10])
            self.update_predefined_sensor(SensorLibrary.PRESSURE__MBAR, pressure)
            self.update_predefined_sensor(SensorLibrary.BATTERY__PERCENTAGE, battery)
