# control parameters
enabled = True
solo = False

# external parameters
runtime = 8000 #ms
fade = False

# effect parameters
repetitons = 7
beat_partition = 0.32
beat_brightness = 0.7
beat_width = 5
beat_ramp_up = 0.25 #max 0.5
wave_brightness = 0.7
wave_width = 7
fadeout = 0.5

import math
import random

#one time calculations
if beat_ramp_up <= 0.05: beat_ramp_up = 0.05
if beat_ramp_up > 0.495: beat_ramp_up = 0.495
beat_ramp_down = 1 - beat_ramp_up

def render(channel, max_channels, time, epoch):

    period = runtime / repetitons

    progress = float(time % period) / period

    value = 0

    p = progress
    if(progress > beat_partition): p -= beat_partition
    p /= beat_partition
    if p < beat_ramp_down + beat_ramp_up:
        dist = abs(0.5-channel/max_channels)
        dist *= max_channels
        if dist < beat_width:
            if(p < beat_ramp_up):
                p /= beat_ramp_up
            elif p < beat_ramp_up + beat_ramp_down:
                p -= beat_ramp_up
                p /= beat_ramp_down
                p = 1-p

            val = beat_brightness * p
            val *= beat_width-dist
            if val > 1: val = 1
            value += val
    
    if progress > beat_partition:
        p = progress - beat_partition

        dist_from_center = p / (1-beat_partition)
        dist_from_center = math.pow(dist_from_center, 0.5)
        dist_from_center /= 2
        led_dist = abs(0.5-channel/max_channels)
        dist = abs(dist_from_center-led_dist)

        bri = p / beat_partition
        bri /= beat_ramp_up
        if bri > 1: bri = 1

        if p/ (1-beat_partition) > 1-fadeout:
            bri *= math.pow((1-(p / (1-beat_partition)))/(fadeout*2),0.5)

        dist *= max_channels
        if dist < 1.0:
            val = wave_brightness
            val *= wave_width-dist
            if val > 1: val = 1
            value += val * bri


    return value