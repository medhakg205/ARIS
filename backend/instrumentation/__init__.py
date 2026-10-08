"""
ARIS Transparent Sketch Instrumentation Module.
Enables non-invasive, shadow-build instrumentation of standard Arduino sketches.
"""

from .sketch_instrumenter import SketchInstrumenter, InstrumentationResult

__all__ = ["SketchInstrumenter", "InstrumentationResult"]
