# control parameters
enabled = True
solo = False

# external parameters
runtime = 12000 #ms
fade = False

# effect parameters
dot_brightness = 1.0
stack_brightness = 0.25

import math

def render(channel, max_channels, time, epoch):

    steps = max_channels/2*(max_channels+1)
    timef = time/runtime
    current_step = int(steps*timef)

    current_stack = 0
    stack_steps = 0
    dot_index = 0
    for i in range(max_channels):
        steps = max_channels-i
        if(stack_steps + steps > current_step):
            current_stack = i
            dot_index = max_channels-(current_step-stack_steps)-1
            break
        stack_steps += steps

    if channel == dot_index:
        return dot_brightness
    
    if channel < current_stack:
        return stack_brightness

    return 0.0