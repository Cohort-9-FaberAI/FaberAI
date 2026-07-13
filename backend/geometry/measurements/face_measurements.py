import numpy as np

def compute_face_area(face) -> float:
  return 0.5 * np.linalg.norm(np.cross((face[0] - face[1]), (face[0] - face[2])))

def compute_face_centroid(face) -> np.ndarray:
  return np.array([np.mean([face[0][0], face[1][0], face[2][0]]), np.mean([face[0][1], face[1][1], face[2][1]]), np.mean([face[0][2], face[1][2], face[2][2]])])

def compute_face_normal(face) -> np.ndarray:
  unnormalized_normal = np.cross((face[0] - face[1]), (face[0] - face[2]))
  normal = unnormalized_normal / (np.linalg.norm(unnormalized_normal))
  return normal

# Uses vertices array and incices array
# example: compute_face_normal(vertices_array[face_indices_array[0]])
