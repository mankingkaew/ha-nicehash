"""
Sensor platform for NiceHash
"""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import Config, HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import (
    BALANCE_TYPE_AVAILABLE,
    BALANCE_TYPE_PENDING,
    BALANCE_TYPE_TOTAL,
    CURRENCY_BTC,
    CURRENCY_EUR,
    CURRENCY_USD,
    DOMAIN,
    DEVICE_LOAD,
    DEVICE_RPM,
    DEVICE_SPEED_RATE,
    DEVICE_SPEED_ALGORITHM,
)
from .nicehash import NiceHashPrivateClient, NiceHashPublicClient
from .account_sensors import BalanceSensor
from .rig_sensors import (
    RigStatusSensor,
    RigTemperatureSensor,
    RigProfitabilitySensor,
)
from .device_sensors import (
    DeviceAlgorithmSensor,
    DeviceSpeedSensor,
    DeviceStatusSensor,
    DeviceLoadSensor,
    DeviceRPMSensor,
    DeviceTemperatureSensor,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant, config: Config, async_add_entities, discovery_info=None
):
    """Setup NiceHash sensor platform"""
    _LOGGER.debug("Creating new NiceHash sensor components")

    data = hass.data[DOMAIN]
    # Configuration
    organization_id = data.get("organization_id")
    client = data.get("client")
    # Options
    currency = data.get("currency")
    rigs_enabled = data.get("rigs_enabled")
    devices_enabled = data.get("devices_enabled")

    # Add account balance sensors
    accounts_coordinator = data.get("accounts_coordinator")
    balance_sensors = create_balance_sensors(
        organization_id, currency, accounts_coordinator
    )
    async_add_entities(balance_sensors, True)

    if rigs_enabled or devices_enabled:
        rigs_coordinator = data.get("rigs_coordinator")
        rig_data = await client.get_mining_rigs()
        mining_rigs = rig_data.get("miningRigs")

        # Add mining rig sensors if enabled
        if rigs_enabled:
            rig_sensors = create_rig_sensors(mining_rigs, rigs_coordinator)
            async_add_entities(rig_sensors, True)

        # Add device sensors if enabled
        if devices_enabled:
            device_sensors = create_device_sensors(mining_rigs, rigs_coordinator)
            async_add_entities(device_sensors, True)


def create_balance_sensors(organization_id, currency, coordinator):
    balance_sensors = [
        BalanceSensor(
            coordinator,
            organization_id,
            currency=CURRENCY_BTC,
            balance_type=BALANCE_TYPE_AVAILABLE,
        ),
        BalanceSensor(
            coordinator,
            organization_id,
            currency=CURRENCY_BTC,
            balance_type=BALANCE_TYPE_PENDING,
        ),
        BalanceSensor(
            coordinator,
            organization_id,
            currency=CURRENCY_BTC,
            balance_type=BALANCE_TYPE_TOTAL,
        ),
    ]
    if currency == CURRENCY_USD or currency == CURRENCY_EUR:
        balance_sensors.append(
            BalanceSensor(
                coordinator,
                organization_id,
                currency=currency,
                balance_type=BALANCE_TYPE_AVAILABLE,
            )
        )
        balance_sensors.append(
            BalanceSensor(
                coordinator,
                organization_id,
                currency=currency,
                balance_type=BALANCE_TYPE_PENDING,
            )
        )
        balance_sensors.append(
            BalanceSensor(
                coordinator,
                organization_id,
                currency=currency,
                balance_type=BALANCE_TYPE_TOTAL,
            )
        )
    else:
        _LOGGER.warn("Invalid currency: must be EUR or USD")

    return balance_sensors


def create_rig_sensors(mining_rigs, coordinator):
    rig_sensors = []
    for rig in mining_rigs:
        rig_sensors.append(RigStatusSensor(coordinator, rig))
        rig_sensors.append(RigTemperatureSensor(coordinator, rig))
        rig_sensors.append(RigProfitabilitySensor(coordinator, rig))

    return rig_sensors


def create_device_sensors(mining_rigs, coordinator):
    device_sensors = []
    for rig in mining_rigs:
        devices = rig.get("devices")
        for device in devices:
            device_sensors.append(DeviceAlgorithmSensor(coordinator, rig, device))
            device_sensors.append(DeviceSpeedSensor(coordinator, rig, device))
            device_sensors.append(DeviceStatusSensor(coordinator, rig, device))
            device_sensors.append(DeviceTemperatureSensor(coordinator, rig, device))
            device_sensors.append(DeviceLoadSensor(coordinator, rig, device))
            device_sensors.append(DeviceRPMSensor(coordinator, rig, device))

    return device_sensors
