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

par1 = 0
par2 = 0
par3 = 0

def prepare(max_channels, time, epoch):
    global par1, par2, par3
    t = epoch*runtime + time
    par1 = math.sin(t/17413*math.tau)*0.4+1.2
    par2 = math.cos(t/23717*math.tau)*1.2+3.8
    par3 = math.sin(-t/11051*math.tau)*2+3

def render(channel, max_channels, time, epoch):

    t = epoch*runtime + time
    divisor = max_channels

    channelpos = channel*math.tau/divisor

    value = math.sin(t/1305*math.tau + channelpos * par1)/2+0.5
    value += math.sin(-t/1701*math.tau + channelpos * par2)/2+0.5
    value += math.cos(t/5807*math.tau + channelpos * par3)/2+0.5

    value /= 3

    if enable_palette_variant and epoch%2:
        value = math.sin((value%1)*2*math.pi)
        

    return value * brightness