# control parameters
enabled = True
solo = False

# external parameters
runtime = 15000 #ms
fade = False

# effect parameters
min_brightness = 0.7
max_brightness = 1.0
avg_per_second = 1.0
ramp_up = 400 #ms
ramp_down = 3000 #ms
min_size = 0.1
max_size = 0.3
size_pulse_scale = 0.1
size_pulse_frequency_min = 0.8
size_pulse_frequency_max = 2.3

import math
import random

def render(channel, max_channels, time, epoch):
    seed = (epoch * 412789)*243
    random.seed(seed)

    count = max_channels/20 * runtime / 1000 * avg_per_second

    

    value = 0

    for i in range(count):
        bri = min_brightness + random.random()*(max_brightness-min_brightness)
        size = (min_size + random.random()*(max_size-min_size))/2

        position = size * 0.7 + random.random() * (1-size*0.7*2)
        peaktime = random.randrange(ramp_up, runtime-ramp_down)

        period = size_pulse_frequency_min + random.random()*(size_pulse_frequency_max-size_pulse_frequency_min)
        size += math.sin(random.random()*2*math.pi + time/1000.0*2*math.pi*period) * size_pulse_scale * random.random()
        channel_size = size * max_channels

        if(time < peaktime-ramp_up):
            bri = 0
        elif(time < peaktime):
            bri *= 1.0 - (peaktime-time)/ramp_up
        elif(time < peaktime+ramp_down):
            bri *= 1.0 - (time-peaktime)/ramp_down
        else:
            bri = 0

        position = position*max_channels
        dist = abs(channel-position)
        if dist < channel_size and channel_size > 0:
            val = bri
            val *= (channel_size-dist)/channel_size
            if val > 1: val = 1
            value += val
        
    if value > 1: value = 1
    
    return value