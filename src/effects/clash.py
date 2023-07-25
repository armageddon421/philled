# control parameters
enabled = True
solo = False

# external parameters
runtime = 12000 #ms
fade = False

# effect parameters
repetitons = 6
dot_brightness = 0.7
dot_width = 1.5
spark_brightness_min = 0.7
spark_brightness_max = 0.95
sparks_per_channel = 0.5
spark_pow = 0.35
spark_distance_min = 0.075
spark_distance_factor = 1.5
spark_max_pre_aged = 0.3

import math
import random

def render(channel, max_channels, time, epoch):

    reps = repetitons

    period = runtime / reps

    progress = float(time % period) / period

    rep = int(time/period)

    seed = (epoch * 412789 + rep * 17625)*243
    random.seed(seed)

    value = 0

    if(progress < 0.5):
        dist_from_center = (1-math.pow(progress*2,2))/2
        led_dist = abs(0.5-channel/max_channels)
        dist = abs(dist_from_center-led_dist)

        dist *= max_channels
        if dist < dot_width:
            val = dot_brightness
            val *= dot_width-dist
            if val > 1: val = 1
            value += val
    else: #progress >0.5
        num_sparks = int(max_channels*sparks_per_channel)

        for i in range(num_sparks):
            t = (progress-0.5)*2
            dist_from_center = (math.pow(t,spark_pow)*(spark_distance_min+random.random()*spark_distance_factor))/2
            if i%2:
                dist_from_center = -dist_from_center
            led_dist = 0.5-channel/max_channels
            dist = abs(dist_from_center-led_dist)

            dist *= max_channels
            if dist < 1.0:
                t += random.random() * spark_max_pre_aged
                if t > 1: t=1
                val = (1-t*t) * (spark_brightness_min+random.random()*(spark_brightness_max-spark_brightness_min))
                val *= 1.0-dist
                if val > 1: val = 1
                value += val

    return value