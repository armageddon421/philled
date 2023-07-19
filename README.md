


## Flash a microPython version that supports espnow, e.g. the included one




## Uploading

Uloading uses mpremote, which can be installed via pip as explained in https://docs.micropython.org/en/latest/reference/mpremote.html

use included batch files:
clean.bat deletes everything on the board, useful if files have been deleted locally
upload.bat uploads the src folder to the auto-detected board by mpremote
sync_to_all_boards.bat syncs all files to all connected and online boards via espnow