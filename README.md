


## Flash a microPython version that supports espnow

Grab at least version v1.20.0-53 from [micropython.org](https://micropython.org/download/esp32c3/)

Use esptool with the following commands to flash micropython to the board. You can install esptool with `pip install esptool`

```
esptool --chip esp32c3 erase_flash
esptool --chip esp32c3 --baud 460800 write_flash -z 0x0 esp32c3-usb-20230508-unstable-v1.20.0-53-g7c645b52e.bin
```


## Uploading

Uploading uses mpremote, which can be installed via pip as explained on [this page](https://docs.micropython.org/en/latest/reference/mpremote.html)

use included batch files:
| File | Description |
| --- | --- |
| clean.bat | deletes everything on the board, useful if files have been deleted locally | 
| upload.bat | uploads the src folder to the auto-detected board by mpremote | 
| sync_to_all_boards.bat | syncs all files from the connected board to all other wirelessly online boards via espnow | 
| repl.bat | starts an interative python shell on the board | 

## Notes on mesh network

In order for the mesh network and therefore the file syncing to work, all boards have to have the same boards defined in their boards.py. Ideally this file is identical on all boards. This means, to add a new board to an existing mesh, all boards have to be updated via cable once initially. Afterwards, small changes to boards.py such as channel mappings can be updated wirelessly.

To create two separate sets of boards that operate independantly from each other, simply have two separate boards.py files with no boards shared.

## Notes on effects

Because the only thing that is synced between the boards is the time, all effects have to rely solely on time to determine their current state. The operating principle is similar to a GPU shader where the effect is run for each pixel and has to determine the brightness value based on given inputs.

In this case, the inputs are:
- time in ms since effect started. If the effect is allowed to fade, time can be negative and can overrun the defined runtime by the fadetime
- the channel, which is the current pixel number to be rendered
- max_channels: how many total channels there are
- epoch, which represents how often this effect theoretically has been run. Useful to create slight variations of the effects.

files in the effects subfolder are loaded automatically.

Each effect needs at least the following parameters and the render function
```python
# control parameters
enabled = True
solo = False #disables all other effects

# external parameters
runtime = 4000 #ms
fade = True

def render(channel, max_channels, time, epoch):
    return 1.0
```

## Notes on boards.py

The mac address needed will be output by a board during startup. After flashing micropython and uploading the project, connect via repl and hit Ctrl+D to reboot it. The mac can be copied to the boards.py file in the way it is represented there.

for the channels list, which is limited to 6 entries on the esp32-c3, the first number is the channel or pixel number in the whole setup. The second number is the GPIO pin of the board to use. These are the raw GPIO numbers of the ESP32-c3, not the "D" numbers. You can find a diagram on [seedstudio's wiki](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/#pinout-diagram) where it's the GPIO pin numbers in the green boxes.

The name can be defined arbitrarily but has to be unique. This will also be the name of the wifi AP provided.