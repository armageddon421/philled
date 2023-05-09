
import time
import network
import espnow
import struct

from conf import config, boards

import timesync

def find_peer_by_mac(mac):
    for board in boards.board_conf:
        if(board['mac'] == mac):
            return board


def find_peer_by_name(name):
    for board in boards.board_conf:
        if(board['name'] == name):
            return board

network.WLAN(network.STA_IF).active(False)

ap = network.WLAN(network.AP_IF)
ap.active(True)

my_mac = ap.config('mac')
print("MY MAC")
print(my_mac)

my_conf = find_peer_by_mac(my_mac)
print(my_conf)


ap.config(ssid=my_conf['name'], channel=config.wifi_config['chn'], key=config.wifi_config['psk'], security=network.AUTH_WPA2_PSK)


print(ap.config('ssid'))
print(ap.config('channel'))

enow = espnow.ESPNow()
enow.active(True)

my_peers = []

for peer in my_conf['peers']:
    peer_conf = find_peer_by_name(peer)
    enow.add_peer(peer_conf['mac'], ifidx=network.AP_IF)
    my_peers.append(peer_conf)


def ping(mac):
    data = struct.pack("II", 10, time.ticks_ms())
    enow.send(mac, data, False)


def recv_cb(enow):
    #tnow = time.ticks_ms()
    mac, data = enow.irecv(0)
    info = enow.peers_table[mac]
    tnow = info[1]
    type = struct.unpack("I", data)[0]
    

    if(type == 10):
        sendts = struct.unpack_from("I", data, 4)[0]
        reply = struct.pack("III", 11, sendts, timesync.now())
        enow.send(mac, reply, False)
    
    elif(type == 11):
        result = struct.unpack("III", data)
        timesync.sync(result[1], result[2], tnow)

        signal = info[0]

        print("ping", find_peer_by_mac(mac)["name"], time.ticks_diff(tnow, result[1]), signal)



enow.irq(recv_cb)

from machine import Pin, PWM
import random

for channel in my_conf['channels']:
    channel[1] = PWM(Pin(channel[1]), freq=5000, duty=10)


last_sync = 0

import math

while(True):
    rawtime = time.ticks_ms()
    if(time.ticks_diff(rawtime, last_sync) >= 100):
        last_sync = rawtime
        for peer in my_peers:
            ping(peer['mac'])

        timesync.update()
    
        print("time:", timesync.now(), "offset:", timesync.time_offset, timesync.time_slow_offset)

    #random.seed((timesync.now()//50)*23471)

    for channel in my_conf['channels']:
        #channel[1].duty(random.randint(0,1023))
        channel[1].duty(int(math.sin(timesync.now()/500*math.pi + channel[0]*math.pi*2/3)*511+511))