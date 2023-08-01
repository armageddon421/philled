# control parameters
enabled = True
solo = False

# external parameters
runtime = 15000 #ms
fade = True

# effect parameters
min_flashes = 3
max_flashes = 7
base_brightness = 0.35
flash_time = 50
recover_time = 500
enable_zero_recovery_variant = True
recover_brightness = 0.0
enable_recovery_inversion_variant = True

import math
import random

def render(channel, max_channels, time, epoch):

    recover_bri = recover_brightness
    recover_t = recover_time

    if (epoch//2)%2 and enable_recovery_inversion_variant:
        recover_bri = 1.0-recover_brightness
    
    if epoch%2 and enable_zero_recovery_variant:
        recover_t = 0

    seed = (epoch * 412789 + channel * 17625)*243
    random.seed(seed)

    flashes = random.randint(min_flashes,max_flashes)


    prev_flash = -100000
    #next_flash = runtime + 100000

    for i in range(flashes):
        flashtime = random.randrange(runtime)

        if flashtime < time and flashtime > prev_flash:
            prev_flash = flashtime
        #elif flashtime > time and flashtime < next_flash:
        #    next_flash = flashtime

    value = base_brightness

    flash_age = time - prev_flash

    if flash_age > (flash_time+recover_t):
        pass #base brightness
    elif flash_age > flash_time:
        k = (flash_age-flash_time)/recover_t
        value = (1.0-k)*recover_bri + k*base_brightness
    elif flash_age > 0:
        value = 1.0

    

    return value