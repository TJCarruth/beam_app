"""Matplotlib beam sketch and synchronized analysis diagrams."""

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .models import AnalysisResult, BeamInput


class BeamPlots:
    def __init__(self, parent, on_drag):
        self.figure = Figure(figsize=(8.4, 7.2), dpi=90, facecolor="#f5f7fb")
        grid = self.figure.add_gridspec(4, 1, height_ratios=[1.0, 1, 1, 1], hspace=.42)
        self.axes = [self.figure.add_subplot(grid[i]) for i in range(4)]
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.widget = self.canvas.get_tk_widget()
        self.on_drag = on_drag
        self.beam = None
        self.result = None
        self.drag_load = None
        self.cursor = [ax.axvline(0, color="#64748b", lw=.8, alpha=.7, visible=False) for ax in self.axes[1:]]
        self.canvas.mpl_connect("motion_notify_event", self._motion)
        self.canvas.mpl_connect("button_press_event", self._press)
        self.canvas.mpl_connect("button_release_event", self._release)

    def draw(self, beam: BeamInput, result: AnalysisResult, dark=False):
        self.beam, self.result = beam, result
        bg = "#172235" if dark else "#eaf3ff"
        fg = "#e7edf7" if dark else "#172235"
        grid = "#36445b" if dark else "#cbdcf2"
        colors = ["#2867e8", "#0e9f9a", "#8b5bd6"]
        uniform_colors = ["#0e9f9a", "#e07a2d", "#7b61c9", "#d14b64", "#2692a5", "#8a9b32", "#cf5da8", "#526fbd"]
        uniform_index = 0
        for ax in self.axes:
            ax.clear()
            ax.set_facecolor(bg)
            ax.tick_params(colors=fg, labelsize=8)
            ax.spines[:].set_color(grid)
        beam_ax = self.axes[0]
        beam_ax.set_xlim(-beam.span * .04, beam.span * 1.04)
        beam_ax.set_ylim(-.8, 1.4)
        beam_ax.axis("off")
        beam_ax.plot([0, beam.span], [0, 0], color="#25344c", lw=5, solid_capstyle="round")
        if beam.support == "simple":
            beam_ax.scatter([0, beam.span], [-.18, -.18], marker="^", s=180, color="#9bb4d6")
            beam_ax.plot([-0.4, .4], [-.34, -.34], color="#71819c")
            beam_ax.plot([beam.span-.4, beam.span+.4], [-.34, -.34], color="#71819c")
        else:
            beam_ax.plot([0, 0], [-.35, .45], lw=5, color="#71819c")
        for load in beam.loads:
            if load.kind == "point":
                beam_ax.annotate("", (load.position, .12), (load.position, .82), arrowprops={"arrowstyle": "-|>", "color": "#2867e8", "lw": 1.8})
                beam_ax.text(load.position, .9, f"{load.magnitude:g} k", ha="center", color=fg, fontsize=8)
            else:
                load_color = uniform_colors[uniform_index % len(uniform_colors)]
                uniform_index += 1
                beam_ax.plot([load.start, load.end], [.72, .72], color=load_color, lw=1.5)
                for xp in np.linspace(load.start, load.end, max(2, int((load.end-load.start)*2)+1)):
                    beam_ax.annotate("", (xp, .12), (xp, .7), arrowprops={"arrowstyle": "-|>", "color": load_color, "lw": 1})
                beam_ax.text((load.start+load.end)/2, .82, f"{load.magnitude:g} k/ft", ha="center", color=load_color, fontsize=8)
        beam_ax.text(0, -.62, f"Rₗ {result.reaction_left:.2f} k", ha="left", color=fg, fontsize=8)
        if beam.support == "simple":
            beam_ax.text(beam.span, -.62, f"Rᵣ {result.reaction_right:.2f} k", ha="right", color=fg, fontsize=8)
        else:
            beam_ax.text(0, -.78, f"Mfixed {result.reaction_moment:.2f} kip-ft", ha="left", color=fg, fontsize=8)
        beam_ax.text(beam.span, -.62 if beam.support == "cantilever" else -.8, f"{beam.span:g} ft", ha="right", color=fg, fontsize=8)

        series = [(result.shear, "Shear", "kips"), (result.moment, "Moment", "kip-ft"), (result.deflection, "Deflection", "in")]
        for ax, (values, title, unit), color in zip(self.axes[1:], series, colors):
            ax.fill_between(result.x, values, 0, color=color, alpha=.17)
            ax.plot(result.x, values, color=color, lw=2)
            ax.axhline(0, color=grid, lw=.8)
            i = int(np.argmax(np.abs(values)))
            ax.scatter([result.x[i]], [values[i]], color=color, s=18, zorder=3)
            ax.annotate(f"{values[i]:.3g} {unit}", (result.x[i], values[i]), xytext=(5, 7), textcoords="offset points", color=color, fontsize=8)
            ax.set_ylabel(f"{title} ({unit})", color=fg, fontsize=8)
            ax.set_xlim(0, beam.span)
            ax.grid(axis="x", color=grid, alpha=.5)
            ax.set_xticks(np.linspace(0, beam.span, 5))
            ax.set_xlabel("Span (ft)", color=fg, fontsize=8)
        self.canvas.draw_idle()

    def _motion(self, event):
        if event.inaxes not in self.axes[1:] or event.xdata is None or self.result is None:
            return
        x = float(np.clip(event.xdata, 0, self.beam.span))
        for line in self.cursor:
            line.set_xdata([x, x]); line.set_visible(True)
        self.canvas.draw_idle()

    def _press(self, event):
        if event.inaxes != self.axes[0] or event.xdata is None or not self.beam:
            return
        candidates = [(abs(load.position-event.xdata), i) for i, load in enumerate(self.beam.loads) if load.kind == "point"]
        if candidates and min(candidates)[0] < self.beam.span * .04:
            self.drag_load = min(candidates)[1]

    def _release(self, event):
        if self.drag_load is not None and event.xdata is not None:
            self.on_drag(self.drag_load, max(0, min(self.beam.span, round(event.xdata * 4) / 4)))
        self.drag_load = None
