from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class Undercut:
    """A group of adjacent faces the mold cannot reach in a straight line
    along their own release direction, for a given single pull direction.

    `releasable` is a PLACEHOLDER until Stage 2 (side-action reachability)
    is built — defaults to True ("assume fixable via a side-action") since
    that's the conservative default already used elsewhere in the DFM rule
    layer (an inference should not call a part unmouldable). Once Stage 2
    exists, this will be set based on an actual reachability test.
    """

    id: int
    pull_direction: np.ndarray
    center: np.ndarray
    face_ids: list = field(default_factory=list)
    max_shadow_depth: Optional[float] = None  # how deep the blocking material is, if measured
    releasable: bool = True  # PLACEHOLDER -- see docstring