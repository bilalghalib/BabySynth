import sys
sys.path.insert(0, 'demos')
from britney import ToxicJam
import time

jam = ToxicJam()
print('\nToxicJam initialized')
print('Checking if LEDs are set...')

# Check a few LED colors
for y in [7, 6, 5, 1]:
    for x in range(min(4, 8)):
        led = jam.lp.panel.led(x, y)
        color = led.color
        if color != (0, 0, 0):
            print(f'LED ({x}, {y}): color = {color}')

print('\nPress any button on the Launchpad to test, or Ctrl+C to exit')
print('Waiting for 10 seconds...')
time.sleep(10)
