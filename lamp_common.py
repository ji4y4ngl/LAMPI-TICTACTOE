import paho.mqtt.client

DEVICE_ID_FILENAME = '/sys/class/net/eth0/address'

# MQTT Topic Names
TOPIC_SET_LAMP_CONFIG = "lamp/set_config"
TOPIC_LAMP_CHANGE_NOTIFICATION = "lamp/changed"
TOPIC_LAMP_ASSOCIATED = "lamp/associated"

# TTT Game MQTT Topics
TTT_TOPIC_SET_CONFIG = "lamp/ttt/set_config"
TTT_TOPIC_GAME_CHANGE = "lamp/ttt/changed"
TTT_TOPIC_ASSOCIATE = "lamp/ttt/associate_game"


def get_device_id():
    mac_addr = open(DEVICE_ID_FILENAME).read().strip()
    return mac_addr.replace(':', '')


def client_state_topic(client_id):
    return 'lamp/connection/{}/state'.format(client_id)


def broker_bridge_connection_topic():
    device_id = get_device_id()
    return '$SYS/broker/connection/{}_broker/state'.format(device_id)


# MQTT Broker Connection info
MQTT_VERSION = paho.mqtt.client.MQTTv311
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
EC2_MQTT_BROKER_HOST = "3.222.78.41"
EC2_MQTT_BROKER_PORT = 50001
MQTT_BROKER_KEEP_ALIVE_SECS = 60
