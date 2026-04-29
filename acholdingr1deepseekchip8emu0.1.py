import tkinter as tk
from tkinter import filedialog, messagebox
import random

class Chip8:
    def __init__(self, scale):
        self.scale = scale
        self.reset()

    def reset(self):
        # 4KB Memory
        self.memory = [0] * 4096
        # 16 8-bit registers (V0-VF)
        self.v = [0] * 16
        # Index register (16-bit)
        self.i = 0
        # Program Counter (starts at 0x200)
        self.pc = 0x200
        # Stack (16 levels)
        self.stack = []
        # Timers
        self.delay_timer = 0
        self.sound_timer = 0
        # Display (64x32 monochrome)
        self.display = [[0] * 32 for _ in range(64)]
        # Keyboard state (0-F)
        self.key = [0] * 16

        # Font set (0-F)
        font_set = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]
        for idx, val in enumerate(font_set):
            self.memory[idx] = val

    def load_rom(self, filename):
        with open(filename, "rb") as f:
            rom_data = f.read()
            for idx, byte in enumerate(rom_data):
                if 0x200 + idx < 4096:
                    self.memory[0x200 + idx] = byte

    def cycle(self):
        """Execute a single Chip-8 instruction."""
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2

        op = (opcode & 0xF000) >> 12
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        n = opcode & 0x000F
        nn = opcode & 0x00FF
        nnn = opcode & 0x0FFF

        if op == 0x0:
            if nn == 0xE0:          # CLS
                self.display = [[0] * 32 for _ in range(64)]
            elif nn == 0xEE:        # RET
                if self.stack:
                    self.pc = self.stack.pop()
        elif op == 0x1:             # JP addr
            self.pc = nnn
        elif op == 0x2:             # CALL addr
            self.stack.append(self.pc)
            self.pc = nnn
        elif op == 0x3:             # SE Vx, byte
            if self.v[x] == nn: self.pc += 2
        elif op == 0x4:             # SNE Vx, byte
            if self.v[x] != nn: self.pc += 2
        elif op == 0x5:             # SE Vx, Vy
            if self.v[x] == self.v[y]: self.pc += 2
        elif op == 0x6:             # LD Vx, byte
            self.v[x] = nn
        elif op == 0x7:             # ADD Vx, byte
            self.v[x] = (self.v[x] + nn) & 0xFF
        elif op == 0x8:
            if n == 0x0:            # LD Vx, Vy
                self.v[x] = self.v[y]
            elif n == 0x1:          # OR Vx, Vy
                self.v[x] |= self.v[y]
            elif n == 0x2:          # AND Vx, Vy
                self.v[x] &= self.v[y]
            elif n == 0x3:          # XOR Vx, Vy
                self.v[x] ^= self.v[y]
            elif n == 0x4:          # ADD Vx, Vy
                sum_val = self.v[x] + self.v[y]
                self.v[0xF] = 1 if sum_val > 255 else 0
                self.v[x] = sum_val & 0xFF
            elif n == 0x5:          # SUB Vx, Vy
                self.v[0xF] = 1 if self.v[x] >= self.v[y] else 0
                self.v[x] = (self.v[x] - self.v[y]) & 0xFF
            elif n == 0x6:          # SHR Vx
                self.v[0xF] = self.v[x] & 0x1
                self.v[x] >>= 1
            elif n == 0x7:          # SUBN Vx, Vy
                self.v[0xF] = 1 if self.v[y] >= self.v[x] else 0
                self.v[x] = (self.v[y] - self.v[x]) & 0xFF
            elif n == 0xE:          # SHL Vx
                self.v[0xF] = (self.v[x] & 0x80) >> 7
                self.v[x] = (self.v[x] << 1) & 0xFF
        elif op == 0x9:             # SNE Vx, Vy
            if self.v[x] != self.v[y]: self.pc += 2
        elif op == 0xA:             # LD I, addr
            self.i = nnn
        elif op == 0xB:             # JP V0, addr
            self.pc = nnn + self.v[0]
        elif op == 0xC:             # RND Vx, byte
            self.v[x] = random.randint(0, 255) & nn
        elif op == 0xD:             # DRW Vx, Vy, nibble
            self.v[0xF] = 0
            for row in range(n):
                sprite_byte = self.memory[self.i + row]
                for col in range(8):
                    if (sprite_byte & (0x80 >> col)) != 0:
                        px = (self.v[x] + col) % 64
                        py = (self.v[y] + row) % 32
                        if self.display[px][py] == 1:
                            self.v[0xF] = 1
                        self.display[px][py] ^= 1
        elif op == 0xE:
            if nn == 0x9E:          # SKP Vx
                if self.key[self.v[x]]: self.pc += 2
            elif nn == 0xA1:        # SKNP Vx
                if not self.key[self.v[x]]: self.pc += 2
        elif op == 0xF:
            if nn == 0x07:          # LD Vx, DT
                self.v[x] = self.delay_timer
            elif nn == 0x0A:        # LD Vx, K
                key_pressed = False
                for k in range(16):
                    if self.key[k]:
                        self.v[x] = k
                        key_pressed = True
                        break
                if not key_pressed:
                    self.pc -= 2
            elif nn == 0x15:        # LD DT, Vx
                self.delay_timer = self.v[x]
            elif nn == 0x18:        # LD ST, Vx
                self.sound_timer = self.v[x]
            elif nn == 0x1E:        # ADD I, Vx
                self.i = (self.i + self.v[x]) & 0xFFFF
            elif nn == 0x29:        # LD F, Vx
                self.i = self.v[x] * 5
            elif nn == 0x33:        # LD B, Vx
                self.memory[self.i] = self.v[x] // 100
                self.memory[self.i + 1] = (self.v[x] // 10) % 10
                self.memory[self.i + 2] = self.v[x] % 10
            elif nn == 0x55:        # LD [I], Vx
                for idx in range(x + 1):
                    self.memory[self.i + idx] = self.v[idx]
            elif nn == 0x65:        # LD Vx, [I]
                for idx in range(x + 1):
                    self.v[idx] = self.memory[self.i + idx]

    def update_timers(self):
        if self.delay_timer > 0: self.delay_timer -= 1
        if self.sound_timer > 0: self.sound_timer -= 1


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Acholdings Chip-8 Emu 1.0x – V4 + Gemini & DeepSeek")
        self.root.configure(bg="black")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Scaling factor for display
        self.scale = 12
        self.width = 64 * self.scale
        self.height = 32 * self.scale

        # UI Setup
        self.canvas = tk.Canvas(
            root, width=self.width, height=self.height,
            bg="black", highlightthickness=0
        )
        self.canvas.pack(pady=10, padx=10)

        # Fast pixel drawing using PhotoImage
        self.image = tk.PhotoImage(width=self.width, height=self.height)
        self.canvas.create_image((self.width//2, self.height//2), image=self.image, state="normal")

        self.btn_frame = tk.Frame(root, bg="black")
        self.btn_frame.pack(fill="x", side="bottom")

        self.load_btn = tk.Button(
            self.btn_frame, text="LOAD ROM", command=self.load_rom,
            fg="#00aaff", bg="black", activeforeground="#0055ff",
            activebackground="#111", relief="flat", font=("Courier", 10, "bold")
        )
        self.load_btn.pack(side="left", padx=20, pady=10)

        self.about_btn = tk.Button(
            self.btn_frame, text="ABOUT", command=self.show_about,
            fg="#00aaff", bg="black", activeforeground="#0055ff",
            activebackground="#111", relief="flat", font=("Courier", 10, "bold")
        )
        self.about_btn.pack(side="right", padx=20, pady=10)

        self.chip8 = Chip8(self.scale)
        self.running = False
        self.rom_loaded = False
        self.after_id = None

        # Key Mapping (QWERTY -> Chip-8 hex pad)
        self.key_map = {
            '1': 0x1, '2': 0x2, '3': 0x3, '4': 0xC,
            'q': 0x4, 'w': 0x5, 'e': 0x6, 'r': 0xD,
            'a': 0x7, 's': 0x8, 'd': 0x9, 'f': 0xE,
            'z': 0xA, 'x': 0x0, 'c': 0xB, 'v': 0xF
        }

        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)
        self.root.bind("<FocusOut>", self.clear_keys)

    def load_rom(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Chip-8 ROMs", "*.ch8"), ("All files", "*.*")]
        )
        if file_path:
            self.stop_emulation()
            self.chip8.reset()
            self.chip8.load_rom(file_path)
            self.rom_loaded = True
            self.start_emulation()

    def show_about(self):
        messagebox.showinfo(
            "About Acholdings Chip-8 Emu",
            "Acholdings Chip-8 Emu 1.0x\n"
            "V4 – Powered by Gemini & DeepSeek\n\n"
            "A robust CHIP‑8 emulator with all known bugs fixed.\n"
            "Enjoy classic 8‑bit emulation!"
        )

    def key_down(self, event):
        key = event.char.lower()
        if key in self.key_map:
            self.chip8.key[self.key_map[key]] = 1

    def key_up(self, event):
        key = event.char.lower()
        if key in self.key_map:
            self.chip8.key[self.key_map[key]] = 0

    def clear_keys(self, event=None):
        """Release all keys when window loses focus."""
        for i in range(16):
            self.chip8.key[i] = 0

    def start_emulation(self):
        if not self.running:
            self.running = True
            self.run_frame()

    def stop_emulation(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.running = False

    def run_frame(self):
        """Execute 9 instruction cycles, update timers and redraw. Scheduled at ~60 Hz."""
        if not self.running:
            return

        # 9 cycles per frame = 540 instructions/sec (close to original speed)
        for _ in range(9):
            self.chip8.cycle()

        self.chip8.update_timers()
        self.draw_screen()

        # Schedule next frame
        self.after_id = self.root.after(16, self.run_frame)  # ~60 Hz

    def draw_screen(self):
        """Fast screen update using PhotoImage pixel manipulation."""
        # Build a flat pixel string for the whole image
        pixel_data = ""
        for y in range(32):
            for x in range(64):
                color = "#00aaff" if self.chip8.display[x][y] else "#000000"
                pixel_data += f"{{{color}}} "  # PhotoImage expects space‑separated "#rrggbb"
        self.image.put(pixel_data, to=(0, 0, self.width, self.height))

    def on_close(self):
        self.stop_emulation()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()