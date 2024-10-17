import socket
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import threading
from sklearn.ensemble import IsolationForest
import time

# Server configuration
HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Port to listen on

# Data variables for plotting and ML model
x_data = []
pure_y_data = []
noisy_y_data = []
outlier_indices = []

# Create a plot window
app = QtWidgets.QApplication([])  
win = pg.GraphicsLayoutWidget(show=True)
plot = win.addPlot(title="Real-Time Sine Wave with Outlier Detection")
pure_curve = plot.plot(pen='g', name="Pure Sine Wave")  # Pure sine wave line in green
noisy_curve = plot.plot(pen='b', name="Sine Wave with Outliers")  # Noisy line in blue
outlier_curve = plot.plot(pen=None, symbol='o', symbolSize=8, symbolBrush='r')  # Outliers in red

# Isolation Forest for outlier detection
model = IsolationForest(contamination=0.05)  # 5% contamination
outlier_threshold = 100  # Minimum number of points before detecting outliers

# Create a list to hold text items for outlier labels
outlier_labels = []

def update_plot():
    global x_data, pure_y_data, noisy_y_data, outlier_indices, outlier_labels
    # Update the plot with the latest data
    pure_curve.setData(x_data, pure_y_data)
    noisy_curve.setData(x_data, noisy_y_data)
    plot.enableAutoRange('xy', True)  # Enable automatic range adjustments

    # Clear previous outlier labels
    for label in outlier_labels:
        plot.removeItem(label)
    outlier_labels.clear()

    # Highlight outliers in the plot
    if outlier_indices:
        outliers = [noisy_y_data[i] for i in outlier_indices]
        outlier_x_values = [x_data[i] for i in outlier_indices]
        outlier_curve.setData(outlier_x_values, outliers)  # Set outlier markers

        # Add labels for each outlier
        for index in outlier_indices:
            label = pg.TextItem("Outlier", anchor=(0, 0), color='r')  # Create a text item
            label.setPos(x_data[index], noisy_y_data[index])  # Set position at the outlier
            plot.addItem(label)  # Add the text item to the plot
            outlier_labels.append(label)  # Keep track of labels for clearing later
    else:
        outlier_curve.clear()  # Clear outlier points if none detected

def detect_outliers():
    global noisy_y_data, outlier_indices
    while True:
        time.sleep(1)  # Check for outliers every second
        if len(noisy_y_data) >= outlier_threshold:
            y_reshaped = np.array(noisy_y_data).reshape(-1, 1)  # Reshape the data for model input
            predictions = model.fit_predict(y_reshaped)  # Fit model and get outlier predictions
            
            # Get indices of outliers
            outlier_indices = [i for i, pred in enumerate(predictions) if pred == -1]
        else:
            outlier_indices = []  # Reset outlier indices if not enough data

def receive_data(conn):
    global x_data, pure_y_data, noisy_y_data
    idx = 0
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            try:
                message = data.decode('utf-8').strip()
                if message.startswith("pure:"):
                    pure_sin_value = float(message.split(':')[1])
                    # Append pure sine wave data
                    x_data.append(idx)
                    pure_y_data.append(pure_sin_value)

                elif message.startswith("with_outlier:"):
                    noisy_sin_value = float(message.split(':')[1])
                    # Append noisy sine wave data
                    noisy_y_data.append(noisy_sin_value)
                
                # Update index and manage data length
                idx += 1

                # Flush data when the number of points exceeds 100 (sliding window)
                if len(x_data) > 100:
                    x_data = x_data[1:]
                    pure_y_data = pure_y_data[1:]
                    noisy_y_data = noisy_y_data[1:]
                
            except ValueError:
                print("Invalid data received")
    except (ConnectionAbortedError, ConnectionResetError, OSError) as e:
        print(f"Connection error: {e}")
    finally:
        print("Connection closed")
        conn.close()

# Set up the socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server is listening on {HOST}:{PORT}")
    
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        
        # Start data receiving in a separate thread
        data_thread = threading.Thread(target=receive_data, args=(conn,))
        data_thread.daemon = True
        data_thread.start()

        # Start outlier detection in a separate thread
        outlier_thread = threading.Thread(target=detect_outliers)
        outlier_thread.daemon = True
        outlier_thread.start()

        # Use a timer to continuously update the plot
        timer = QtCore.QTimer()
        timer.timeout.connect(update_plot)
        timer.start(50)  # Update every 50ms

        QtWidgets.QApplication.instance().exec_()
