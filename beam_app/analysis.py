"""Statically determinate beam calculations, independent of the UI."""

import math

import numpy as np

from .models import AnalysisResult, BeamInput, Load, Section
from .sections import SECTIONS, material_properties, section_by_name


def normalize_loads(loads: list[Load], span: float) -> list[Load]:
    """Clamp nonnegative loads to the beam; zero-length uniform loads vanish."""
    out: list[Load] = []
    for load in loads:
        magnitude = max(0.0, float(load.magnitude))
        if load.kind == "point":
            out.append(Load("point", magnitude, position=min(span, max(0.0, load.position))))
        else:
            a = min(span, max(0.0, load.start))
            b = min(span, max(0.0, load.end))
            if b > a:
                out.append(Load("uniform", magnitude, start=a, end=b))
    return out


def _load_action(loads: list[Load]) -> tuple[float, float]:
    total = first_moment = 0.0
    for load in loads:
        if load.kind == "point":
            total += load.magnitude
            first_moment += load.magnitude * load.position
        else:
            force = load.magnitude * (load.end - load.start)
            total += force
            first_moment += force * (load.start + load.end) / 2
    return total, first_moment


def _internal_forces(x: np.ndarray, beam: BeamInput, loads: list[Load], left: float) -> tuple[np.ndarray, np.ndarray]:
    shear = np.full_like(x, left, dtype=float)
    moment = left * x
    if beam.support == "cantilever":
        shear.fill(0.0)
        moment = np.zeros_like(x)
        for load in loads:
            if load.kind == "point":
                remaining = x <= load.position
                shear[remaining] -= load.magnitude
                moment[remaining] -= load.magnitude * (load.position - x[remaining])
            else:
                a = np.maximum(x, load.start)
                b = load.end
                length = np.maximum(0.0, b - a)
                shear -= load.magnitude * length
                moment -= load.magnitude * length * ((a + b) / 2 - x)
        return shear, moment

    for load in loads:
        if load.kind == "point":
            active = x >= load.position
            shear[active] -= load.magnitude
            moment[active] -= load.magnitude * (x[active] - load.position)
        else:
            loaded_end = np.minimum(x, load.end)
            length = np.maximum(0.0, loaded_end - load.start)
            shear -= load.magnitude * length
            moment -= load.magnitude * length * (x - (load.start + loaded_end) / 2)
    return shear, moment


def analyze(beam: BeamInput) -> AnalysisResult:
    """Analyze a single-span beam. Downward loads are positive input values."""
    span = min(40.0, max(4.0, float(beam.span)))
    beam.span = span
    loads = normalize_loads(beam.loads, span)
    beam.loads = loads
    total, first_moment = _load_action(loads)
    if beam.support == "simple":
        right = first_moment / span
        left = total - right
        fixed_moment = 0.0
    else:
        right = 0.0
        left = total
        fixed_moment = first_moment

    # Include boundaries exactly, while limiting the regular sampling interval to 0.25 ft.
    points = list(np.arange(0.0, span, min(0.025, span / 1600))) + [span]
    for load in loads:
        points.extend([load.position] if load.kind == "point" else [load.start, load.end])
    x = np.unique(np.round(points, 10))
    shear, moment = _internal_forces(x, beam, loads, left)

    section = section_by_name(beam.material, beam.section_name)
    elastic_modulus, allowable_bending = material_properties(beam.material)
    ei = elastic_modulus * section.ix
    # M is kip-ft; curvature uses kip-in / (kip/in^2 * in^4).
    curvature = moment * 12 / ei
    slope = np.zeros_like(x)
    displacement = np.zeros_like(x)
    for i in range(1, len(x)):
        dx = (x[i] - x[i - 1]) * 12
        slope[i] = slope[i - 1] + (curvature[i - 1] + curvature[i]) * dx / 2
        displacement[i] = displacement[i - 1] + (slope[i - 1] + slope[i]) * dx / 2
    if beam.support == "simple":
        displacement -= displacement[0] + (displacement[-1] - displacement[0]) * (x / span)
    else:
        displacement = -displacement

    max_m_i = int(np.argmax(np.abs(moment)))
    max_y_i = int(np.argmax(np.abs(displacement)))
    max_shear = float(np.max(np.abs(shear))) if len(shear) else 0.0
    bending_stress = abs(float(moment[max_m_i])) * 12 / section.sx
    allowable_deflection = span * 12 / beam.limit
    passing = []
    for candidate in SECTIONS[beam.material]:
        stress = abs(float(moment[max_m_i])) * 12 / candidate.sx
        deflection = float(np.max(np.abs(displacement))) * section.ix / candidate.ix
        if stress <= allowable_bending and deflection <= allowable_deflection:
            passing.append(candidate)
    if beam.material == "steel":
        recommended = min(passing, key=lambda s: (s.weight or math.inf, -s.ix)) if passing else None
    else:
        recommended = passing[0] if passing else None

    return AnalysisResult(
        x, shear, moment, displacement, left, right, fixed_moment,
        max_shear, float(moment[max_m_i]), float(x[max_m_i]),
        float(displacement[max_y_i]), float(x[max_y_i]), bending_stress,
        allowable_bending, allowable_deflection, recommended,
    )
