


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