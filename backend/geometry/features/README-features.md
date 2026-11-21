# Geometry feature extraction

These modules detect manufacturing features from STEP topology and measured
faces. `geometry/loaders/dispatcher.py` invokes them while constructing the
`GeometryModel` consumed by `app/services/geometry_engine_adapter.py`.

| Module | Features |
| --- | --- |
| `holes.py` | Cylindrical holes and hole measurements |
| `bosses.py` | Bosses and attachment measurements |
| `cavities.py` | Cavities and pockets |
| `fillets.py` | Rounded transitions |
| `chamfers.py` | Beveled transitions |
| `ribs.py` | Rib candidates and measurements |
| `overhangs.py` | Overhanging faces relative to a build direction |

STL analysis uses separate mesh heuristics in `geometry/Mesh_features/`.
Triangle meshes cannot provide every B-rep measurement available from STEP;
missing feature evidence must remain distinguishable from a measured absence.

Run the [geometry tests](../../tests/geometry/readme-tests.md) after changing
feature detection. See the [DFM guide](../../dfm/README-dfm.md) for how downstream
rules consume measurements.
