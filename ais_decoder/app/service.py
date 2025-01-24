import socket
from pyais.stream import UDPReceiver
from confluent_kafka import Producer
import json
from utils import ship_type_mapping, status_mapping

def kafka_delivery_report(err, msg):
    """Callback que confirma si el mensaje se envió exitosamente a Kafka."""
    if err is not None:
        print(f"Error al enviar mensaje a Kafka: {err}")
    else:
        print(f"Mensaje enviado a Kafka: {msg.topic()} [{msg.partition()}]")

def start_udp_listener(host="0.0.0.0", port=10110, kafka_broker="100.114.52.104:9092", kafka_topic="ais_data"):
    """
    Inicia un receptor UDP para recibir, procesar mensajes AIS y enviarlos a Kafka.
    """
    print(f"Escuchando mensajes NMEA AIS en UDP {host}:{port}...\n")

    # Configurar el productor de Kafka
    kafka_config = {"bootstrap.servers": kafka_broker}
    producer = Producer(kafka_config)

    # Crear un receptor UDP utilizando pyais
    with UDPReceiver(host, port) as stream:
        for msg in stream:
            try:
                # Decodificar el mensaje NMEA
                decoded_message = msg.decode()
                json_message = decoded_message.to_json()

                # Filtrar o transformar los datos si es necesario
                data = json.loads(json_message)

                # Reemplazar el valor de ship_type con su descripción si existe
                if "ship_type" in data:
                    ship_type_code = data["ship_type"]
                    data["ship_type"] = ship_type_mapping.get(ship_type_code, f"{ship_type_code}")

                if "status" in data:
                    status_code = data["status"]
                    data["status"] = status_mapping.get(status_code, f"{status_code}")

                if data.get("msg_type") in [1, 2, 3, 5, 18, 19]:
                    # Enviar a Kafka
                    producer.produce(kafka_topic, json.dumps(data), callback=kafka_delivery_report)
                    producer.flush()
            except Exception as e:
                print(f"Error al procesar mensaje: {e}")

if __name__ == "__main__":
    start_udp_listener()
