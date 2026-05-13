import pyautogui
import pygetwindow as gw
import keyboard
import time

# Edit this to match your emulator’s window title
WINDOW_TITLE = "BlueStacks"

# Try to find the emulator window
win = None
for w in gw.getWindowsWithTitle(WINDOW_TITLE):
    try:
        if w.visible:  # <-- fixed here
            win = w
            break
    except AttributeError:
        # Fallback for older versions
        win = w
        break

if not win:
    print(f"Could not find window titled '{WINDOW_TITLE}'.")
    exit()

print(f"Tracking window '{win.title}' at ({win.left}, {win.top}) size {win.width}x{win.height}")
print("Move your mouse to a position INSIDE the window and press 'p' to record it.")
print("Press 'esc' when you’re done.\n")

while True:
    if keyboard.is_pressed('esc'):
        print("Exiting.")
        break

    if keyboard.is_pressed('p'):
        x, y = pyautogui.position()
        rel_x = (x - win.left) / win.width
        rel_y = (y - win.top) / win.height
        print(f"Absolute: ({x}, {y})  →  Relative: ({rel_x:.4f}, {rel_y:.4f})")
        time.sleep(0.5)
