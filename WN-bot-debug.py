import pyautogui
import pygetwindow as gw
import keyboard
import random
import time
import datetime
import threading

expected_color = (255, 255, 255)
tolerance = 25
radius_x = 4
radius_y = 4
scroll_limit = 5
pause_key = "f9"
debug_key = "f10"
timeout = 1200
cooldown_after_reset = 5
shift_y = -10
debug_enabled = False


pyautogui_lock = threading.Lock()

layout = {
    "check_pos": (0.8859, 0.1222),
    "alt_check_pos": (0.8714, 0.1250),
    "click_area_1": ((0.8135, 0.145), (0.9196, 0.145)),
    "click_area_2": ((0.0675, 0.1583), (0.87, 0.1583)),
    "scroll_click_area": ((0.1415, 0.2787), (0.8023, 0.4815)),
    "reset_click": (0.8971, 0.0750),
    "reset_click_2": (0.2363, 0.4528),
}

def get_emulator_windows():
    windows = [w for w in gw.getWindowsWithTitle("") if w.title.strip()]
    return [w for w in windows if "BlueStacks" in w.title]

def log_action(window_title, message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{window_title}] {message}")

def rel_to_abs(window, rel_xy):
    x = window.left + int(rel_xy[0] * window.width)
    y = window.top + int(rel_xy[1] * window.height)
    return (x, y)

def is_window_valid(window):
    return not window.isMinimized and window.width > 0 and window.height > 0

def is_safe_point(x, y, margin=10):
    screen_w, screen_h = pyautogui.size()
    return (
        margin <= x <= screen_w - margin and
        margin <= y <= screen_h - margin
    )

def safe_click(window, pos, description="click"):
    x, y = pos

    if not is_safe_point(x, y):
        log_action(window.title, f"Skipped unsafe {description} at ({x}, {y})")
        return False

    try:
        with pyautogui_lock:
            pyautogui.click(x, y)
        return True
    except pyautogui.FailSafeException:
        log_action(window.title, "fail-safe triggered")
        raise

def safe_scroll(window, amount):
    try:
        with pyautogui_lock:
            pyautogui.scroll(amount)
        return True
    except pyautogui.FailSafeException:
        log_action(window.title, "fail-safe triggered")
        raise

def pixel_matches(pos, expected, tol=0, rx=1, ry=1):
    x, y = pos

    print(f"pixel_matches called at base pos: ({x}, {y})", flush=True)

    if not is_safe_point(x, y, margin=0):
        print(f"Position is unsafe/outside screen: ({x}, {y})", flush=True)
        return False

    for dx in range(-rx, rx + 1):
        for dy in range(-ry, ry + 1):
            try:
                check_x = x + dx
                check_y = y + dy
                pixel = pyautogui.pixel(check_x, check_y)

                print(f"Checking ({check_x}, {check_y}) = {pixel}", flush=True)

                if all(abs(pixel[i] - expected[i]) <= tol for i in range(3)):
                    print("MATCH FOUND", flush=True)
                    return True

            except Exception as e:
                print(f"Pixel read failed at ({x + dx}, {y + dy}): {repr(e)}", flush=True)

    return False

def draw_debug_dot(x, y):
    if not debug_enabled:
        return

    import tkinter as tk

    def _draw():
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.geometry(f"6x6+{x-3}+{y-3}")
        root.config(bg="red")
        root.after(300, root.destroy)
        root.mainloop()

    threading.Thread(target=_draw, daemon=True).start()

def click_random_in_area(window, area):
    if not is_window_valid(window):
        log_action(window.title, "Skipped click")
        return False

    (x1_rel, y1_rel), (x2_rel, y2_rel) = area

    x1, y1 = rel_to_abs(window, (x1_rel, y1_rel))
    x2, y2 = rel_to_abs(window, (x2_rel, y2_rel))

    x = random.randint(min(x1, x2), max(x1, x2))
    y = random.randint(min(y1, y2), max(y1, y2))

    return safe_click(window, (x, y), "random area click")

def scroll_down(window):
    safe_scroll(window, -500)
    time.sleep(3)

button_press_count = 0
button_press_lock = threading.Lock()

paused = False

def toggle_pause():
    global paused
    paused = not paused
    print(f"--- Script {'PAUSED' if paused else 'RESUMED'} ---")

def toggle_debug():
    global debug_enabled
    debug_enabled = not debug_enabled
    print(f"--- Debug dots {'ENABLED' if debug_enabled else 'DISABLED'} ---")

keyboard.add_hotkey(pause_key, toggle_pause)
keyboard.add_hotkey(debug_key, toggle_debug)

def handle_window(window):
    global button_press_count

    window_title = window.title
    last_seen = time.time()
    scroll_count = 0

    while True:
        if paused:
            time.sleep(1)
            continue

        if not is_window_valid(window):
            log_action(window_title, "Waiting...")
            time.sleep(5)
            continue

        check_positions = [
            rel_to_abs(window, layout["check_pos"]),
            rel_to_abs(window, layout["alt_check_pos"])
        ]

        found_button = False

        for pos in check_positions:
            x, y = pos

            for offset_y in [0, shift_y]:
                check_x = x
                check_y = y + offset_y

                draw_debug_dot(check_x, check_y)

                if pixel_matches(
                    (check_x, check_y),
                    expected_color,
                    tolerance,
                    radius_x,
                    radius_y
                ):
                    found_button = True
                    break

            if found_button:
                break

        if found_button:
            last_seen = time.time()
            scroll_count = 0

            click_random_in_area(window, layout["click_area_1"])
            time.sleep(2)
            click_random_in_area(window, layout["click_area_2"])

            with button_press_lock:
                button_press_count += 1
                if button_press_count % 2 == 0:
                    log_action(window_title, "Button press sequence triggered")

        else:
            if time.time() - last_seen > timeout:
                click_random_in_area(window, layout["scroll_click_area"])
                scroll_down(window)

                scroll_count += 1
                last_seen = time.time()

                log_action(window_title, f"Scroll #{scroll_count}")

                if scroll_count >= scroll_limit:
                    safe_click(
                        window,
                        rel_to_abs(window, layout["reset_click"]),
                        "reset click 1"
                    )

                    safe_scroll(window, 100)
                    time.sleep(0.5)

                    safe_click(
                        window,
                        rel_to_abs(window, layout["reset_click_2"]),
                        "reset click 2"
                    )

                    scroll_count = 0
                    log_action(window_title, "Performed reset sequence")
                    time.sleep(cooldown_after_reset)

        time.sleep(0.5)

def main():
    windows = get_emulator_windows()

    if not windows:
        print("No BlueStacks windows found. Open them first.")
        return

    print(f"Found {len(windows)} emulator window(s). Starting...")

    for window in windows[:4]:
        log_action(window.title, "Automation started.")
        t = threading.Thread(target=handle_window, args=(window,), daemon=True)
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- Script manually stopped ---")

if __name__ == "__main__":
    main()
