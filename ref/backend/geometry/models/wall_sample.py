from dataclasses import dataclass
import numpy as np


@dataclass
class WallSample:
    """
    One local wall thickness measurement.
    """

    id: int

    point: np.ndarray              # measurement location

    normal: np.ndarray             # outward normal

    thickness: float               # mm

    face_id: int

    opposite_face_id: int | None

    ray_length: float

    reliable: bool = True