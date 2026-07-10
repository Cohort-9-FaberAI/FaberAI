import trimesh


def load_stl(file_path):
  mesh = trimesh.load(file_path)
  return mesh
