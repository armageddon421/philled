
import os
import math
import random

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

    random.seed(epoch*783627)
    bowl = [x for x in range(len(effects))]
    shuffled_effects = []
    while(len(bowl)):
        i = bowl[random.randrange(len(bowl))]
        bowl.remove(i)
        shuffled_effects.append(effects[i])

    active_effect = None

    for e in shuffled_effects:
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

        try:
            active_effect.prepare(maxchannels, etime, epoch)
        except AttributeError as e: #prepare function is optional
            pass
        except Exception as e:
            import sys
            sys.print_exception(e)
            print(type(e))
            for channel in channels:
                channel[1].duty(50)
            return

        for channel in channels:
            try:
                chn = channel[0]
                if reverse:
                    chn = maxchannels - chn - 1
                value = active_effect.render(chn, maxchannels, etime, epoch)
                value *= fade_multiplier
                value = math.pow(value, gamma)
                value = int(value * multiplier)
                if value < 0: value = 0
                if value > 1023: value = 1023
                channel[1].duty(value)
            except Exception as e:
                import sys
                sys.print_exception(e)
                print(type(e))
                channel[1].duty(50)
        