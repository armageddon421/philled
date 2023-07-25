# control parameters
enabled = True
solo = False

# external parameters
runtime = 15000 #ms
fade = True

# effect parameters
min_brightness = 0.1
max_brightness = 0.75
min_period = 1000
max_period = 3000
enable_half_speed_variant = True

import math
import random

def render(channel, max_channels, time, epoch):

    seed = (epoch * 412789 + channel * 17625)*243
    random.seed(seed)

    offset = random.random() * 2 * math.pi
    period = (min_period+ random.random()*(max_period-min_period)) / 2 / math.pi
    
    if epoch%2 and enable_half_speed_variant:
        period *= 2


    value = math.sin(time/period + offset)/2+0.5

    value = min_brightness + value*(max_brightness-min_brightness)

    return value