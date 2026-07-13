import numpy as np


def extract_faces_mesh(mesh):
  face_indices_array = mesh.faces
  return np.array(face_indices_array), np.array(mesh.vertices)

def extract_faces_occ(shape):
  vertices, indices = shape.tessellate(tolerance=0.1)

  np_vertices = np.array([tuple(v) for v in vertices])
  np_indices = np.array(indices)

  return np_vertices, np_indices

# face extraction gives an array of the vertex locations and the indices of
# those vertex locations (to save memory)
# example: vertices_array[face_indices_array[face_number]]
