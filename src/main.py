
import time
import network
import espnow
import struct

from conf import config, boards

import timesync

dbgled = 511

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
num_leds = 0
channels = dict()

for peer_conf in boards.board_conf:
    if(peer_conf['mac'] != my_mac):
        enow.add_peer(peer_conf['mac'], ifidx=network.AP_IF)
        peer_conf['rssi'] = -1000
        peer_conf['hops'] = 100
        peer_conf['via'] = b'\x00\x00\x00\x00\x00\x00'
        peer_conf['age'] = 1000
        my_peers.append(peer_conf)
    
    
    for ch in peer_conf['channels']:
        channels[ch[0]] = 0

num_leds = len(channels)
del channels
print("num leds:", num_leds)

num_boards = len(boards.board_conf)
print("num boards:", num_boards)


def ping(mac):
    data = struct.pack("II", 10, time.ticks_ms())
    enow.send(mac, data, False)


def handle_msg(type, data):
    global dbgled
    dbgled = 500

def send_msg(type, mac, msg):
    if type < 1000: return
    data = bytearray(10+len(msg))
    struct.pack_into("I6s", data, 0, type, mac)
    data[10:] = bytes(msg)

    try:
        via = find_peer_by_mac(mac)['via']
        enow.send(via, data, False)
    except: pass

announce_fmt = '6shB6s'
announce_fmt_size = struct.calcsize(announce_fmt)

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

        #print("ping", find_peer_by_mac(mac)["name"], time.ticks_diff(tnow, result[1]), signal)
    elif(type == 100):
        sender = find_peer_by_mac(mac)
        if(info[0] >= sender['rssi'] or sender['age'] > config.age_limit or sender['via'] == mac):
            sender['rssi'] = info[0]
            sender['hops'] = 1
            sender['age'] = 0
            sender['via'] = mac
            print("direct ", sender['name'], "via", len(sender['name'])*'.', "hops", sender['hops'], "rssi", sender['rssi'])
        offset = 4

        while offset+announce_fmt_size <= len(data):
            result = struct.unpack_from(announce_fmt, data, offset)
            offset += announce_fmt_size

            if(result[0] == my_mac): continue
            if(result[3] == my_mac): continue
            if(result[2] >= num_boards -1): continue

            remote_peer = find_peer_by_mac(result[0])
            min_rssi = min(info[0], result[1])
            if(remote_peer['age'] > config.age_limit or remote_peer['rssi'] < min_rssi or remote_peer['via'] == mac):
                remote_peer['rssi'] = min_rssi
                remote_peer['hops'] = result[2] + 1
                remote_peer['age'] = 0
                remote_peer['via'] = mac
                print("updated", remote_peer['name'], "via", sender['name'], "hops", remote_peer['hops'], "rssi", remote_peer['rssi'])

        for peer in my_peers:
            if(peer['via'] == mac and peer['age'] > 0):
                peer['age'] = 1000

    elif(type >= 1000):
        destination = struct.unpack_from("6s", data, 4)[0]
       
        if(destination == my_mac):
            handle_msg(type, data[10:])
            print("got msg for myself from", find_peer_by_mac(mac)['name'])
        else:
            try:
                dest_peer = find_peer_by_mac(destination)
                via = dest_peer['via']
                enow.send(via, data, False)
                print("got msg for ", dest_peer['name'], "from", find_peer_by_mac(mac)['name'])
            except: pass

    elif(type == 999):
        destination, origin = struct.unpack_from("6s6s", data, 4)
        print("trace")
        if(origin == my_mac):
            print("tracert:", end='')
            offset = 10
            while offset+6 <= len(data):
                result = struct.unpack_from("6s", data, offset)[0]
                offset += 6
                peer = find_peer_by_mac(result)
                print("->", peer['name'], end='')
            print()
       
        elif(destination == my_mac):
            try:
                reply = bytearray(data)
                struct.pack_into("6s", reply, 4, origin)
                reply.extend(struct.pack("6s", my_mac))
                dest_peer = find_peer_by_mac(origin)
                via = dest_peer['via']
                enow.send(via, reply, False)
            except: pass
        else:
            try:
                reply = bytearray(data)
                reply.extend(struct.pack("6s", my_mac))
                dest_peer = find_peer_by_mac(destination)
                via = dest_peer['via']
                enow.send(via, reply, False)
            except: pass



def tracert(peer):
    data = struct.pack("I6s6s", 999, peer['mac'], my_mac)
    enow.send(peer['via'], data, False)


def announce():
    knownpeers = list(filter(lambda peer: peer['age'] < config.age_limit, my_peers))
    data = bytearray(4 + len(knownpeers) * announce_fmt_size)

    struct.pack_into('I', data, 0, 100)

    for i,peer in enumerate(knownpeers):
        struct.pack_into(announce_fmt, data, 4+i*announce_fmt_size, peer['mac'], peer['rssi'], peer['hops'], peer['via'])
    
    try:
        enow.send(data)
    except: pass

    for peer in my_peers:
        #print(peer['name'], "age", peer['age'])
        if peer['age'] < 1000:
            peer['age'] += 1
        




from machine import Pin, PWM
import random

for channel in my_conf['channels']:
    channel[1] = PWM(Pin(channel[1]), freq=5000, duty=10)


last_sync = 0
last_announce = 0

next_test = 0

import math

enow.irq(recv_cb)
while(True):
    rawtime = time.ticks_ms()
    if(time.ticks_diff(rawtime, last_sync) >= 100):
        last_sync = rawtime
        for peer in my_peers:
            if(peer['hops'] == 1 and peer['age'] < config.age_limit):
                ping(peer['mac'])

        timesync.update()
    
        #print("time:", timesync.now(), "offset:", timesync.time_offset, timesync.time_slow_offset)

    if(time.ticks_diff(rawtime, last_announce) >= 1000):
        last_announce = rawtime
        announce()

    if(timesync.now() >= next_test):
        period = (len(my_peers)+1) * 1000
        offset = boards.board_conf.index(my_conf) * 1000
        next_test = timesync.now()//period*period + period + offset
        
        dbgled = 500
        for peer in my_peers:
            send_msg(1000, peer['mac'],b'test')

    #random.seed((timesync.now()//50)*23471)

    if(dbgled > 511): dbgled = 500

    for channel in my_conf['channels']:
        #channel[1].duty(random.randint(0,1023))
        channel[1].duty(int(math.sin(timesync.now()/500*math.pi + channel[0]*math.pi*2/3*0)*511+511)//20 + (dbgled>0) * 900)

    if(dbgled > 0): dbgled -= 40
    if(dbgled < 0): dbgled = 0
    