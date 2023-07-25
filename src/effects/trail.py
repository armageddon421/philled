# control parameters
enabled = True
solo = False

# external parameters
runtime = 5000 #ms
fade = True

# effect parameters
repetitons = 6
subdivisions = 1
brightness = 0.8

import math


def render(channel, max_channels, time, epoch):

    reps = repetitons / ((epoch//2)%2+1)
    subs = subdivisions

    if (epoch//3)%2:
        subs += 1

    period = runtime / reps

    progress = float(time % period) / period

    active_led = (progress * max_channels)

    distance = (active_led - channel)%(max_channels/subs)

    value = 1.0 - (distance / (max_channels/subs))

    return value * brightness