# control parameters
enabled = True
solo = False

# external parameters
runtime = 2000 #ms
fade = False

# effect parameters
repetitons = 6

import math


def render(channel, max_channels, time, epoch):

    reps = repetitons / ((epoch//2)%2+1)

    period = runtime / reps

    progress = float(time % period) / period

    active_led = int(progress * max_channels)

    return (channel == active_led) * 1.0