# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos del proyecto
COPY ./app /app/app
COPY requirements.txt /app

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto UDP para recibir mensajes
EXPOSE 10110/udp

# Comando de inicio
CMD ["python", "/app/app/service.py"]

