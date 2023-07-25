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

pulsars = []

def prepare(max_channels, time, epoch):
    global pulsars
    seed = (epoch * 412789)*243
    random.seed(seed)

    count = int(max_channels/20 * runtime / 1000 * avg_per_second)

    if(len(pulsars) != count):
        pulsars = [{} for x in range(count)]

    for pulsar in pulsars:
        pulsar["bri"] = min_brightness + random.random()*(max_brightness-min_brightness)
        size = (min_size + random.random()*(max_size-min_size))/2

        pulsar["pos"] = size * 0.7 + random.random() * (1-size*0.7*2)
        pulsar["peaktime"] = random.randrange(ramp_up, runtime-ramp_down)

        pulsar["period"] = size_pulse_frequency_min + random.random()*(size_pulse_frequency_max-size_pulse_frequency_min)
        pulsar["size"] = size + math.sin(random.random()*2*math.pi + time/1000.0*2*math.pi*pulsar["period"]) * size_pulse_scale * random.random()


def render(channel, max_channels, time, epoch):
    global pulsars


    value = 0

    for pulsar in pulsars:

        channel_size = pulsar["size"] * max_channels
        bri = pulsar["bri"]

        if(time < pulsar["peaktime"]-ramp_up):
            bri = 0
        elif(time < pulsar["peaktime"]):
            bri *= 1.0 - (pulsar["peaktime"]-time)/ramp_up
        elif(time < pulsar["peaktime"]+ramp_down):
            bri *= 1.0 - (time-pulsar["peaktime"])/ramp_down
        else:
            bri = 0

        position = pulsar["pos"]*max_channels
        dist = abs(channel-position)
        if dist < channel_size and channel_size > 0:
            val = bri
            val *= (channel_size-dist)/channel_size
            if val > 1: val = 1
            value += val
        
    if value > 1: value = 1
    
    return value