"""Constraint modules for enforcing physical and fabrication requirements.

This package provides constraint modules that can be applied during optimization
to ensure designs meet physical realizability and fabrication requirements.
Key constraints include:

- Minimum feature size constraints
- Binary material constraints (air/dielectric only)
- Connectivity constraints (no floating material)
- Fabrication constraints (no trapped air, etc.)

The constraints are implemented as modules that can be chained together
and applied during the optimization process.
"""

from .initialization import BoundaryConfig, boundary_objects_from_config
from .perfectly_matched_layer import PerfectlyMatchedLayer
from .periodic import PeriodicBoundary

__all__ = [
    "BoundaryConfig",
    "boundary_objects_from_config",
    "PerfectlyMatchedLayer",
    "PeriodicBoundary",
]
