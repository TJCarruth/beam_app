"""Tkinter controls and live result presentation."""

import tkinter as tk
from tkinter import ttk

from .analysis import analyze
from .models import BeamInput, Load
from .plots import BeamPlots
from .sections import SECTIONS, material_properties, section_by_name


class BeamDesignerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Beam Designer · Structural analysis")
        self.root.geometry("1360x900")
        self.root.minsize(980, 680)
        self.beam = BeamInput(20, "simple", "steel", "W12x26", 360, [Load("uniform", 1, start=0, end=20)])
        self.dark = False
        self.vars = {}
        self._style()
        self._layout()
        self.refresh()

    def run(self):
        self.root.mainloop()

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", background="#ffffff", foreground="#172235", font=("Segoe UI", 9))
        style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"))
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", padding=7)

    def _layout(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Beam Designer", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="Toggle dark mode", command=self.toggle_dark).pack(side="right")
        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self.left = ttk.Frame(body, style="Card.TFrame", padding=14, width=320)
        self.left.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        self.left.grid_propagate(False)
        self.right = ttk.Frame(body, style="Card.TFrame", padding=10)
        self.right.grid(row=0, column=1, sticky="nsew")
        self.right.rowconfigure(0, weight=1)
        self.right.columnconfigure(0, weight=1)
        self._controls()
        self.plot = BeamPlots(self.right, self._drag_point)
        self.plot.widget.grid(row=0, column=0, sticky="nsew")

    def _controls(self):
        f = self.left
        ttk.Label(f, text="Beam setup", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self.support_var = tk.StringVar(value="simple")
        ttk.Label(f, text="Support type").pack(anchor="w")
        support = ttk.Frame(f); support.pack(fill="x", pady=3)
        ttk.Radiobutton(support, text="Simply supported", value="simple", variable=self.support_var, command=self._control_change).pack(side="left")
        ttk.Radiobutton(support, text="Cantilever", value="cantilever", variable=self.support_var, command=self._control_change).pack(side="left")
        self.span_var = tk.DoubleVar(value=20)
        self._field(f, "Span (ft)", ttk.Scale(f, from_=4, to=40, variable=self.span_var, command=self._span_scale))
        span_entry = ttk.Entry(f, textvariable=self.span_var, width=8); span_entry.pack(anchor="e"); span_entry.bind("<Return>", self._control_change); span_entry.bind("<FocusOut>", self._control_change)
        self.limit_var = tk.StringVar(value="360")
        self._field(f, "Deflection limit", ttk.Combobox(f, textvariable=self.limit_var, values=("240", "360"), state="readonly"))
        f.winfo_children()[-1].bind("<<ComboboxSelected>>", self._control_change)
        ttk.Separator(f).pack(fill="x", pady=9)
        ttk.Label(f, text="Loads", style="Section.TLabel").pack(anchor="w")
        self.loads_frame = ttk.Frame(f); self.loads_frame.pack(fill="x")
        buttons = ttk.Frame(f); buttons.pack(fill="x", pady=4)
        ttk.Button(buttons, text="＋ Point load", command=self.add_point).pack(fill="x", pady=2)
        ttk.Button(buttons, text="＋ Uniform load", command=self.add_uniform).pack(fill="x", pady=2)
        ttk.Separator(f).pack(fill="x", pady=9)
        ttk.Label(f, text="Material & section", style="Section.TLabel").pack(anchor="w")
        self.material_var = tk.StringVar(value="steel")
        material = ttk.Combobox(f, textvariable=self.material_var, values=("steel", "wood"), state="readonly")
        self._field(f, "Material", material); material.bind("<<ComboboxSelected>>", self._material_change)
        self.section_var = tk.StringVar(value="W12x26")
        section = ttk.Combobox(f, textvariable=self.section_var, state="readonly")
        self._field(f, "Section", section); section.bind("<<ComboboxSelected>>", self._control_change)
        self.section_meta = ttk.Label(f, text="", foreground="#64748b", wraplength=285)
        self.section_meta.pack(anchor="w", pady=3)
        self.cards = ttk.Frame(self.right); self.cards.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.check_labels = {}
        for key, title in (("bend", "Bending"), ("deflect", "Deflection")):
            card = ttk.Frame(self.cards, style="Card.TFrame", padding=10); card.pack(side="left", fill="both", expand=True, padx=4)
            ttk.Label(card, text=title, style="Section.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="—", font=("Segoe UI", 15, "bold")); value.pack(anchor="w")
            allow = ttk.Label(card, text="Allowable —"); allow.pack(anchor="w")
            status = ttk.Label(card, text="PASS"); status.pack(anchor="e")
            self.check_labels[key] = (value, allow, status)
        self.recommend = ttk.Label(self.right, text="", padding=8, wraplength=700)
        self.recommend.grid(row=2, column=0, sticky="ew")
        self.use_button = ttk.Button(self.right, text="Use recommended section", command=self.use_recommended)
        self.use_button.grid(row=3, column=0, sticky="e")

    def _field(self, parent, label, widget):
        ttk.Label(parent, text=label).pack(anchor="w", pady=(5, 1))
        widget.pack(fill="x")

    def _span_scale(self, value):
        self.span_var.set(round(float(value) * 4) / 4)
        self._control_change()

    def _control_change(self, *_):
        try:
            self.beam.span = min(40, max(4, float(self.span_var.get())))
        except (ValueError, tk.TclError):
            self.beam.span = 20
        self.span_var.set(self.beam.span)
        self.beam.support = self.support_var.get()
        self.beam.limit = int(self.limit_var.get())
        self.beam.section_name = self.section_var.get()
        self.refresh()

    def _material_change(self, *_):
        self.beam.material = self.material_var.get()
        self.section_var.set(SECTIONS[self.beam.material][0].name)
        self._control_change()

    def _load_changed(self, index, key, value):
        load = self.beam.loads[index]
        try: number = max(0.0, float(value))
        except (ValueError, tk.TclError): return
        setattr(load, key, number)
        if key in ("position", "start", "end"): setattr(load, key, min(self.beam.span, number))
        if load.kind == "uniform" and load.end < load.start: load.start, load.end = load.end, load.start
        self.refresh()

    def _render_loads(self):
        for child in self.loads_frame.winfo_children(): child.destroy()
        for i, load in enumerate(self.beam.loads):
            row = ttk.LabelFrame(self.loads_frame, text=f"{load.kind.title()} load", padding=5); row.pack(fill="x", pady=3)
            ttk.Button(row, text="×", width=3, command=lambda n=i: self.remove_load(n)).grid(row=0, column=2)
            values = [("Magnitude", "magnitude", "k" if load.kind == "point" else "k/ft")]
            values += [("Position", "position", "ft")] if load.kind == "point" else [("Start", "start", "ft"), ("End", "end", "ft")]
            for j, (label, key, unit) in enumerate(values):
                ttk.Label(row, text=f"{label} ({unit})").grid(row=j+1, column=0, sticky="w")
                var = tk.StringVar(value=f"{getattr(load,key):g}")
                entry = ttk.Entry(row, textvariable=var, width=10); entry.grid(row=j+1, column=1, sticky="ew")
                entry.bind("<Return>", lambda e, n=i, k=key, v=var: self._load_changed(n,k,v.get()))
                entry.bind("<FocusOut>", lambda e, n=i, k=key, v=var: self._load_changed(n,k,v.get()))
            row.columnconfigure(1, weight=1)

    def add_point(self):
        self.beam.loads.append(Load("point", 5, position=self.beam.span if self.beam.support == "cantilever" else self.beam.span/2)); self.refresh()

    def add_uniform(self):
        self.beam.loads.append(Load("uniform", .5, start=0, end=self.beam.span)); self.refresh()

    def remove_load(self, index):
        del self.beam.loads[index]; self.refresh()

    def _drag_point(self, index, x):
        self.beam.loads[index].position = x; self.refresh()

    def refresh(self):
        self.beam.span = min(40, max(4, self.beam.span))
        self.beam.loads = [Load(l.kind, l.magnitude, l.position, l.start, min(l.end, self.beam.span)) for l in self.beam.loads]
        self.section_var.set(self.beam.section_name)
        self._render_loads()
        section = section_by_name(self.beam.material, self.beam.section_name)
        e, fb = material_properties(self.beam.material)
        self.section_meta.configure(text=f"E {e:g} ksi · Fb {fb:g} ksi · Ix {section.ix:g} in⁴ · Sx {section.sx:g} in³" + (f" · {section.weight:g} lb/ft" if section.weight else ""))
        result = analyze(self.beam)
        self.plot.draw(self.beam, result, self.dark)
        ratios = (result.bending_stress/result.bending_allowable, abs(result.max_deflection)/result.deflection_allowable)
        actuals = ((result.bending_stress, result.bending_allowable, "ksi"), (abs(result.max_deflection), result.deflection_allowable, "in"))
        for key, ratio, (actual, allowable, unit) in zip(("bend", "deflect"), ratios, actuals):
            value, allow, status = self.check_labels[key]
            value.configure(text=f"{actual:.3f} {unit}")
            allow.configure(text=f"Allowable {allowable:.3f} {unit}")
            status.configure(text="PASS" if ratio <= 1 else "FAIL", foreground="#159447" if ratio <= 1 else "#d34b4b")
        if result.recommended_section:
            self.recommend.configure(text=f"Lightest passing section: {result.recommended_section.name} · meets bending and deflection limits.")
            self.use_button.state(["!disabled"])
        else:
            self.recommend.configure(text="No listed section passes both checks.")
            self.use_button.state(["disabled"])
        self.result = result

    def use_recommended(self):
        if self.result.recommended_section:
            self.beam.section_name = self.result.recommended_section.name; self.section_var.set(self.beam.section_name); self.refresh()

    def toggle_dark(self):
        self.dark = not self.dark
        self.root.configure(bg="#172235" if self.dark else "#f5f7fb")
        self.refresh()
