
import os
import math

effects = []
total_time = 0
maxchannels = 0
fadetime = 0

def init(max_channels, fade_time):
    global effects
    global total_time
    global maxchannels
    global fadetime

    maxchannels = max_channels
    fadetime = fade_time

    for filename in os.listdir("effects"):
        print(filename)
        if filename[-3:] == ".py":
            modulename = filename[:-3]
            module = __import__("effects/" + modulename)
            if module.enabled:
                effects.append(module)
                if(module.solo):
                    effects = [module]
                    break

    for effect in effects:
        total_time += effect.runtime
        if effect.fade:
            total_time += fadetime * 2
    
    print("total time:", total_time, "ms")

def run(channels, time, multiplier, gamma):
    global effects
    global total_time
    global maxchannels
    global fadetime

    if(total_time < 10): return

    epoch = time // total_time
    etime = time % total_time

    reverse = (epoch%2) == 1

    active_effect = None

    for e in effects:
        effective_runtime = e.runtime
        if e.fade:
            effective_runtime += fadetime * 2

        if etime < effective_runtime:
            active_effect = e
            break
        etime -= effective_runtime
    
    if(active_effect):
        fade_multiplier = 1.0

        if active_effect.fade:
            etime -= fadetime

            if etime < 0:
                fade_multiplier = 1.0 - etime / -fadetime
            elif etime > active_effect.runtime:
                fade_multiplier = 1.0 - (etime-active_effect.runtime)/fadetime

        for channel in channels:
            chn = channel[0]
            if reverse:
                chn = maxchannels - chn - 1
            value = active_effect.render(chn, maxchannels, etime, epoch)
            value *= fade_multiplier
            value = math.pow(value, gamma)
            value = int(value * multiplier)
            channel[1].duty(value)
        