"""
homeassistant.components.switch.mqtt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Allows to configure a MQTT switch.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.mqtt/
"""
import logging
import homeassistant.components.mqtt as mqtt
from homeassistant.components.switch import SwitchDevice

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "MQTT Switch"
DEFAULT_QOS = 0
DEFAULT_PAYLOAD_ON = "ON"
DEFAULT_PAYLOAD_OFF = "OFF"
DEFAULT_OPTIMISTIC = False
DEFAULT_RETAIN = False

DEPENDENCIES = ['mqtt']


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """ Add MQTT Switch. """

    if config.get('command_topic') is None:
        _LOGGER.error("Missing required variable: command_topic")
        return False

    add_devices_callback([MqttSwitch(
        hass,
        config.get('name', DEFAULT_NAME),
        config.get('state_topic'),
        config.get('command_topic'),
        config.get('qos', DEFAULT_QOS),
        config.get('retain', DEFAULT_RETAIN),
        config.get('payload_on', DEFAULT_PAYLOAD_ON),
        config.get('payload_off', DEFAULT_PAYLOAD_OFF),
        config.get('optimistic', DEFAULT_OPTIMISTIC),
        config.get('state_format'))])


# pylint: disable=too-many-arguments, too-many-instance-attributes
class MqttSwitch(SwitchDevice):
    """ Represents a switch that can be toggled using MQTT. """
    def __init__(self, hass, name, state_topic, command_topic, qos, retain,
                 payload_on, payload_off, optimistic, state_format):
        self._state = False
        self._hass = hass
        self._name = name
        self._state_topic = state_topic
        self._command_topic = command_topic
        self._qos = qos
        self._retain = retain
        self._payload_on = payload_on
        self._payload_off = payload_off
        self._optimistic = optimistic
        self._parse = mqtt.FmtParser(state_format)

        def message_received(topic, payload, qos):
            """ A new MQTT message has been received. """
            payload = self._parse(payload)
            if payload == self._payload_on:
                self._state = True
                self.update_ha_state()
            elif payload == self._payload_off:
                self._state = False
                self.update_ha_state()

        if self._state_topic is None:
            # force optimistic mode
            self._optimistic = True
        else:
            # subscribe the state_topic
            mqtt.subscribe(hass, self._state_topic, message_received,
                           self._qos)

    @property
    def should_poll(self):
        """ No polling needed. """
        return False

    @property
    def name(self):
        """ The name of the switch. """
        return self._name

    @property
    def is_on(self):
        """ True if device is on. """
        return self._state

    def turn_on(self, **kwargs):
        """ Turn the device on. """
        mqtt.publish(self.hass, self._command_topic, self._payload_on,
                     self._qos, self._retain)
        if self._optimistic:
            # optimistically assume that switch has changed state
            self._state = True
            self.update_ha_state()

    def turn_off(self, **kwargs):
        """ Turn the device off. """
        mqtt.publish(self.hass, self._command_topic, self._payload_off,
                     self._qos, self._retain)
        if self._optimistic:
            # optimistically assume that switch has changed state
            self._state = False
            self.update_ha_state()
