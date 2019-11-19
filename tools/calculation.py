import numpy as np


def point_to_line_distance(p, p1, p2):
    length = np.linalg.norm(p2 - p1)
    if length == 0:
        return 0
    else:
        return np.linalg.norm(np.cross(p2-p1, p-p1)) / length

