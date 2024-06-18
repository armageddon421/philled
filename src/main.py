
import time
import network
import espnow
import struct
import machine
import sys

from conf import config, boards

import timesync

import filetools

dbgled = 511

def find_peer_by_mac(mac):
    for board in boards.board_conf:
        if(board['mac'] == mac):
            return board
    return None


def find_peer_by_name(name):
    for board in boards.board_conf:
        if(board['name'] == name):
            return board
    return None

network.WLAN(network.STA_IF).active(False)

ap = network.WLAN(network.AP_IF)
ap.active(True)

my_mac = ap.config('mac')
print("MY MAC")
print(my_mac)

my_conf = find_peer_by_mac(my_mac)
print(my_conf)

if not my_conf:
    while True:
        print("unconfigured, MY MAC:", my_mac)
        time.sleep(1.0)


#filter boards by group assignment
boards.board_conf = [x for x in filter(lambda conf: conf["group"] == my_conf["group"], boards.board_conf)]

ap.config(ssid=my_conf['name'], channel=config.wifi_config['chn'], key=config.wifi_config['psk'], security=network.AUTH_WPA2_PSK)

print(ap.config('ssid'))
print(ap.config('channel'))

enow = espnow.ESPNow()
enow.active(False)
time.sleep_ms(100)
enow.active(True)

my_peers = []
num_leds = 0

for peer_conf in boards.board_conf:
    if(peer_conf['mac'] != my_mac):
        enow.add_peer(peer_conf['mac'], ifidx=network.AP_IF, channel=config.wifi_config['chn'], encrypt=False)
        peer_conf['rssi'] = -1000
        peer_conf['hops'] = 100
        peer_conf['via'] = b'\x00\x00\x00\x00\x00\x00'
        peer_conf['age'] = 1000
        peer_conf['last_ping'] = 0
        my_peers.append(peer_conf)
    
    
    for ch in peer_conf['channels']:
        num_leds = max(num_leds, ch[0]+1)

print("num leds:", num_leds)

num_boards = len(boards.board_conf)
print("num boards:", num_boards)


def ping(mac):
    data = struct.pack("II", 10, time.ticks_ms())
    enow.send(mac, data, False)

def send_brightness(brightness):
    data = struct.pack("If", 15, brightness)
    try:
        enow.send(data)
    except: pass


msg_response = None
current_file_write = None
current_file_chunk = 0
reset_timer = 0
last_upload_msg_time = 0
# uneven types are responses
def handle_msg(type, data):
    global dbgled
    global msg_response
    global current_file_write
    global current_file_chunk
    global reset_timer
    global last_upload_msg_time

    dbgled = 5

    if type%2:
        msg_response = (type, data)
        return
    
    if type == 1000: #respond to call
        send_msg(1001, data, my_mac)

    if type == 1100: #delete folder
        filetools.wipe_dir(bytes(data[6:]).decode())
        send_msg(1101, data[:6], my_mac)
        last_upload_msg_time = time.ticks_ms()

    if type == 1200: #report checksum
        hash = filetools.hash(bytes(data[10:]).decode())
        send_msg(1201, data[:6], data[6:10] + hash)
        last_upload_msg_time = time.ticks_ms()

    if type == 1210: #report dirlist checksum
        hash = filetools.hash_dirlist(bytes(data[6:]).decode())
        send_msg(1211, data[:6], hash)
        last_upload_msg_time = time.ticks_ms()

    if type == 2000: #begin file
        fname = bytes(data[6:]).decode()
        filetools.ensure_path_exists(fname)
        try:
            if(current_file_write != None): current_file_write.close()
            current_file_write = open(fname, "wb")
            send_msg(2001, data[:6], my_mac)
            current_file_chunk = 0
        except:
            print("ERROR opening", fname)
            pass
        last_upload_msg_time = time.ticks_ms()

    if type == 2100: #chunk file
        try:
            idx = struct.unpack_from('I', data, 6)[0]
            if(idx == current_file_chunk):
                current_file_write.write(data[10:])
                send_msg(2101, data[:6], struct.pack('I', idx))
                current_file_chunk += 1
        except:
            print("ERROR writing chunk")
            pass
        last_upload_msg_time = time.ticks_ms()

    if type == 2110: #end file
        try:
            current_file_write.write(data[6:])
            current_file_write.close()
            current_file_write = None
            send_msg(2111, data[:6], my_mac)
        except:
            print("ERROR writing last chunk")
            pass
        last_upload_msg_time = time.ticks_ms()
    
    if type == 9000: #reset board
        reset_timer = time.ticks_ms() + 5000
        send_msg(9001, data[:6], my_mac)
        last_upload_msg_time = time.ticks_ms()



def send_msg(type, mac, msg):
    if type < 1000: return
    data = bytearray(10+len(msg))
    struct.pack_into("I6s", data, 0, type, mac)
    data[10:] = bytes(msg)

    try:
        via = find_peer_by_mac(mac)['via']
        enow.send(via, data, False)
    except Exception as e: sys.print_exception(e)


brightness_filtered = 0
brightness_shutdown = False
last_brightness_send = 0

announce_fmt = '6shB6s'
announce_fmt_size = struct.calcsize(announce_fmt)

def recv_cb(enow):
    global dbgled
    global brightness_filtered
    global last_upload_msg_time
    dbgled += 1
    try:
        #tnow = time.ticks_ms()
        mac, data = enow.irecv(0)
        info = None
        try:
            info = enow.peers_table[mac]
        except:
            print("received data from unknown mac")
            return
        tnow = info[1]
        type = struct.unpack("I", data)[0]
        

        if(type == 10):
            sendts = struct.unpack_from("I", data, 4)[0]
            try:
                reply = struct.pack("III", 11, sendts, timesync.now())
                enow.send(mac, reply, False)
            except Exception as e: sys.print_exception(e)
        
        elif(type == 11):
            result = struct.unpack("III", data)
            timesync.sync(result[1], result[2], tnow)

            signal = info[0]

            #print("ping", find_peer_by_mac(mac)["name"], time.ticks_diff(tnow, result[1]), result[2], signal)
        elif(type == 15):
            result = struct.unpack("If", data)
            brightness_filtered = brightness_filtered * 0.75 + 0.25 * result[1]

            #print("brightness ", brightness_filtered)
        elif(type == 100):
            sender = find_peer_by_mac(mac)
            if not sender: return
            if(info[0] - config.rssi_hysteresis_direct >= sender['rssi'] or sender['age'] > config.age_limit or sender['via'] == mac):
                sender['rssi'] = info[0]
                sender['hops'] = 1
                sender['age'] = 0
                sender['via'] = mac
                #print("direct ", sender['name'], "via", len(sender['name'])*'.', "hops", sender['hops'], "rssi", sender['rssi'])
            offset = 4

            while offset+announce_fmt_size <= len(data):
                result = struct.unpack_from(announce_fmt, data, offset)
                offset += announce_fmt_size

                if(result[0] == my_mac): continue
                if(result[3] == my_mac): continue
                if(result[2] >= num_boards -1): continue

                remote_peer = find_peer_by_mac(result[0])
                if not remote_peer: continue
                min_rssi = min(info[0], result[1]) - config.rssi_penalty_per_hop
                if(remote_peer['age'] > config.age_limit or remote_peer['rssi'] < min_rssi - config.rssi_hysteresis or remote_peer['via'] == mac):
                    remote_peer['rssi'] = min_rssi
                    remote_peer['hops'] = result[2] + 1
                    remote_peer['age'] = 0
                    remote_peer['via'] = mac
                    #print("updated", remote_peer['name'], "via", sender['name'], "hops", remote_peer['hops'], "rssi", remote_peer['rssi'])

            for peer in my_peers:
                if(peer['via'] == mac and peer['age'] > 0):
                    peer['age'] = 1000

        elif(type >= 1000):
            destination = struct.unpack_from("6s", data, 4)[0]
        
            if(destination == my_mac):
                handle_msg(type, data[10:])
                #print("got msg for myself from", find_peer_by_mac(mac)['name'], "type", type)
            else:
                last_upload_msg_time = time.ticks_ms()
                try:
                    dest_peer = find_peer_by_mac(destination)
                    if not dest_peer: return
                    via = dest_peer['via']
                    enow.send(via, data, False)
                    #print("got msg for ", dest_peer['name'], "from", find_peer_by_mac(mac)['name'])
                except Exception as e: sys.print_exception(e)

        elif(type == 999):
            destination, origin = struct.unpack_from("6s6s", data, 4)
            dbgled = 500
            print("trace")
            if(origin == my_mac):
                print("tracert:", end='')
                offset = 10
                while offset+6 <= len(data):
                    result = struct.unpack_from("6s", data, offset)[0]
                    offset += 6
                    peer = find_peer_by_mac(result)
                    if not peer: return
                    print("->", peer['name'], end='')
                print()
        
            elif(destination == my_mac):
                try:
                    reply = bytearray(data)
                    struct.pack_into("6s", reply, 4, origin)
                    reply.extend(struct.pack("6s", my_mac))
                    dest_peer = find_peer_by_mac(origin)
                    if not dest_peer: return
                    via = dest_peer['via']
                    enow.send(via, reply, False)
                except Exception as e: sys.print_exception(e)
            else:
                try:
                    reply = bytearray(data)
                    reply.extend(struct.pack("6s", my_mac))
                    dest_peer = find_peer_by_mac(destination)
                    if not dest_peer: return
                    via = dest_peer['via']
                    enow.send(via, reply, False)
                except Exception as e: sys.print_exception(e)
    except KeyboardInterrupt as ir:
        raise ir
    except Exception as e:
        sys.print_exception(e)
        time.sleep(1)
        machine.reset()


def tracert(peer):
    data = struct.pack("I6s6s", 999, peer['mac'], my_mac)
    try:
        enow.send(peer['via'], data, False)
    except Exception as e: sys.print_exception(e)


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
        




from machine import Pin, PWM, ADC
import random

for channel in my_conf['channels']:
    channel[1] = PWM(Pin(channel[1]), freq=5000, duty=10)

photodiode = ADC(Pin(2),atten=ADC.ATTN_11DB)
statusled = Pin(8, Pin.OUT)

import effect
effect.init(num_leds, config.fade_time)

#last_sync = 0
last_announce = 0
last_peer_valid = 0

next_test = 0

def handle_network(max_delay = 100):
    global msg_response
    global last_sync
    global last_announce
    global last_peer_valid

    rawtime = time.ticks_ms()

    msg_response = None

    while(enow.any() and time.ticks_ms() < rawtime+max_delay):
        recv_cb(enow)
        if(msg_response != None): break
        
    if time.ticks_ms() < rawtime+max_delay:
        ping_period = config.time_ping_period
        if max_delay > 200: ping_period *= 5 #reduce on active upload
        #if(time.ticks_diff(rawtime, last_sync) >= ping_period):
        #last_sync = rawtime
        max_ping_age = ping_period
        max_ping_peer = None
        for peer in my_peers:
            ping_age = time.ticks_diff(rawtime, peer['last_ping'])
            if(peer['hops'] == 1 and peer['age'] < config.age_limit and ping_age > max_ping_age):
                max_ping_age = ping_age
                max_ping_peer = peer

        if max_ping_peer:
            last_peer_valid = rawtime #lonely timeout
            ping(max_ping_peer['mac'])
            max_ping_peer['last_ping'] = rawtime

            timesync.update()

            #print("time:", timesync.now(), "offset:", timesync.time_offset, timesync.time_slow_offset)

        if(last_peer_valid > 0 and time.ticks_diff(rawtime, last_peer_valid) > config.lonely_reset_time):
            machine.reset()
    

    if(time.ticks_diff(rawtime, last_announce) >= config.announce_period):
        last_announce = rawtime
        announce()
    
    if(reset_timer > 0 and time.ticks_ms() > reset_timer):
        machine.reset()

def handle_dbgled():
    global dbgled
    global statusled

    if(dbgled > 100): dbgled = 100
    if(dbgled < 0): dbgled = 0
    
    statusled.value(dbgled > 0)

    if(dbgled > 0): dbgled -= 1

import math
import gc


if __name__ == "__main__":
    #enow.irq(recv_cb)
    print("starting")

    last_gc_time = 0

    try:
        
        while(True):
            rawtime = time.ticks_ms()

            upload_active = last_upload_msg_time > 0 and rawtime < last_upload_msg_time + config.remote_upload_timeout
            
            if upload_active:
                for channel in my_conf['channels']:
                    channel[1].duty(50)
                handle_network(250)
                handle_dbgled()
                continue #ignore rest of main loop

            handle_network(25)
            
            multiplier = config.max_brightness

            if brightness_shutdown:
                multiplier = 0

            effect_time = int(timesync.now() * config.timescale)
            
            effect.run(my_conf['channels'], effect_time, multiplier, config.led_gamma)
            
            handle_dbgled()
            
            max_value = 0
            for channel in my_conf['channels']:
                if channel[1].duty() > max_value:
                    max_value = channel[1].duty()

            if max_value == 0:
                brightness_filtered = brightness_filtered * 0.999 + 0.001 * (1-(photodiode.read() / 4095.0))
                if(time.ticks_diff(rawtime,last_gc_time) >= config.min_gc_distance):
                    gc.collect() #collect only when nothing is visible right now
                    last_gc_time = rawtime

            if brightness_filtered > 0.7:
                brightness_shutdown = True
            elif brightness_filtered < 0.3:
                brightness_shutdown = False
            
            if(time.ticks_diff(rawtime,last_brightness_send) >= config.brightness_period):
                last_brightness_send = rawtime
                send_brightness(brightness_filtered)
            
           


    except KeyboardInterrupt as ir:
        raise ir
    except Exception as e:
        sys.print_exception(e)
        time.sleep(1)
        machine.reset()

def waitResponse(type=0,timeout=2000):
    global msg_response
    starttime = time.ticks_ms()
    handle_network()
    handle_dbgled()
    while msg_response == None or (type != 0 and msg_response[0] != type):
        handle_network()
        handle_dbgled()
        elapsed = time.ticks_diff(time.ticks_ms(), starttime)
        if elapsed > timeout:
            return None
    return msg_response


def sendFile(peer, fname):
    try:
        f = open(fname, "rb")
        
        #header, send filename to write
        header_success = False
        for i in range(10):
            send_msg(2000, peer['mac'], my_mac+fname)
            if waitResponse(2001,1000):
                print("got response for header")
                header_success = True
                break

        if not header_success:
            print("timeout header", peer['name'])
            return False
        
        chunksize = 220 # max packet size is 250 minus overhead?
        chunk = f.read(chunksize)
        idx = 0

        print("sending", fname, "chunks", end=' ')
        while(len(chunk) == chunksize):
            #send and read new chunk
            chunk_success = False
            for i in range(20):
                send_msg(2100, peer['mac'], my_mac+struct.pack('I',idx)+chunk)
                if waitResponse(2101, 1000):
                    ack_idx = struct.unpack('I',msg_response[1])[0]
                    if(idx == ack_idx):
                        print(idx, end=' ')
                        idx += 1
                        chunk_success = True
                        break
                    else:
                        print("x",end='')
                print('.',end='')

            if not chunk_success:
                print("\ntimeout chunk", peer['name'])
                return False
            

            chunk = f.read(chunksize)
        
        f.close()
        
        #send last chunk
        end_success = False
        for i in range(10):
            send_msg(2110, peer['mac'], my_mac+chunk)
            if waitResponse(2111):
                print("got response for last chunk", idx)
                end_success = True
                break
        if not end_success:
            print("\ntimeout chunk", idx, peer['name'])
            return False

        #read back checksum
        checkusm_success = False
        for i in range(10):
            uid = struct.pack("I", time.ticks_ms())
            send_msg(1200, peer['mac'], my_mac+uid+fname)
            sha = filetools.hash(fname)
            response = waitResponse(1201)
            if response and response[1][:4] == uid:
                remote_sha = response[1][4:]
                if len(remote_sha) != 32:
                    print(fname, "still not present")
                    return False
                elif sha != remote_sha:
                    print(fname, "still different")
                    return False
                checkusm_success = True
                break
        if not checkusm_success:
            print("timeout checksum")
            return False

        return True
    except Exception as e:
        print("Exception sending file")
        sys.print_exception(e)

        return False


def syncFiles(dir=".", forceWipe=False):
    success = True

    #never wipe if not syncing everything afterwards
    if dir != ".":
        forceWipe = False

    if type(dir) is not list:
        dir = [dir]

    #warm up network
    print("network warmup", end='')
    for i in range(30):
        waitResponse(0,200)
        print(".",end='')
    print("DONE")
    

    #dim all leds
    for channel in my_conf['channels']:
        channel[1].duty(10)

    peers_alive = []
    #ping/call all known boards
    for peer in my_peers:
        if(peer['age'] < config.age_limit):
            for i in range(5):
                send_msg(1000, peer['mac'], my_mac)
                if waitResponse(1001):
                    print("got response from", peer['name'])
                    peers_alive.append(peer)
                    break
                else:
                    print("timeout", peer['name'])
        else:
            print("unreachable", peer['name'])

    handle_effects = False
    if not forceWipe:
        for d in dir:
            if(d == "." or d == "/" or d == "./" or d == "effects" or d == "/effects" or d == "./effects"):
                handle_effects = True
                break
    
    #for each responsive board
    for peer in peers_alive:
        print("===== handling", peer['name'])

        if handle_effects:
            #check effects dirlist hashes
            wipe_effects = False
            effects_hash = filetools.hash_dirlist("effects")

            abandon_peer = True

            for i in range(5):
                send_msg(1210, peer['mac'], my_mac+"effects")
                response = waitResponse(1211)
                if response:
                    remote_effects_hash = response[1]
                    if len(remote_effects_hash) != 32:
                        print("remote effects not present")
                    elif effects_hash != remote_effects_hash:
                        print("remote effects different, wipe!")
                        wipe_effects = True
                    else:
                        print("remote effects list unchanged")
                    abandon_peer = False
                    break
                    
            
            if(abandon_peer):
                print("remote effects hash timeout, abandoning client")
                continue
            abandon_peer = True

            #clear effects folder
            if(wipe_effects):
                for i in range(5):
                    send_msg(1100, peer['mac'], my_mac+"effects")
                    if waitResponse(1101, 5000):
                        print("wiped effects")
                        abandon_peer = False
                        break
            else:
                print("not wiping effects")
                abandon_peer = False

            if(abandon_peer):
                print("timeout wiping effects, abandoning client")
                continue
        else:
            print("skipping effects handling")


        if forceWipe:
            wipe_success = False
            for i in range(5):
                send_msg(1100, peer['mac'], my_mac+".")
                if waitResponse(1101, 5000):
                    print("WIPE successful")
                    wipe_success = True
                    break
            
            if not wipe_success:
                print("WIPE UNSUCCESSFUL, continuing normal sync")



        sendlist = []
        #for each local file
        for file,sha in [item for row in [filetools.filelist(d) for d in dir] for item in row]:
            #query remote board file checksum
            abandon_peer = True
            uid = struct.pack("I", time.ticks_ms())
            for i in range(5):
                send_msg(1200, peer['mac'], my_mac+uid+file)
                response = waitResponse(1201)
                if response and response[1][:4] == uid:
                    remote_sha = response[1][4:]
                    if len(remote_sha) != 32:
                        print(file, "not present")
                        sendlist.append(file)
                    elif sha != remote_sha:
                        print(file, "changed")
                        sendlist.append(file)
                    abandon_peer = False
                    break
                    
            
            if(abandon_peer):
                if forceWipe:
                    print("timeout checking file, adding file anyways due to forced wipe")
                    sendlist.append(file)
                else:
                    print("timeout checking file, abandoning client")
                    success = False
                    sendlist.clear()
                    break
        
        if(len(sendlist) == 0):
            continue

        print("sending", sendlist, "to", peer['name'])

        #for each changed file
        for file in sendlist:
            f_success = False

            #send file in chunks and retry up to 20 times
            for i in range(20):
                if sendFile(peer, file):
                    print("success!")
                    f_success = True
                    break
                waitResponse() # handle network until timeout
                print("retry", i)
            
            #mark overall success as failed
            if not f_success:
                success = False
    
    #do not reset if anything failed
    if(success):
        #reset all boards in about 5 seconds
        for peer in peers_alive:
            reset_success = False
            for i in range(3):
                send_msg(9000, peer['mac'], my_mac)
                if waitResponse(9001, 500):
                    print("reset ack from", peer['name'])
                    reset_success = True
                    break
            if not reset_success:
                print("Error resetting", peer['name'])
        
        #reset self after 5 seconds
        #time.sleep(5)
        #machine.reset()
        print("Successfully synced to", len(peers_alive), "reachable boards!")
    else:
        print("Something failed, not resetting boards. Check logs and try again please.")
