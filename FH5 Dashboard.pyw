import socket
import struct
import threading
import tkinter as tk
from tkinter import ttk
import math

UDP_IP = "127.0.0.1"
UDP_PORT = 5555

class ForzaCustomDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Forza Horizon 5 - Custom Telemetry")
        self.root.geometry("1340x780")
        self.root.configure(bg="#0a0a0a")
        self.root.attributes("-topmost", True)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#0a0a0a", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1f1f1f", foreground="#aaaaaa",
                        padding=[20, 8], font=("Consolas", 11, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#00cc88")], 
                  foreground=[("selected", "#ffffff")])
        style.configure("TFrame", background="#0a0a0a")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)

        # TAB 1: MAIN DASHBOARD
        self.tab_main = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_main, text="  MAIN DASHBOARD  ")

        self.canvas_main = tk.Canvas(self.tab_main, width=1300, height=520, bg="#0a0a0a", highlightthickness=0)
        self.canvas_main.pack(pady=20)

        self.create_tachometer(260, 240)
        self.create_speed_display()
        self.create_turbo_gauge(590, 250)

        # TAB 2: TIRE TEMPERATURES
        self.tab_tires = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tires, text="  TIRE TEMPERATURES  ")

        self.canvas_tires = tk.Canvas(self.tab_tires, width=1300, height=520, bg="#0a0a0a", highlightthickness=0)
        self.canvas_tires.pack(pady=40)

        self.create_wheel_temps(650, 260)
        self.create_small_gear_display()

        # TAB 3: G-FORCE
        self.tab_gforce = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_gforce, text="  G-FORCE  ")

        self.canvas_gforce = tk.Canvas(self.tab_gforce, width=1300, height=520, bg="#0a0a0a", highlightthickness=0)
        self.canvas_gforce.pack(pady=20)

        self.create_gforce_graph(650, 260)

        # SHARED BOTTOM BAR
        self.bottom_frame = tk.Frame(self.root, bg="#0a0a0a")
        self.bottom_frame.pack(fill="x", pady=12, padx=20)

        self.labels = {}
        fields = ["Throttle", "Brake", "Steering", "G-Force"]
        colors = ["#00ffcc", "#ff5555", "#ffff66", "#00ccff"]

        for i, (field, color) in enumerate(zip(fields, colors)):
            frame = tk.Frame(self.bottom_frame, bg="#0a0a0a")
            frame.grid(row=0, column=i, padx=50)
            tk.Label(frame, text=field, font=("Consolas", 12), fg="#777777", bg="#0a0a0a").pack()
            self.labels[field] = tk.Label(frame, text="--", font=("Consolas", 24, "bold"), 
                                          fg=color, bg="#0a0a0a")
            self.labels[field].pack()

        self.status = tk.Label(self.root, text="Waiting for Forza telemetry...",
                               font=("Consolas", 14, "bold"), fg="#ffaa00", bg="#0a0a0a")
        self.status.pack(pady=8)

        threading.Thread(target=self.listen_udp, daemon=True).start()
        self.root.mainloop()

    # ===================== GAUGE CREATION METHODS =====================
    def create_turbo_gauge(self, cx, cy):
        radius = 58
        self.canvas_main.create_oval(cx-radius-12, cy-radius-12, cx+radius+12, cy+radius+12,
                                     outline="#222222", width=20)
        self.turbo_bg = self.canvas_main.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                                                     outline="#444444", width=10)

        self.boost_arc = self.canvas_main.create_arc(cx-radius, cy-radius, cx+radius, cy+radius,
                                                     start=200, extent=0, style="arc",
                                                     outline="#00ccff", width=13)

        zero_angle = math.radians(200 + (15 / 60) * 270)
        zx = cx + (radius - 6) * math.cos(zero_angle)
        zy = cy + (radius - 6) * math.sin(zero_angle)
        ex = cx + (radius + 8) * math.cos(zero_angle)
        ey = cy + (radius + 8) * math.sin(zero_angle)
        self.zero_line = self.canvas_main.create_line(zx, zy, ex, ey, fill="#ffffff", width=3)

        self.canvas_main.create_oval(cx-26, cy-26, cx+26, cy+26, fill="#1a1a1a", outline="#555555", width=5)

        self.canvas_main.create_text(cx, cy-78, text="BOOST", font=("Consolas", 13, "bold"), fill="#ffaa00")
        self.boost_text = self.canvas_main.create_text(cx, cy+4, text="0.0", 
                                                       font=("Consolas", 26, "bold"), fill="#ffcc33")
        self.canvas_main.create_text(cx, cy+32, text="psi", font=("Consolas", 11, "bold"), fill="#888888")

    def create_tachometer(self, cx, cy):
        self.tacho_center = (cx, cy)
        self.tacho_radius = 165
        canvas = self.canvas_main
        canvas.create_oval(cx-175, cy-175, cx+175, cy+175, outline="#222222", width=36)
        canvas.create_oval(cx-158, cy-158, cx+158, cy+158, outline="#1a1a1a", width=24)

        for i in range(11):
            angle = math.radians(135 + i * 27)
            x1 = cx + (self.tacho_radius - 30) * math.cos(angle)
            y1 = cy + (self.tacho_radius - 30) * math.sin(angle)
            x2 = cx + self.tacho_radius * math.cos(angle)
            y2 = cy + self.tacho_radius * math.sin(angle)
            color = "#ff3366" if i >= 8 else "#eeeeee"
            canvas.create_line(x1, y1, x2, y2, fill=color, width=4)

            nx = cx + (self.tacho_radius - 68) * math.cos(angle)
            ny = cy + (self.tacho_radius - 68) * math.sin(angle)
            canvas.create_text(nx, ny, text=str(i), fill="#bbbbbb", font=("Consolas", 13, "bold"))

        canvas.create_arc(cx-158, cy-158, cx+158, cy+158,
                          start=135+8*27, extent=81, outline="#ff3366", style="arc", width=26)

        self.tacho_needle = canvas.create_line(cx, cy, cx, cy-130, fill="#ffff00", width=6, arrow="last")
        canvas.create_oval(cx-11, cy-11, cx+11, cy+11, fill="#1a1a1a", outline="#ffff00", width=3)
        self.rpm_text = canvas.create_text(cx, cy + 95, text="0000 RPM", 
                                           fill="#ffff00", font=("Consolas", 19, "bold"))

    def create_speed_display(self):
        canvas = self.canvas_main
        self.speed_text = canvas.create_text(880, 215, text="000", 
                                             font=("Consolas", 128, "bold"), fill="#ff3366")
        canvas.create_text(880, 325, text="MPH", 
                           font=("Consolas", 32, "bold"), fill="#ff7777")
        self.gear_text = canvas.create_text(880, 105, text="N", 
                                            font=("Consolas", 92, "bold"), fill="#ffff44")

    def create_small_gear_display(self):
        self.small_gear_text = self.canvas_tires.create_text(650, 100, text="N", 
                                                             font=("Consolas", 48, "bold"), fill="#ffff44")

    def create_wheel_temps(self, cx, cy):
        self.wheel_positions = {
            "FL": (cx - 140, cy - 80),
            "FR": (cx + 140, cy - 80),
            "RL": (cx - 140, cy + 80),
            "RR": (cx + 140, cy + 80)
        }
        self.wheel_labels = {}
        canvas = self.canvas_tires

        for pos, (x, y) in self.wheel_positions.items():
            canvas.create_oval(x-52, y-52, x+52, y+52, outline="#444444", width=18, fill="#111111")
            canvas.create_oval(x-34, y-34, x+34, y+34, outline="#222222", width=9, fill="#1a1a1a")
            label_x = x + 95
            self.wheel_labels[pos] = canvas.create_text(label_x, y, text="--°F",
                                                        font=("Consolas", 22, "bold"), fill="#88ccff", anchor="w")
            canvas.create_text(x, y-75, text=pos, font=("Consolas", 16, "bold"), fill="#666666")

    def create_gforce_graph(self, cx, cy):
        self.gforce_center = (cx, cy)
        self.gforce_radius = 235
        canvas = self.canvas_gforce

        canvas.create_oval(cx - self.gforce_radius - 18, cy - self.gforce_radius - 18,
                           cx + self.gforce_radius + 18, cy + self.gforce_radius + 18,
                           outline="#1a1a1a", width=36)
        canvas.create_oval(cx - self.gforce_radius, cy - self.gforce_radius,
                           cx + self.gforce_radius, cy + self.gforce_radius,
                           outline="#ff3333", width=10)
        canvas.create_oval(cx - self.gforce_radius + 40, cy - self.gforce_radius + 40,
                           cx + self.gforce_radius - 40, cy + self.gforce_radius - 40,
                           outline="#333333", width=4)

        canvas.create_line(cx - self.gforce_radius - 20, cy, cx + self.gforce_radius + 20, cy, 
                           fill="#444444", width=3)
        canvas.create_line(cx, cy - self.gforce_radius - 20, cx, cy + self.gforce_radius + 20, 
                           fill="#444444", width=3)

        self.gforce_line = canvas.create_line(cx, cy, cx, cy, fill="#ffff00", width=5)
        self.gforce_dot = canvas.create_oval(cx-13, cy-13, cx+13, cy+13, 
                                             fill="#0088ff", outline="#00ddff", width=4)

        self.gforce_text = canvas.create_text(cx, cy + 290, text="0.00 g",
                                              font=("Consolas", 36, "bold"), fill="#00ffcc")

        canvas.create_text(cx - 175, cy, text="← LAT", font=("Consolas", 14, "bold"), fill="#888888")
        canvas.create_text(cx + 175, cy, text="LAT →", font=("Consolas", 14, "bold"), fill="#888888")
        canvas.create_text(cx, cy - 175, text="LONG ↑", font=("Consolas", 14, "bold"), fill="#888888")
        canvas.create_text(cx, cy + 175, text="LONG ↓", font=("Consolas", 14, "bold"), fill="#888888")

    # ===================== UPDATE METHODS =====================
    def update_tachometer(self, rpm):
        rpm_clamped = min(max(rpm, 0), 10000)
        angle = math.radians(135 + (rpm_clamped / 10000) * 270)
        x = self.tacho_center[0] + 130 * math.cos(angle)
        y = self.tacho_center[1] + 130 * math.sin(angle)
        self.canvas_main.coords(self.tacho_needle, self.tacho_center[0], self.tacho_center[1], x, y)
        color = "#ff3366" if rpm > 8500 else "#ffff44"
        self.canvas_main.itemconfig(self.tacho_needle, fill=color)
        self.canvas_main.itemconfig(self.rpm_text, text=f"{int(rpm):04d} RPM", fill=color)

    def update_wheel_temps(self, fl, fr, rl, rr):
        temps = {"FL": fl, "FR": fr, "RL": rl, "RR": rr}
        for pos, temp in temps.items():
            if temp < 0 or temp > 400:
                color = "#666666"
                display_temp = "--"
            else:
                temp_clamped = max(60, min(temp, 350))
                if temp_clamped >= 260: color = "#ff3366"
                elif temp_clamped >= 180: color = "#00ff99"
                elif temp_clamped >= 140: color = "#ffdd33"
                else: color = "#77bbff"
                display_temp = f"{int(temp_clamped)}°F"
            self.canvas_tires.itemconfig(self.wheel_labels[pos], text=display_temp, fill=color)

    def update_boost(self, boost_psi):
        boost_clamped = max(-18.0, min(boost_psi, 45.0))

        min_psi = -15.0
        max_psi = 45.0
        span = max_psi - min_psi
        normalized = (boost_clamped - min_psi) / span
        extent = -normalized * 270

        if boost_clamped >= 25:
            arc_color = "#ff3366"
        elif boost_clamped >= 12:
            arc_color = "#ff8800"
        elif boost_clamped >= 5:
            arc_color = "#ffcc00"
        elif boost_clamped >= 0:
            arc_color = "#aaff00"
        else:
            arc_color = "#00ccff"

        self.canvas_main.itemconfig(self.boost_arc, extent=extent, outline=arc_color, start=200)
        self.canvas_main.itemconfig(self.boost_text, text=f"{boost_clamped:.1f}", fill=arc_color)

    def update_gforce_graph(self, long_accel, lat_accel):
        long_g = long_accel / 9.81
        lat_g  = lat_accel / 9.81
        g_magnitude = math.sqrt(long_g**2 + lat_g**2)
        max_g = 2.5
        normalized = min(g_magnitude / max_g, 1.0)

        dot_x = self.gforce_center[0] - lat_g * (self.gforce_radius * 0.92 / max_g)
        dot_y = self.gforce_center[1] + long_g * (self.gforce_radius * 0.92 / max_g)

        dx = dot_x - self.gforce_center[0]
        dy = dot_y - self.gforce_center[1]
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > self.gforce_radius * 0.92:
            factor = (self.gforce_radius * 0.92) / distance
            dot_x = self.gforce_center[0] + dx * factor
            dot_y = self.gforce_center[1] + dy * factor

        self.canvas_gforce.coords(self.gforce_line, self.gforce_center[0], self.gforce_center[1], dot_x, dot_y)
        self.canvas_gforce.coords(self.gforce_dot, dot_x-13, dot_y-13, dot_x+13, dot_y+13)

        color = "#ff3366" if g_magnitude > 1.2 else "#00ff99"
        self.canvas_gforce.itemconfig(self.gforce_text, text=f"{g_magnitude:.2f} g", fill=color)

    def update_display(self, data):
        try:
            is_race_on = struct.unpack_from('<I', data, 0)[0]
            if is_race_on == 0:
                self.status.config(text="Not racing - telemetry paused", fg="#ffaa00")
                return

            rpm = struct.unpack_from('<f', data, 16)[0]
            speed_ms = struct.unpack_from('<f', data, 256)[0]
            speed_mph = max(0, int(speed_ms * 2.23694))

            # === FIXED: Throttle & Brake now correctly shown as 0-100% ===
            throttle = struct.unpack_from('<B', data, 315)[0]
            brake = struct.unpack_from('<B', data, 316)[0]
            throttle_pct = round((throttle / 255.0) * 100)
            brake_pct   = round((brake / 255.0) * 100)

            gear = struct.unpack_from('<B', data, 319)[0]
            steer = struct.unpack_from('<b', data, 320)[0]

            tire_fl = struct.unpack_from('<f', data, 268)[0]
            tire_fr = struct.unpack_from('<f', data, 272)[0]
            tire_rl = struct.unpack_from('<f', data, 276)[0]
            tire_rr = struct.unpack_from('<f', data, 280)[0]

            boost_psi = struct.unpack_from('<f', data, 284)[0]
            lat_accel  = struct.unpack_from('<f', data, 20)[0]
            long_accel = struct.unpack_from('<f', data, 28)[0]

            gear_text = str(gear) if 1 <= gear <= 10 else "N"

            self.update_tachometer(rpm)
            self.update_wheel_temps(tire_fl, tire_fr, tire_rl, tire_rr)
            self.update_boost(boost_psi)
            self.update_gforce_graph(long_accel, lat_accel)

            self.canvas_main.itemconfig(self.speed_text, text=f"{speed_mph:03d}")
            self.canvas_main.itemconfig(self.gear_text, text=gear_text)
            self.canvas_tires.itemconfig(self.small_gear_text, text=gear_text)

            # Updated bottom bar with proper percentages
            self.labels["Throttle"].config(text=f"{throttle_pct}%")
            self.labels["Brake"].config(text=f"{brake_pct}%")
            self.labels["Steering"].config(text=f"{steer}°")

            lat_g = lat_accel / 9.81
            long_g = long_accel / 9.81
            g_magnitude = math.sqrt(lat_g**2 + long_g**2)
            self.labels["G-Force"].config(text=f"{g_magnitude:.2f}g", 
                                          fg="#ff3366" if g_magnitude > 1.2 else "#00ff99")

            self.status.config(text="● LIVE TELEMETRY", fg="#00ff88")

        except Exception as e:
            self.status.config(text="Parse Error", fg="#ff5555")
            print("Update error:", e)

    def listen_udp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        print(f"Listening for Forza Horizon 5 telemetry on {UDP_IP}:{UDP_PORT}...")

        while True:
            try:
                data, _ = sock.recvfrom(1500)
                if len(data) >= 323:
                    self.root.after(0, self.update_display, data)
            except:
                pass

if __name__ == "__main__":
    ForzaCustomDashboard()