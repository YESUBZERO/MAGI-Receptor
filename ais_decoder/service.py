import os
import json
import logging
import socket
import signal
import sys
from pyais.stream import UDPReceiver
from confluent_kafka import Producer
from utils import ship_type_mapping, status_mapping

# Configuración de Kafka desde variables de entorno
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
STATIC_TOPIC = os.getenv("STATIC_TOPIC", "static-message")
DYNAMIC_TOPIC = os.getenv("DYNAMIC_TOPIC", "dynamic-message")
UDP_HOST = os.getenv("UDP_HOST", "0.0.0.0")
UDP_PORT = int(os.getenv("UDP_PORT", 10110))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KafkaProducer")

# Configurar el productor de Kafka
conf = {"bootstrap.servers": KAFKA_BROKER}
producer = Producer(conf)

def kafka_delivery_report(err, msg):
    """Callback que confirma si el mensaje se envió exitosamente a Kafka."""
    if err is not None:
        logger.error(f"Error al enviar mensaje a Kafka: {err}")
    else:
        logger.info(f"Mensaje enviado a Kafka: {msg.topic()} [{msg.partition()}]")

def process_ais_message(data):
    """Procesa mensajes AIS y los envía al tópico correspondiente en Kafka."""
    if "ship_type" in data:
        ship_type_code = data["ship_type"]
        data["ship_type"] = ship_type_mapping.get(ship_type_code, f"{ship_type_code}")
    
    if "status" in data:
        status_code = data["status"]
        data["status"] = status_mapping.get(status_code, f"{status_code}")
    
    msg_type = data.get("msg_type")
    if msg_type in [5, 24]:
        topic = STATIC_TOPIC
    elif msg_type in [1, 2, 3]:
        topic = DYNAMIC_TOPIC
    else:
        logger.info(f"Mensaje AIS ignorado: {data}")
        return
    
    producer.produce(topic, json.dumps(data), callback=kafka_delivery_report)
    producer.flush()

def signal_handler(sig, frame):
    """Maneja la señal de interrupción para salir limpiamente."""
    logger.info("Interrupción detectada. Cerrando productor y saliendo...")
    producer.flush()
    sys.exit(0)

def start_udp_listener():
    """Escucha mensajes AIS a través de UDP y los envía a Kafka."""
    signal.signal(signal.SIGINT, signal_handler)  # Capturar Ctrl+C
    logger.info(f"Escuchando mensajes NMEA AIS en UDP {UDP_HOST}:{UDP_PORT}...")
    with UDPReceiver(UDP_HOST, UDP_PORT) as stream:
        for msg in stream:
            try:
                decoded_message = msg.decode()
                json_message = decoded_message.to_json()
                data = json.loads(json_message)
                process_ais_message(data)
            except Exception as e:
                logger.error(f"Error procesando mensaje AIS: {e}")

if __name__ == "__main__":
    start_udp_listener()
