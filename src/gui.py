import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pygame
import os
import threading
import ast
from src.pattern import Pattern
from src.renderer import Renderer
from src.stdlib import beep, elastic_beeps, silence, echo_pattern, cusp_crescendo, reverse, chord, note_to_freq, crossfade

class AudioApp:
    def __init__(self, root, ffmpeg_path="ffmpeg"):
        self.root = root
        self.root.title("Musical Jades v0.2")
        self.root.geometry("800x600")
        
        # Theme Colors (Musical Jades: Forest, Sage, Olive)
        self.colors = {
            "bg_main": "#1B2E25",      # Deep Forest Green
            "bg_editor": "#12201A",    # Darker Jungle Green
            "fg_text": "#E0F2E0",      # Pale Mint
            "fg_dim": "#8FA394",       # Sage Grey
            "btn_bg": "#2D4D3D",       # Olive/Forest mix
            "btn_active": "#3E6651",   # Lighter Jade
            "highlight": "#509E75",    # Jade Green
            "bg_sidebar": "#1B2E25"    # Sidebar Background (Same as Main for unification)
        }
        
        self.root.configure(bg=self.colors["bg_main"])
        
        self.ffmpeg_path = ffmpeg_path
        self.renderer = Renderer(bpm=120, ffmpeg_path=self.ffmpeg_path)
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        self._setup_ui()
        
        # Default code
        default_code = 'beep()'
        self.text_editor.insert(tk.END, default_code)

    def _setup_ui(self):
        # Main Layout Container
        self.main_container = tk.Frame(self.root, bg=self.colors["bg_main"])
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left Sidebar
        self.sidebar = tk.Frame(self.main_container, bg=self.colors["bg_editor"], width=250)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.sidebar.pack_propagate(False) # Force width
        
        self._create_sidebar()
        self._create_extended_bar() # Create but don't show yet
        
        # Right Content Area
        right_frame = tk.Frame(self.main_container, bg=self.colors["bg_main"])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ... Editor (Moved to right_frame) ...
        lbl_title = tk.Label(right_frame, text="Pattern Description (Python Code):", 
                             bg=self.colors["bg_main"], fg=self.colors["fg_text"], font=("Segoe UI", 10, "bold"))
        lbl_title.pack(anchor="w")
        
        self.text_editor = scrolledtext.ScrolledText(right_frame, height=15, font=("Consolas", 12),
                                                     bg=self.colors["bg_editor"], fg=self.colors["fg_text"],
                                                     insertbackground="white", relief=tk.FLAT)
        self.text_editor.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # ... Controls (Moved to right_frame) ...
        # Middle Frame: Controls
        control_frame = tk.Frame(right_frame, bg=self.colors["bg_main"])
        control_frame.pack(fill=tk.X, pady=10)
        
        btn_style = {
            "bg": self.colors["btn_bg"],
            "fg": self.colors["fg_text"],
            "activebackground": self.colors["btn_active"],
            "activeforeground": "#FFFFFF",
            "relief": tk.FLAT,
            "font": ("Segoe UI", 10)
        }
        
        self.btn_play = tk.Button(control_frame, text="Render & Play", command=self.on_render_play, **btn_style, height=2)
        self.btn_play.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.btn_replay = tk.Button(control_frame, text="Replay", command=self.on_replay, **btn_style, height=2)
        self.btn_replay.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.btn_mp3 = tk.Button(control_frame, text="Save MP3", command=self.on_save_mp3, **btn_style, height=2)
        self.btn_mp3.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Playback Controls
        self.btn_pause = tk.Button(control_frame, text="Pause", command=self.on_pause, **btn_style, height=2)
        self.btn_pause.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.btn_resume = tk.Button(control_frame, text="Resume", command=self.on_resume, **btn_style, height=2)
        self.btn_resume.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.btn_stop = tk.Button(control_frame, text="Stop", command=self.on_stop, **btn_style, height=2)
        self.btn_stop.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Volume Slider
        vol_frame = tk.Frame(control_frame, bg=self.colors["bg_main"])
        vol_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(vol_frame, text="Vol", bg=self.colors["bg_main"], fg=self.colors["fg_dim"]).pack()
        self.vol_slider = tk.Scale(vol_frame, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, 
                                   bg=self.colors["bg_main"], fg=self.colors["fg_dim"], 
                                   troughcolor=self.colors["bg_editor"], activebackground=self.colors["highlight"], 
                                   highlightthickness=0, length=100, command=self.update_volume)
        self.vol_slider.set(0.05)
        self.vol_slider.pack()
        
        # Options Frame
        opt_frame = tk.Frame(control_frame, bg=self.colors["bg_main"])
        opt_frame.pack(side=tk.LEFT, padx=5)
        self.overwrite_var = tk.BooleanVar(value=False)
        self.chk_overwrite = tk.Checkbutton(opt_frame, text="Overwrite", variable=self.overwrite_var,
                                            bg=self.colors["bg_main"], fg=self.colors["fg_dim"],
                                            selectcolor=self.colors["bg_editor"], activebackground=self.colors["bg_main"])
        self.chk_overwrite.pack()

        # Bottom Frame: Status checks
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                              bg=self.colors["bg_editor"], fg=self.colors["fg_dim"],
                              relief=tk.FLAT, anchor="w", padx=10, pady=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_sidebar(self):
        pad = 10
        btn_style = {
            "bg": self.colors["btn_bg"], "fg": self.colors["fg_text"],
            "activebackground": self.colors["btn_active"], "relief": tk.FLAT, "width": 25
        }
        
        # --- Duration Selector ---
        tk.Label(self.sidebar, text="Note Duration", font=("Segoe UI", 10, "bold"), 
                 bg=self.sidebar["bg"], fg=self.colors["fg_dim"]).pack(pady=(pad, 2), anchor="w", padx=pad)
        
        dur_frame = tk.Frame(self.sidebar, bg=self.sidebar["bg"])
        dur_frame.pack(fill=tk.X, padx=pad, pady=(0, 10))
        
        self.duration_var = tk.DoubleVar(value=0.25) # Default 1/4 note
        
        # Unicode music notes: 𝅝 (Whole), 𝅗𝅥 (Half), 𝅘𝅥 (Quarter), 𝅘𝅥𝅮 (Eighth)
        # Note: These require a font that supports them. Segoe UI Symbol usually does on Windows.
        # Format: (Symbol, Value, Label)
        durations = [("𝅝", 1.0, "Whole"), ("𝅗𝅥", 0.5, "Half"), ("𝅘𝅥", 0.25, "Quarter"), ("𝅘𝅥𝅮", 0.125, "Eighth")]
        
        # Helper to set duration
        def set_dur(v):
            self.duration_var.set(v)
            
        # Grid layout for duration buttons
        for i, (sym, val, name) in enumerate(durations):
            # User request: "𝅝 for full note". 
            # We use "Segoe UI Symbol" which definitely has these characters on Windows.
            # Reduced width and size to fit all 4
            b = tk.Radiobutton(dur_frame, text=sym, variable=self.duration_var, value=val, 
                               indicatoron=0, width=4, bg=self.colors["btn_bg"], fg="white", 
                               selectcolor=self.colors["highlight"], activebackground=self.colors["btn_active"],
                               font=("Segoe UI Symbol", 12)) # Specific font for symbols
            b.grid(row=0, column=i, padx=1)
            
        # Row 1: Extra Tools ("..." and "Keys")
        # "..." Button for Extended Notes
        tk.Button(dur_frame, text="...", width=3, bg=self.colors["btn_bg"], fg="white",
                  activebackground=self.colors["btn_active"], relief=tk.FLAT,
                  command=self.toggle_extended_bar).grid(row=1, column=0, columnspan=2, sticky="ew", padx=1, pady=(2, 0))

        # "Keys" Button
        tk.Button(dur_frame, text="Keys", width=5, bg=self.colors["btn_bg"], fg="white",
                  activebackground=self.colors["btn_active"], relief=tk.FLAT,
                  command=self.toggle_keys_menu).grid(row=1, column=2, columnspan=2, sticky="ew", padx=1, pady=(2, 0))

        tk.Frame(self.sidebar, height=1, bg=self.colors["fg_dim"]).pack(fill=tk.X, pady=5, padx=pad)

        # --- Quick Tools (Cycleable) ---
        self.tool_frame = tk.Frame(self.sidebar, bg=self.sidebar["bg"])
        self.tool_frame.pack(fill=tk.X)
        
        self.current_toolbar_index = 0
        self.toolbars = [
            {"name": "Basic", "render": self._render_basic_toolbar},
            {"name": "Chords", "render": self._render_chord_toolbar}
        ]
        
        self._render_current_toolbar()

        # Generator Section
        tk.Label(self.sidebar, text="Generators", font=("Segoe UI", 12, "bold"), 
                 bg=self.sidebar["bg"], fg=self.colors["fg_text"]).pack(pady=(pad, 5), anchor="w", padx=pad)
                 
        # Generator Selector Dropdown
        self.gen_var = tk.StringVar(value="Time Warp")
        gen_options = ["Time Warp", "Echo", "Cusp Crescendo"] # Extensible list
        
        gen_menu = tk.OptionMenu(self.sidebar, self.gen_var, *gen_options, command=self._on_gen_change)
        gen_menu.config(bg=self.colors["btn_bg"], fg="white", highlightthickness=0, relief=tk.FLAT, width=20)
        gen_menu["menu"].config(bg=self.colors["bg_editor"], fg="white")
        gen_menu.pack(padx=pad, anchor="w")
        
        self.gen_frame = tk.Frame(self.sidebar, bg=self.sidebar["bg"])
        self.gen_frame.pack(fill=tk.X, padx=pad, pady=5)
        
        self.gen_entries = {}
        self._on_gen_change("Time Warp") # Render initial form

    def _create_extended_bar(self):
        # Hidden top bar (reused for Micro-Timing and Keys)
        self.top_bar_frame = tk.Frame(self.root, bg=self.colors["bg_sidebar"], height=40)
        self.top_bar_mode = None # "micro", "keys", or None
        
        # We don't pack it yet.
        
    def _clear_top_bar(self):
        for widget in self.top_bar_frame.winfo_children():
            widget.destroy()
            
    def toggle_extended_bar(self):
        self.set_top_bar_mode("micro")

    def toggle_keys_menu(self):
        self.set_top_bar_mode("keys")
        
    def set_top_bar_mode(self, mode):
        # If clicking same mode, toggle off
        if self.top_bar_mode == mode and self.top_bar_frame.winfo_ismapped():
            self.top_bar_frame.pack_forget()
            self.top_bar_mode = None
            return
            
        self.top_bar_mode = mode
        self._clear_top_bar()
        self.top_bar_frame.pack(side=tk.TOP, fill=tk.X, before=self.main_container)
        
        if mode == "micro":
            self._render_micro_timing_bar()
        elif mode == "keys":
            self._render_keys_bar()
            
    def _render_micro_timing_bar(self):
        lbl = tk.Label(self.top_bar_frame, text="Micro-Timing:", fg=self.colors["fg_dim"], bg=self.colors["bg_sidebar"], font=("Segoe UI", 10))
        lbl.pack(side=tk.LEFT, padx=10, pady=5)
        
        micros = [("𝅘𝅥𝅯 (1/16)", 0.0625), ("𝅘𝅥𝅰 (1/32)", 0.03125), ("𝅘𝅥𝅱 (1/64)", 0.015625)]
        for text, val in micros:
             tk.Radiobutton(self.top_bar_frame, text=text, variable=self.duration_var, value=val, 
                               indicatoron=0, width=10, bg=self.colors["btn_bg"], fg="white", 
                               selectcolor=self.colors["highlight"], activebackground=self.colors["btn_active"],
                               font=("Segoe UI Symbol", 10)).pack(side=tk.LEFT, padx=2, pady=5)
                               
        tk.Button(self.top_bar_frame, text="×", command=lambda: self.set_top_bar_mode(self.top_bar_mode), # Wraps to toggle off
                  bg=self.colors["btn_bg"], fg="white", relief=tk.FLAT).pack(side=tk.RIGHT, padx=5, pady=5)

    def _render_keys_bar(self):
        # Default Key if not set
        if not hasattr(self, "current_key"):
            self.current_key = "C"

        # Key Selector
        lbl = tk.Label(self.top_bar_frame, text="Key:", fg=self.colors["fg_dim"], bg=self.colors["bg_sidebar"], font=("Segoe UI", 10))
        lbl.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        
        keys = ["C", "G", "D", "A", "E", "F", "Bb", "Eb"]
        # Use helper to refresh bar when key changes
        def set_key(k):
            self.current_key = k
            self._clear_top_bar()
            self._render_keys_bar()
            
        for k in keys:
            color = self.colors["highlight"] if k == self.current_key else self.colors["btn_bg"]
            tk.Button(self.top_bar_frame, text=k, command=lambda k=k: set_key(k),
                      bg=color, fg="white", relief=tk.FLAT, width=3).pack(side=tk.LEFT, padx=1, pady=5)
                      
        # Spacer
        tk.Frame(self.top_bar_frame, width=20, bg=self.colors["bg_sidebar"]).pack(side=tk.LEFT)
        
        # Chord Buttons (Diatonic)
        # I=Maj, ii=min, iii=min, IV=Maj, V=Maj, vi=min, vii=dim
        degrees = [("I", "maj"), ("ii", "min"), ("iii", "min"), ("IV", "maj"), ("V", "maj"), ("vi", "min"), ("vii°", "dim")]
        
        for deg_label, quality in degrees:
             tk.Button(self.top_bar_frame, text=deg_label, 
                       command=lambda d=deg_label, q=quality: self._insert_diatonic_chord(d, q),
                       bg=self.colors["btn_bg"], fg="white", relief=tk.FLAT, width=4).pack(side=tk.LEFT, padx=1, pady=5)
                       
        tk.Button(self.top_bar_frame, text="×", command=lambda: self.set_top_bar_mode(self.top_bar_mode),
                  bg=self.colors["btn_bg"], fg="white", relief=tk.FLAT).pack(side=tk.RIGHT, padx=5, pady=5)

    def _insert_diatonic_chord(self, degree_label, quality):
        # Calculate root note based on Key + Degree
        intervals = {"I": 0, "ii": 2, "iii": 4, "IV": 5, "V": 7, "vi": 9, "vii°": 11}
        interval = intervals.get(degree_label, 0)
        
        semitone_map = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 
                        'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
        
        key_semi = semitone_map.get(self.current_key, 0)
        root_semi = (key_semi + interval) % 12
        
        reverse_map = {0: 'C', 1: 'Cs', 2: 'D', 3: 'Ds', 4: 'E', 5: 'F', 6: 'Fs', 7: 'G', 8: 'Gs', 9: 'A', 10: 'As', 11: 'B'}
        
        note_name = reverse_map.get(root_semi, 'C')
        note_str = f"{note_name}4"
        
        d = self.duration_var.get()
        code = f"chord('{note_str}', '{quality}', duration={d})"
        self.insert_code(code)


    def cycle_toolbar(self):
        self.current_toolbar_index = (self.current_toolbar_index + 1) % len(self.toolbars)
        self._render_current_toolbar()

    def _render_current_toolbar(self):
        # Clear existing
        for widget in self.tool_frame.winfo_children():
            widget.destroy()
            
        toolbar = self.toolbars[self.current_toolbar_index]
        name = toolbar["name"]
        render_func = toolbar["render"]
        
        pad = 10
        btn_style = {
            "bg": self.colors["btn_bg"], "fg": self.colors["fg_text"],
            "activebackground": self.colors["btn_active"], "relief": tk.FLAT, "width": 25
        }
        
        # Header Row with Cycle Button
        header_frame = tk.Frame(self.tool_frame, bg=self.sidebar["bg"])
        header_frame.pack(fill=tk.X, padx=pad, pady=(pad, 5))
        
        tk.Label(header_frame, text=f"Tools ({name})", font=("Segoe UI", 12, "bold"), 
                 bg=self.sidebar["bg"], fg=self.colors["fg_text"]).pack(side=tk.LEFT)
        
        # specific style for cycle button
        cycle_style = btn_style.copy()
        cycle_style["width"] = 3
        tk.Button(header_frame, text="↻", **cycle_style, 
                  command=self.cycle_toolbar).pack(side=tk.RIGHT)
                  
        render_func(pad, btn_style)

    def _render_basic_toolbar(self, pad, btn_style):
        # Helper to get current duration
        def insert_note(wave):
            d = self.duration_var.get()
            self.insert_code(f"beep(waveform='{wave}', duration={d})")
            
        def insert_silence():
            d = self.duration_var.get()
            self.insert_code(f"silence(duration={d})")
        
        tk.Button(self.tool_frame, text="Insert Beep (Sine)", **btn_style, 
                  command=lambda: insert_note("sine")).pack(pady=2, padx=pad)
        tk.Button(self.tool_frame, text="Insert Beep (Saw)", **btn_style, 
                  command=lambda: insert_note("sawtooth")).pack(pady=2, padx=pad)
        tk.Button(self.tool_frame, text="Insert Beep (Square)", **btn_style, 
                  command=lambda: insert_note("square")).pack(pady=2, padx=pad)
        tk.Button(self.tool_frame, text="Insert Silence (Gap)", **btn_style, 
                  command=insert_silence).pack(pady=2, padx=pad)

    def _render_chord_toolbar(self, pad, btn_style):
        def insert_chord(semitones):
            d = self.duration_var.get()
            # Gen chord code: (beep(440) + beep(440*semi))
            # Just handy snippets
            code = f"(beep(440, duration={d}) + beep(440 * 2**({semitones}/12), duration={d}))"
            self.insert_code(code)
            
        tk.Button(self.tool_frame, text="Major 3rd (Dyad)", **btn_style, 
                  command=lambda: insert_chord(4)).pack(pady=2, padx=pad)
        tk.Button(self.tool_frame, text="Minor 3rd (Dyad)", **btn_style, 
                  command=lambda: insert_chord(3)).pack(pady=2, padx=pad)
        tk.Button(self.tool_frame, text="Perfect 5th (Power)", **btn_style, 
                  command=lambda: insert_chord(7)).pack(pady=2, padx=pad)
        tk.Button(self.tool_frame, text="Octave", **btn_style, 
                  command=lambda: insert_chord(12)).pack(pady=2, padx=pad)
                  

    def _on_gen_change(self, selected_gen):
        # Clear existing
        for widget in self.gen_frame.winfo_children():
            widget.destroy()
        self.gen_entries = {}
        
        if selected_gen == "Time Warp":
            self._render_time_warp_form()
        elif selected_gen == "Echo":
            self._render_echo_form()
        elif selected_gen == "Cusp Crescendo":
            self._render_cusp_form()

    def _render_time_warp_form(self):
        pad = 5 # Local padding
        tk.Label(self.gen_frame, text="elastic_beeps()", font=("Consolas", 9), 
                  bg=self.sidebar["bg"], fg=self.colors["fg_dim"]).pack(pady=(5, 5), anchor="w")
        self._render_generic_form([
            ("Start Density", 1), ("Peak Density", 8), ("End Density", 1), 
            ("Bars", 8), ("Freq (Hz)", 440)
        ])

    def _render_echo_form(self):
        pad = 5
        tk.Label(self.gen_frame, text="echo_pattern()", font=("Consolas", 9), 
                  bg=self.sidebar["bg"], fg=self.colors["fg_dim"]).pack(pady=(5, 5), anchor="w")
        self._render_generic_form([
            ("Freq (Hz)", 440), ("Repeats", 8), ("Decay (0-1)", 0.6), ("Interval", 0.25)
        ])

    def _render_generic_form(self, fields):
        # Helper to render labeled entries
        for label, default in fields:
            f = tk.Frame(self.gen_frame, bg=self.sidebar["bg"])
            f.pack(fill=tk.X, pady=2)
            tk.Label(f, text=label, width=12, anchor="w", bg=self.sidebar["bg"], fg=self.colors["fg_dim"]).pack(side=tk.LEFT)
            e = tk.Entry(f, bg=self.colors["bg_main"], fg="white", insertbackground="white", relief=tk.FLAT)
            e.insert(0, str(default))
            e.pack(side=tk.RIGHT, expand=True, fill=tk.X)
            self.gen_entries[label] = e
            
        # Waveform selector
        f = tk.Frame(self.gen_frame, bg=self.sidebar["bg"])
        f.pack(fill=tk.X, pady=2)
        tk.Label(f, text="Waveform", width=12, anchor="w", bg=self.sidebar["bg"], fg=self.colors["fg_dim"]).pack(side=tk.LEFT)
        self.gen_wave_var = tk.StringVar(value="sine")
        om = tk.OptionMenu(f, self.gen_wave_var, "sine", "sawtooth", "square", "triangle")
        om.config(bg=self.colors["btn_bg"], fg="white", highlightthickness=0, relief=tk.FLAT)
        om["menu"].config(bg=self.colors["bg_editor"], fg="white")
        om.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        btn_style = {
            "bg": self.colors["btn_bg"], "fg": self.colors["fg_text"],
            "activebackground": self.colors["btn_active"], "relief": tk.FLAT, "width": 25
        }
        tk.Button(self.gen_frame, text="Insert Code", **btn_style, 
                  command=self.insert_generator).pack(pady=15)

    def insert_code(self, text):
        self.text_editor.insert(tk.INSERT, text)

    def insert_generator(self):
        gen_type = self.gen_var.get()
        if gen_type == "Time Warp":
            self._insert_time_warp()
        elif gen_type == "Echo":
            self._insert_echo()
        elif gen_type == "Cusp Crescendo":
            self._insert_cusp()
            
    def _insert_time_warp(self):
        try:
            val = self._parse_entries(["Start Density", "Peak Density", "End Density", "Bars", "Freq (Hz)"])
            wave = self.gen_wave_var.get()
            code = f"elastic_beeps(start_density={val['Start Density']}, peak_density={val['Peak Density']}, end_density={val['End Density']}, bars={val['Bars']}, note_freq={val['Freq (Hz)']}, waveform='{wave}')"
            self.insert_code(code)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _insert_echo(self):
        try:
            val = self._parse_entries(["Freq (Hz)", "Repeats", "Decay (0-1)", "Interval"])
            wave = self.gen_wave_var.get()
            code = f"echo_pattern(freq={val['Freq (Hz)']}, repeats={int(val['Repeats'])}, decay={val['Decay (0-1)']}, interval={val['Interval']}, waveform='{wave}')"
            self.insert_code(code)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def _render_cusp_form(self):
        pad = 5
        tk.Label(self.gen_frame, text="cusp_crescendo()", font=("Consolas", 9), 
                  bg=self.sidebar["bg"], fg=self.colors["fg_dim"]).pack(pady=(5, 5), anchor="w")
        self._render_generic_form([
            ("Freq (Hz)", 440), ("Duration", 4), ("N Events", 32), ("Power", 4)
        ])

    def _insert_cusp(self):
        try:
            val = self._parse_entries(["Freq (Hz)", "Duration", "N Events", "Power"])
            wave = self.gen_wave_var.get()
            code = f"cusp_crescendo(freq={val['Freq (Hz)']}, duration={val['Duration']}, n_events={int(val['N Events'])}, power={val['Power']}, waveform='{wave}')"
            self.insert_code(code)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def _parse_entries(self, labels):
        parsed = {}
        for label in labels:
            raw = self.gen_entries[label].get()
            try:
                parsed[label] = float(raw)
            except ValueError:
                raise ValueError(f"Invalid value for '{label}': \"{raw}\"")
        return parsed

    def update_volume(self, val):
        v = float(val)
        try:
            pygame.mixer.music.set_volume(v)
        except Exception:
            pass
            
    def get_user_pattern(self):
        code = self.text_editor.get("1.0", tk.END).strip()
        if not code:
            return None
        
        # Safe-ish eval context
        context = {
            "Pattern": Pattern,
            "Renderer": Renderer,
            "beep": beep,
            "silence": silence,
            "elastic_beeps": elastic_beeps,
            "echo_pattern": echo_pattern,
            "cusp_crescendo": cusp_crescendo,
            "reverse": reverse,
            "chord": chord,
            "note_to_freq": note_to_freq,
            "crossfade": crossfade
        }
        
        try:
            # AST parsing to separate statements from the final expression
            tree = ast.parse(code)
            
            if not tree.body:
                return None
                
            # Check if last node is an expression (the return value)
            if isinstance(tree.body[-1], ast.Expr):
                expr_node = tree.body[-1]
                body_nodes = tree.body[:-1]
                
                # 1. Execute the body (assignments, imports, etc.)
                if body_nodes:
                    module = ast.Module(body=body_nodes, type_ignores=[])
                    exec(compile(module, filename="<string>", mode="exec"), context)
                
                # 2. Evaluate the final expression using the context populated by exec
                expr = ast.Expression(body=expr_node.value)
                result = eval(compile(expr, filename="<string>", mode="eval"), context)
                
                if isinstance(result, Pattern):
                    return result
                else:
                    raise ValueError("Last line must be an expression returning a Pattern object.")
            else:
                # If script ends with assignment or other statement
                # Try executing all and see if a variable '_result' or 'out' is defined? 
                # For now, strict mode: must end in expression.
                # Or we could just exec it all and expect nothing? But we need a Pattern to render.
                raise ValueError("Script must end with a Pattern expression (e.g. 'beep(440)' or variable name).")
                
        except Exception as e:
            messagebox.showerror("Syntax Error", f"Error parsing pattern:\n{e}")
            return None

    def on_render_play(self):
        pattern = self.get_user_pattern()
        if not pattern:
            return
            
        self.status_var.set("Rendering...")
        self.root.update()
        
        # We handle volume via pygame mixer set_volume now for preview.
        # But we still render at full volume (with soft clip) effectively, 
        # allowing mixer to attenuate. 
        # Actually: Renderer soft clip tanh happens. If we render at 1.0, tanh limits at 1.0.
        # Slider controls playback gain.
        
        overwrite = self.overwrite_var.get()
        current_vol = self.vol_slider.get() # Get current value to set initial playback vol
        
        def _task():
            try:
                if overwrite:
                    temp_file = "temp_preview.wav"
                else:
                    import time
                    temp_file = f"preview_{int(time.time())}.wav"
                    
                # Render at full volume (1.0) so we have dynamic range. 
                # Tanh limits it nicely.
                self.renderer.render(pattern, temp_file, master_volume=1.0)
                self.last_rendered_file = temp_file
                
                # Play
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                    
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.set_volume(current_vol) # Set initial volume
                pygame.mixer.music.play()
                
                self.status_var.set(f"Playing {temp_file}...")
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                messagebox.showerror("Render Error", str(e))
                
        threading.Thread(target=_task).start()

    def on_replay(self):
        if not self.last_rendered_file or not os.path.exists(self.last_rendered_file):
            messagebox.showwarning("Replay", "No preview available to replay.")
            return

        current_vol = self.vol_slider.get()
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.load(self.last_rendered_file)
            pygame.mixer.music.set_volume(current_vol)
            pygame.mixer.music.play()
            self.status_var.set(f"Replaying {self.last_rendered_file}...")
        except Exception as e:
             messagebox.showerror("Replay Error", str(e))

    def on_save_mp3(self):
        pattern = self.get_user_pattern()
        if not pattern:
            return
            
        filename = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 Files", "*.mp3")])
        if not filename:
            return
            
        self.status_var.set(f"Saving to {filename}...")
        self.root.update()

        vol = self.vol_slider.get()

        def _task():
            try:
                # Export at full volume (1.0), ignoring the preview slider
                self.renderer.render(pattern, filename, master_volume=1.0)
                self.status_var.set(f"Saved to {filename}")
                messagebox.showinfo("Success", f"Saved to {filename}")
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                messagebox.showerror("Export Error", str(e))
        
        threading.Thread(target=_task).start()

    def on_pause(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.status_var.set("Paused")

    def on_resume(self):
        try:
            pygame.mixer.music.unpause()
            self.status_var.set("Resumed")
        except:
            pass

    def on_stop(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            self.status_var.set("Stopped")

def run_gui(ffmpeg_path="ffmpeg"):
    root = tk.Tk()
    app = AudioApp(root, ffmpeg_path)
    root.mainloop()
