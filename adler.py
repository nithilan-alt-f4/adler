import tkinter as tk
from tkinter import ttk
import threading
import time
from pynput.mouse import Button, Controller
from pynput.keyboard import Listener, KeyCode

mouse = Controller()

# ── State ──────────────────────────────────────────────────────────────────
STATE_IDLE    = "idle"
STATE_RUNNING = "running"
STATE_PAUSED  = "paused"

state = STATE_IDLE
click_count = 0

hotkey_play_pause = KeyCode(char='-')
hotkey_stop        = KeyCode(char='=')

worker_thread = None


# ── Interruptible / pausable sleep ─────────────────────────────────────────

def pausable_sleep(seconds):
    """Sleeps in small increments, bailing out early on stop, freezing on pause."""
    end = time.time() + seconds
    while state != STATE_IDLE and time.time() < end:
        if state == STATE_PAUSED:
            time.sleep(0.05)
            end += 0.05  # push the target out so paused time doesn't count
            continue
        time.sleep(0.05)
    return state != STATE_IDLE


# ── Main click loop ────────────────────────────────────────────────────────

def countdown_and_click(button, interval, max_clicks, delay):
    global state, click_count

    for i in range(delay, 0, -1):
        if state == STATE_IDLE:
            return
        root.after(0, lambda i=i: status_var.set(f"Starting in {i}..."))
        time.sleep(1)

    if state == STATE_IDLE:
        return

    root.after(0, lambda: status_var.set("Running..."))

    while state != STATE_IDLE:
        if state == STATE_PAUSED:
            root.after(0, lambda: status_var.set("Paused"))
            while state == STATE_PAUSED:
                time.sleep(0.05)
            if state == STATE_IDLE:
                return
            root.after(0, lambda: status_var.set("Running..."))
            continue

        if max_clicks > 0 and click_count >= max_clicks:
            root.after(0, lambda: full_stop("Stopped (limit reached)"))
            return

        mouse.click(button)
        click_count += 1
        root.after(0, lambda c=click_count: click_count_var.set(f"Clicks: {c}"))

        alive = pausable_sleep(interval)
        if not alive:
            return


# ── Controls ───────────────────────────────────────────────────────────────

def set_buttons_running():
    play_pause_btn.config(text="⏸  Pause", bg="#f0b429")
    stop_btn.config(state="normal")

def set_buttons_paused():
    play_pause_btn.config(text="▶  Resume", bg=ACCENT)
    stop_btn.config(state="normal")

def set_buttons_idle():
    play_pause_btn.config(text="▶  Start", bg=ACCENT)
    stop_btn.config(state="disabled")


def full_stop(reason="Stopped"):
    global state
    state = STATE_IDLE
    status_var.set(reason)
    set_buttons_idle()


def start():
    global state, click_count, worker_thread

    try:
        hours   = int(entry_h.get()   or 0)
        minutes = int(entry_m.get()   or 0)
        seconds = float(entry_s.get() or 0)
        ms      = float(entry_ms.get() or 100)
        delay   = int(entry_delay.get() or 0)

        interval = hours * 3600 + minutes * 60 + seconds + ms / 1000
        if interval <= 0:
            interval = 0.05

        max_clicks = int(entry_repeat.get() or 0)

        btn_choice = btn_var.get()
        button = (Button.left   if btn_choice == "Left"   else
                  Button.right  if btn_choice == "Right"  else Button.middle)

        state = STATE_RUNNING
        click_count = 0
        click_count_var.set("Clicks: 0")
        set_buttons_running()

        worker_thread = threading.Thread(
            target=countdown_and_click,
            args=(button, interval, max_clicks, delay),
            daemon=True
        )
        worker_thread.start()

    except ValueError:
        status_var.set("Invalid input!")
        state = STATE_IDLE


def toggle_play_pause():
    global state
    if state == STATE_IDLE:
        start()
    elif state == STATE_RUNNING:
        state = STATE_PAUSED
        set_buttons_paused()
    elif state == STATE_PAUSED:
        state = STATE_RUNNING
        set_buttons_running()


def stop():
    full_stop("Stopped")


def on_press(key):
    if key == hotkey_play_pause:
        root.after(0, toggle_play_pause)
    elif key == hotkey_stop:
        root.after(0, stop)


# ── GUI ───────────────────────────────────────────────────────────────────

root = tk.Tk()
root.title("Adler")
root.resizable(False, False)
root.configure(bg="#1a1a2e")

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel",    background="#1a1a2e", foreground="#e0e0e0", font=("Courier New", 10))
style.configure("TFrame",    background="#1a1a2e")
style.configure("TEntry",    fieldbackground="#16213e", foreground="#e0e0e0",
                insertcolor="#e0e0e0", font=("Courier New", 11))
style.configure("TCombobox", fieldbackground="#16213e", foreground="#e0e0e0",
                background="#16213e", font=("Courier New", 11))
style.map("TCombobox", fieldbackground=[("readonly", "#16213e")],
                        foreground=[("readonly", "#e0e0e0")])

ACCENT = "#e94560"
BG     = "#1a1a2e"
CARD   = "#16213e"

# Title
tk.Label(root, text="A D L E R", bg=BG, fg=ACCENT,
         font=("Courier New", 20, "bold")).pack(pady=(20, 0))
tk.Label(root, text="auto clicker", bg=BG, fg="#666",
         font=("Courier New", 9)).pack(pady=(0, 4))
tk.Label(root, text="- play/pause  ·  = stop", bg=BG, fg="#444",
         font=("Courier New", 8)).pack(pady=(0, 10))

# ── Interval card ─────────────────────────────────────────────────────────

card1 = tk.Frame(root, bg=CARD, padx=14, pady=10)
card1.pack(padx=20, pady=6, fill="x")

tk.Label(card1, text="CLICK INTERVAL", bg=CARD, fg=ACCENT,
         font=("Courier New", 9, "bold")).grid(row=0, column=0, columnspan=8, sticky="w", pady=(0,6))

for col, label in enumerate(["hrs", "min", "sec", "ms"]):
    tk.Label(card1, text=label, bg=CARD, fg="#777",
             font=("Courier New", 8)).grid(row=1, column=col*2, padx=(0,2))

entry_h  = ttk.Entry(card1, width=4); entry_h.insert(0,  "0");   entry_h.grid(row=2, column=0, padx=3)
entry_m  = ttk.Entry(card1, width=4); entry_m.insert(0,  "0");   entry_m.grid(row=2, column=2, padx=3)
entry_s  = ttk.Entry(card1, width=4); entry_s.insert(0,  "0");   entry_s.grid(row=2, column=4, padx=3)
entry_ms = ttk.Entry(card1, width=5); entry_ms.insert(0, "100"); entry_ms.grid(row=2, column=6, padx=3)

# ── Options card ──────────────────────────────────────────────────────────

card2 = tk.Frame(root, bg=CARD, padx=14, pady=10)
card2.pack(padx=20, pady=6, fill="x")

tk.Label(card2, text="MOUSE BUTTON", bg=CARD, fg=ACCENT,
         font=("Courier New", 9, "bold")).grid(row=0, column=0, sticky="w")
tk.Label(card2, text="REPEAT (0 = ∞)", bg=CARD, fg=ACCENT,
         font=("Courier New", 9, "bold")).grid(row=0, column=2, sticky="w", padx=(20,0))
tk.Label(card2, text="START DELAY (s)", bg=CARD, fg=ACCENT,
         font=("Courier New", 9, "bold")).grid(row=0, column=4, sticky="w", padx=(20,0))

btn_var = tk.StringVar(value="Left")
ttk.Combobox(card2, textvariable=btn_var, values=["Left","Right","Middle"],
             state="readonly", width=8).grid(row=1, column=0, pady=4)

entry_repeat = ttk.Entry(card2, width=6)
entry_repeat.insert(0, "0")
entry_repeat.grid(row=1, column=2, padx=(20,0), pady=4)

entry_delay = ttk.Entry(card2, width=6)
entry_delay.insert(0, "3")
entry_delay.grid(row=1, column=4, padx=(20,0), pady=4)

# ── Status ────────────────────────────────────────────────────────────────

status_var      = tk.StringVar(value="Stopped")
click_count_var = tk.StringVar(value="Clicks: 0")

tk.Label(root, textvariable=status_var, bg=BG, fg="#44ff99",
         font=("Courier New", 11, "bold")).pack(pady=(12, 0))
tk.Label(root, textvariable=click_count_var, bg=BG, fg="#777",
         font=("Courier New", 10)).pack()

# ── Controls: Play/Pause + Stop ───────────────────────────────────────────

controls = tk.Frame(root, bg=BG)
controls.pack(pady=16)

play_pause_btn = tk.Button(
    controls, text="▶  Start",
    bg=ACCENT, fg="white", activebackground="#c73652", activeforeground="white",
    font=("Courier New", 13, "bold"), relief="flat", padx=24, pady=8,
    cursor="hand2", command=toggle_play_pause
)
play_pause_btn.grid(row=0, column=0, padx=6)

stop_btn = tk.Button(
    controls, text="■  Stop",
    bg="#333", fg="white", activebackground="#222", activeforeground="white",
    font=("Courier New", 13, "bold"), relief="flat", padx=24, pady=8,
    cursor="hand2", command=stop, state="disabled"
)
stop_btn.grid(row=0, column=1, padx=6)

# ── Keyboard listener ─────────────────────────────────────────────────────

listener = Listener(on_press=on_press)
listener.daemon = True
listener.start()

root.mainloop()
