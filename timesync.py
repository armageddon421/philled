import time

time_offset = 0
time_slow_offset = 0

def now():
    return time.ticks_add(time.ticks_ms(), time_offset)

def sync(send_time, peer_time, recv_time):
    global time_offset
    global time_slow_offset
    
    round_trip = time.ticks_diff(recv_time, send_time)
    
    if(round_trip > 50 or round_trip < 0):
        return
    
    peer_now = time.ticks_add(peer_time, (round_trip+0)//2)

    peer_diff = time.ticks_diff(peer_now, time.ticks_add(recv_time, time_offset))

    if(peer_diff > 100):
        time_offset += peer_diff
        time_slow_offset = 0
    else:
        time_slow_offset += peer_diff - 1

def update():
    global time_offset
    global time_slow_offset

    if(abs(time_slow_offset) > 100):
        time_slow_offset //= 2
    
    if(time_slow_offset > 10):
        time_slow_offset -= 10
        time_offset += 1
    elif(time_slow_offset < -10):
        time_slow_offset += 10
        time_offset -= 1
    
    if(time_offset < 0):
        time_offset = 0
    
    

