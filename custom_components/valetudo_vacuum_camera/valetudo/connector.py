"""Version 1.3.5"""
import logging
import time
import os
import paho.mqtt.client as client
from custom_components.valetudo_vacuum_camera.utils.valetudo_jdata import RawToJson

_LOGGER = logging.getLogger(__name__)


class ValetudoConnector(client.Client):
    def __init__(self, mqtthost, mqttusr, mqttpass, mqtt_topic, hass):
        super().__init__("valetudo_connector")
        self._mqtt_topic = mqtt_topic
        if mqtt_topic:
            self._mqtt_subscribe = ([
                (str(mqtt_topic + "/MapData/map-data-hass"), 0),
                (str(mqtt_topic + "/StatusStateAttribute/status"), 0),
                (str(mqtt_topic + "/StatusStateAttribute/error_description"), 0),
            ])
        self._broker = mqtthost
        if not self._broker:
            self._broker = "core-mosquitto"
        self.username_pw_set(username=mqttusr, password=mqttpass)
        self.on_connect = self.on_connect_callback
        self.on_message = self.on_message_callback
        self.connect_async(host=self._broker, port=1883)
        self.enable_bridge_mode()
        self.loop_start()
        self._mqtt_run = False
        self._rcv_topic = None
        self._payload = None
        self._img_payload = None
        self._mqtt_vac_stat = None
        self._mqtt_vac_err = None
        self._data_in = False
        self._img_decoder = RawToJson(hass)
        self.is_client_check_mode(mqtt_topic)

    def update_data(self, process: bool = True):
        if self._img_payload:
            if process:
                _LOGGER.debug("Processing " + self._mqtt_topic + " data from MQTT")
                result = self._img_decoder.camera_message_received(
                    self._img_payload, self._mqtt_topic
                )
                self._data_in = False
                return result
            else:
                _LOGGER.debug("No data from " + self._mqtt_topic + " or vacuum docked")
                self._data_in = False
                return None

    def get_vacuum_status(self):
        return self._mqtt_vac_stat

    def get_vacuum_error(self):
        return self._mqtt_vac_err

    def is_data_available(self):
        return self._data_in

    def save_payload(self, file_name):
        # save payload when available.
        if self._img_payload and (self._data_in is True):
            with open(
                    os.getcwd()
                    +"custom_components/valetudo_vacuum_camera/snapshots/mqtt_"
                    + file_name
                    + ".raw",
                    "wb",
            ) as file:
                file.write(self._img_payload)
            _LOGGER.info("Saved image data from MQTT in mqtt_" + file_name + ".raw!")

    def on_message_callback(self, client, userdata, msg):
        self._rcv_topic = msg.topic
        if self._rcv_topic == (self._mqtt_topic + "/MapData/map-data-hass"):
            _LOGGER.debug("Received " + self._mqtt_topic + " image data from MQTT")
            self._img_payload = msg.payload
            self._data_in = True
        elif self._rcv_topic == (self._mqtt_topic + "/StatusStateAttribute/status"):
            self._payload = msg.payload
            if self._payload:
                self._mqtt_vac_stat = bytes.decode(self._payload, "utf-8")
                _LOGGER.debug(
                    self._mqtt_topic
                    + ": Received vacuum "
                    + self._mqtt_vac_stat
                    + " status from MQTT:"
                    + self._rcv_topic
                )
        elif self._rcv_topic == (
                self._mqtt_topic + "/StatusStateAttribute/error_description"
        ):
            self._payload = msg.payload
            self._mqtt_vac_err = bytes.decode(msg.payload, "utf-8")
            _LOGGER.debug(
                self._mqtt_topic
                + ": Received vacuum "
                + self._mqtt_vac_err
                + " from MQTT"
            )

    def on_connect_callback(self, client, userdata, flags, rc):
        self.subscribe(self._mqtt_subscribe)
        _LOGGER.debug("Subscribed to MQTT broker with topic: " + self._mqtt_topic)

    def stop_and_disconnect(self):
        self.loop_stop(force=False)  # Stop the MQTT loop gracefully
        self.disconnect()  # Disconnect from the broker
        _LOGGER.debug(self._mqtt_topic + ": Stopped and disconnected from MQTT broker.")

    def connect_broker(self):
        self.connect_async(host=self._broker, port=1883)
        self.enable_bridge_mode()
        self.loop_start()
        _LOGGER.debug(self._mqtt_topic + ": Connect MQTT broker.")

    def client_start(self):
        self.loop_start()
        _LOGGER.debug(self._mqtt_topic + ": Started MQTT loop")

    def client_stop(self):
        self.loop_stop()
        self._mqtt_run = False
        _LOGGER.debug(self._mqtt_topic + ": Stopped MQTT loop")

    def is_client_check_mode(self, check_topic):
        test_topic = "valetudo/myTopic"
        if check_topic is test_topic:
            _LOGGER.warning("Valetudo Connector test Topic ON %s", {check_topic})
            try:
                with open("tests/mqtt_data.raw", "rb") as file:
                    binary_data = file.read()
                self._img_payload = binary_data
                self._data_in = True
                self.update_data()
            except FileExistsError:
                _LOGGER.warning(
                    "Valetudo Connector undefined Topic, please check your configuration."
                )
            time.sleep(1.5)
            self.loop_stop()
