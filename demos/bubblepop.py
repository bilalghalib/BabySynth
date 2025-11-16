# In bubble_pop.py, replace the handle_button_press method:

def handle_button_press(self, button):
    """Handle button press"""
    x, y = button.x, button.y
    bubble_popped = False
    
    with self.lock:
        if (x, y) in self.bubbles:
            # Pop the bubble!
            del self.bubbles[(x, y)]
            led = self.lp.panel.led(x, y)
            led.color = (0, 0, 0)
            bubble_popped = True
    
    # Only play sound and animation if we actually popped a bubble
    if bubble_popped:
        self.play_pop_sound(x, y)
        threading.Thread(target=self.pop_bubble, args=(x, y)).start()
