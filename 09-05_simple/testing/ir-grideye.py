
# import matplotlib
# import matplotlib
# matplotlib.use('TkAgg')  # must come before pyplot
# import matplotlib.pyplot as plt
# print(matplotlib.get_backend())


import serial
import numpy as np
import matplotlib.pyplot as plt

ser = serial.Serial('COM6', 9600, timeout=0.01)

plt.ion()
fig, ax = plt.subplots()
im = ax.imshow(np.zeros((8, 8)), vmin=20, vmax=35, cmap='inferno')
plt.colorbar(im)
ax.set_title("AMG8833 Heatmap")
ax.set_xticks(range(8))
ax.set_yticks(range(8))

try:
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            plt.pause(0.01)
            continue
        if line.startswith('[') and line.endswith(']'):
            try:
                vals = [float(x) for x in line[1:-1].replace('\n','').split(',') if x.strip()]
                if len(vals) == 64:
                    data = np.array(vals).reshape((8, 8))
                    print(np.min(data), np.max(data))      # debug
                    im.set_data(data)
                    im.set_clim(np.min(data), np.max(data))  # dynamic scale
                    plt.draw()
                    plt.pause(0.01)
            except ValueError:
                pass

except KeyboardInterrupt:
    print("Exiting...")
finally:
    ser.close()

# import serial

# ser = serial.Serial('/dev/ttyACM0', 9600, timeout=2)

# while True:
#     line = ser.readline().decode(errors="ignore").strip()
#     if line:
#         print("RAW:", line)

