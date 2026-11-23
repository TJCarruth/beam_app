import unittest

from beam_app.analysis import analyze
from beam_app.models import BeamInput, Load


def beam(span, support, material, section, loads):
    return BeamInput(span, support, material, section, 360, loads)


class BeamAnalysisExamples(unittest.TestCase):
    def test_simply_supported_uniform_load(self):
        result = analyze(beam(20, "simple", "steel", "W12x26", [Load("uniform", 1, start=0, end=20)]))
        self.assertAlmostEqual(result.reaction_left, 10, places=3)
        self.assertAlmostEqual(result.reaction_right, 10, places=3)
        self.assertAlmostEqual(abs(result.max_moment), 50, places=1)
        self.assertAlmostEqual(result.bending_stress, 17.96, places=1)
        self.assertAlmostEqual(abs(result.max_deflection), .609, places=2)
        self.assertAlmostEqual(result.max_deflection_x, 10, places=1)

    def test_simply_supported_point_load(self):
        result = analyze(beam(20, "simple", "steel", "W12x26", [Load("point", 10, position=5)]))
        self.assertAlmostEqual(result.reaction_left, 7.5, places=3)
        self.assertAlmostEqual(result.reaction_right, 2.5, places=3)
        self.assertAlmostEqual(abs(result.max_moment), 37.5, places=1)
        self.assertAlmostEqual(abs(result.max_deflection), .340, places=2)
        self.assertAlmostEqual(result.max_deflection_x, 8.82, delta=.04)

    def test_cantilever_end_load(self):
        result = analyze(beam(10, "cantilever", "steel", "W12x26", [Load("point", 5, position=10)]))
        self.assertAlmostEqual(result.reaction_left, 5, places=3)
        self.assertAlmostEqual(result.reaction_moment, 50, places=3)
        self.assertAlmostEqual(abs(result.max_deflection), .487, places=2)
        self.assertAlmostEqual(result.max_deflection_x, 10, places=2)

    def test_wood_joist(self):
        result = analyze(beam(12, "simple", "wood", "2x10", [Load("uniform", .05, start=0, end=12)]))
        self.assertAlmostEqual(abs(result.max_moment), .9, places=2)
        self.assertAlmostEqual(result.bending_stress, .505, places=2)
        self.assertAlmostEqual(abs(result.max_deflection), .147, places=2)

    def test_load_clipping_and_zero_length(self):
        result = analyze(beam(10, "simple", "steel", "W12x26", [
            Load("uniform", 1, start=8, end=14), Load("uniform", 9, start=4, end=4),
        ]))
        self.assertAlmostEqual(result.reaction_left + result.reaction_right, 2, places=5)


if __name__ == "__main__":
    unittest.main()
