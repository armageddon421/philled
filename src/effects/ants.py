# control parameters
enabled = True
solo = False

# external parameters
runtime = 25000 #ms
fade = True

# effect parameters
max_velocity = 2.0
wiggle_scale = 0.8
wiggle_timescale = 20
brightness = 0.7

import math
import random

def render(channel, max_channels, time, epoch):
    seed = (epoch * 412789)*243
    random.seed(seed)

    ant_count = max_channels/3
    if (epoch//2)%2:
        ant_count = max_channels/2

    toffset = runtime*epoch

    value = 0

    for i in range(ant_count):
        bri = 0.7 + random.random()*0.3
        position = random.random()
        speed = random.random()-0.5
        speed *= max_velocity
        position += speed * (time+toffset) / 1000
        position += math.sin(2*math.pi*random.random() + wiggle_timescale*time/1000*random.random()) * wiggle_scale/max_channels * random.random()
        position = position%2 - 0.5 #half will be offscreen
        position = position*max_channels
        if position < -1: continue
        if position > max_channels: continue
        dist = abs(channel-position)
        if dist < 1.0:
            val = brightness * bri
            val *= 1.0-dist
            if val > 1: val = 1
            value += val
        
    if value > 1: value = 1
    
    return value