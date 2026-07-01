import urllib.parse

import paho.mqtt.client as mqtt
import requests

# Configurações do broker
MQTT_BROKER = "broker.emqx.io"  # ou seu IP local
MQTT_PORT = 1883
MQTT_TOPIC = "topicEdilson_ifsc/#"

# URL da API Django para atualizar o valor do sensor
API_URL = "http://localhost:8000/iot/update_sensor/"


def on_connect(client, userdata, flags, rc):
    print("Conectado ao broker com código:", rc)
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    print(f"Mensagem recebida: {msg.topic} => {msg.payload.decode()}")

    try:
        payload_value = float(msg.payload.decode())
        topic = msg.topic.strip()

        if not topic:
            print("Tópico vazio, ignorando mensagem.")
            return

        encoded_topic = urllib.parse.quote(topic, safe="/")
        response = requests.post(
            f"{API_URL}{encoded_topic}/",
            data={"value": payload_value}
        )
        print("Status da atualização:", response.status_code)
    except Exception as e:
        print("Erro ao processar mensagem:", e)

def connect_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    return client

def publish_message(topic, message):
    client = connect_mqtt()
    client.publish(topic, message)
    client.disconnect()

connect_mqtt()