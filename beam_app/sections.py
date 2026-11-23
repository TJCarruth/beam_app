"""Material and section property tables."""

from .models import Material, Section

STEEL_E = 29_000.0
STEEL_FB = 30.0
WOOD_E = 1_600.0
WOOD_FB = 0.9

SECTIONS: dict[Material, tuple[Section, ...]] = {
    "steel": (
        Section("W8x10", 30.8, 7.81, 10), Section("W10x12", 53.8, 10.9, 12),
        Section("W12x26", 204, 33.4, 26), Section("W14x22", 199, 29.0, 22),
        Section("W16x26", 301, 38.4, 26), Section("W18x35", 510, 57.6, 35),
        Section("W21x44", 843, 81.6, 44), Section("W24x55", 1350, 114, 55),
    ),
    "wood": (
        Section("2x8", 47.63, 13.14), Section("2x10", 98.93, 21.39),
        Section("2x12", 177.98, 31.64),
    ),
}


def material_properties(material: Material) -> tuple[float, float]:
    return (STEEL_E, STEEL_FB) if material == "steel" else (WOOD_E, WOOD_FB)


def section_by_name(material: Material, name: str) -> Section:
    return next(section for section in SECTIONS[material] if section.name == name)
