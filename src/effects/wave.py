# control parameters
enabled = True
solo = False

# external parameters
runtime = 20000 #ms
fade = True

# effect parameters
repetitons = 8
brightness = 0.6

import math


def render(channel, max_channels, time, epoch):

    period = runtime / repetitons

    divisor = max_channels

    variant = (epoch//2)%3

    if variant == 1:
        divisor *= 2
    elif variant == 2:
        divisor /= 2

    return brightness * (math.sin(time/period*math.pi*2 + channel*math.pi*2/divisor)/2+0.5)