import socket
import math
import time
import random

# Client configuration
HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

def send_data():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        idx = 0
        drift = 0.0  # Drift value
        seasonal_variation = 0.0  # Seasonal variation value
        seasonal_period = 1000  # Period of the seasonal variation

        while True:
            # Calculate drift and seasonal variations
            drift = 0.0001 * idx  # Slowly increase the drift
            seasonal_variation = 2.0 * math.sin(2 * math.pi * (idx / seasonal_period))  # Seasonal pattern
            pure_sin_value = math.sin(idx * 0.1)
            # Pure sine wave value with drift and seasonal variation
            pure_sin_value_1 = math.sin(idx * 0.1) + drift + seasonal_variation
            s.sendall(f"pure:{pure_sin_value}\n".encode('utf-8'))

            # Sine wave with outliers
            if idx % 50 == 0:  # Introduce outliers every 50 iterations
                outlier_value = pure_sin_value_1 + random.uniform(2, 5)  # Add outlier
            else:
                outlier_value = pure_sin_value_1
            
            s.sendall(f"with_outlier:{outlier_value}\n".encode('utf-8'))
            idx += 1
            time.sleep(0.1)

send_data()
