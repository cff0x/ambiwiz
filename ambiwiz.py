import os
import time
import socket
import json

import mss
import mss.tools
from PIL import Image

# device ip addresses (broadcast supported if enabled)
DEVICES = [
  {"ip": "192.168.0.255", "port": 38899}
]
UDP_BROADCAST = True

# color multiplier
COLOR_MUL = 1

DIM_MUL = 0.75

# coolness/warmth
COOLNESS = 0
WARMTH = 0

# state (on/off)
STATE = True

# used to check for changes to the values
old_color = [
  None,
  None,
  None
] # r, g, b

# socket
sock = None

def process_image(img):
  # get image histogram values
  img_hist = img.histogram()
  hist = (
    img_hist[0:256],
    img_hist[256:256*2],
    img_hist[256*2: 256*3]
  ) # r, g, b

  # calculate and round average color values
  avg_color = (
    round(sum(i*w for i, w in enumerate(hist[0])) / sum(hist[0])),
    round(sum(i*w for i, w in enumerate(hist[1])) / sum(hist[1])),
    round(sum(i*w for i, w in enumerate(hist[2])) / sum(hist[2])),
  ) # r, g, b

  # calculate color values which will be sent to the lamp
  set_color = (
    max(min(avg_color[0] * COLOR_MUL, 255), 0),
    max(min(avg_color[1] * COLOR_MUL, 255), 0),
    max(min(avg_color[2] * COLOR_MUL, 255), 0),
  ) # r, g, b

  set_dimming = round(((set_color[0] + set_color[1] + set_color[2]) / 3) * DIM_MUL)

  # apply color change if anything changed
  if set_color[0] != old_color[0] or set_color[1] != old_color[1] or set_color[2] != old_color[2]:
    print("colors changed!")

    # send setPilot command to specified device(s)
    for device in DEVICES:
      msg = {
        "params": {
          "r": set_color[0],
          "g": set_color[1],
          "b": set_color[2],
          "c": max(min(COOLNESS, 255), 0),
          "w": max(min(WARMTH, 255), 0),
          "dimming": max(min(set_dimming, 100), 0),
          "state": STATE 
        },
        "method":"setPilot"
      }
      print("-> {}:{} (broadcast: {}):\n{}".format(device["ip"], device["port"], UDP_BROADCAST, json.dumps(msg)))
      sock.sendto(str.encode(json.dumps(msg)), (device["ip"], device["port"]))
    
    # store old color values to check for changes
    old_color[0] = set_color[0]
    old_color[1] = set_color[1]
    old_color[2] = set_color[2]

if __name__ == "__main__":
  # setup socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  if UDP_BROADCAST:
    print("-> UDP broadcast enabled!")
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

  while True:
    # grab and analyze screenshot from whole screen
    with mss.mss() as sct:
      sct_img = sct.grab(sct.monitors[-1])
      process_image(Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX"))
    
    time.sleep(0.05)
