"""Typed input and output models for beam analysis."""

from dataclasses import dataclass
from typing import Literal

Support = Literal["simple", "cantilever"]
Material = Literal["steel", "wood"]


@dataclass
class Load:
    kind: Literal["point", "uniform"]
    magnitude: float
    position: float = 0.0
    start: float = 0.0
    end: float = 0.0


@dataclass
class BeamInput:
    span: float
    support: Support
    material: Material
    section_name: str
    limit: int
    loads: list[Load]


@dataclass(frozen=True)
class Section:
    name: str
    ix: float
    sx: float
    weight: float | None = None


@dataclass
class AnalysisResult:
    x: object
    shear: object
    moment: object
    deflection: object
    reaction_left: float
    reaction_right: float
    reaction_moment: float
    max_shear: float
    max_moment: float
    max_moment_x: float
    max_deflection: float
    max_deflection_x: float
    bending_stress: float
    bending_allowable: float
    deflection_allowable: float
    recommended_section: Section | None
