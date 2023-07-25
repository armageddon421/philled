# control parameters
enabled = True
solo = False

# external parameters
runtime = 25000 #ms
fade = True

# effect parameters
brightness = 0.9
enable_palette_variant = True

import math


def render(channel, max_channels, time, epoch):

    t = epoch*runtime + time
    divisor = max_channels


    value = math.sin(t/1300*math.pi*2 + channel*math.pi*2/divisor * (math.sin(t/17400*math.pi*2)*0.4+1.2))/2+0.5
    value += math.sin(-t/1700*math.pi*2 + channel*math.pi*2/divisor * (math.cos(t/23700*math.pi*2)*1.2+3.8))/2+0.5
    value += math.cos(t/5800*math.pi*2 + channel*math.pi*2/divisor * (math.sin(-t/11050*math.pi*2)*2+3))/2+0.5

    value /= 3

    if enable_palette_variant and epoch%2:
        value = math.sin((value%1)*2*math.pi)
        

    return value * brightness