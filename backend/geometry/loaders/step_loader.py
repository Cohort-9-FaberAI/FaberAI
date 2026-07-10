import trimesh
from build123d import *

def load_step(file_path):
  shape = import_step(file_path)
  return shape
