cd src
python -m mpremote cp -r ./filetools.py : + exec "import filetools; filetools.wipe_dir('.')" + reset