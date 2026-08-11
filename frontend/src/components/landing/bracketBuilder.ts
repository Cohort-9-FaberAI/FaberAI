import * as THREE from 'three'

export interface BracketOptions {
  wireColor?: number
  startOpacity: number
  markersHidden?: boolean
}

export interface BracketResult {
  solidMesh: THREE.Mesh
  wireMesh: THREE.LineSegments
  solidMat: THREE.MeshStandardMaterial
  wireMat: THREE.LineBasicMaterial
  markers: THREE.Mesh[]
}

function mergeGeoms(geoms: THREE.BufferGeometry[]): THREE.BufferGeometry {
  const totalPos: number[] = []
  const totalNorm: number[] = []
  geoms.forEach((g) => {
    g.computeVertexNormals()
    const pos = g.attributes.position.array
    const norm = g.attributes.normal.array
    for (let i = 0; i < pos.length; i++) totalPos.push(pos[i])
    for (let i = 0; i < norm.length; i++) totalNorm.push(norm[i])
  })
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.Float32BufferAttribute(totalPos, 3))
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(totalNorm, 3))
  return geo
}

export function buildBracket(group: THREE.Group, opts: BracketOptions): BracketResult {
  const primary = new THREE.Color(0x0858f4)
  const solidMat = new THREE.MeshStandardMaterial({
    color: primary,
    metalness: 0.25,
    roughness: 0.4,
    transparent: true,
    opacity: opts.startOpacity,
  })
  const wireMat = new THREE.LineBasicMaterial({
    color: opts.wireColor !== undefined ? opts.wireColor : 0xffffff,
    transparent: true,
    opacity: 1 - opts.startOpacity * 0.85,
  })

  const base = new THREE.BoxGeometry(2.6, 0.42, 1.7)
  base.translate(0, -0.6, 0)
  const wall = new THREE.BoxGeometry(0.42, 1.7, 1.7)
  wall.translate(-1.1, 0.25, 0)

  const merged = mergeGeoms([base, wall])

  const solidMesh = new THREE.Mesh(merged, solidMat)
  const edges = new THREE.EdgesGeometry(merged, 12)
  const wireMesh = new THREE.LineSegments(edges, wireMat)

  group.add(solidMesh)
  group.add(wireMesh)

  const holeMat = new THREE.MeshStandardMaterial({
    color: 0x081040,
    metalness: 0.1,
    roughness: 0.7,
  })
  const holePositions: [number, number, number][] = [
    [0.6, -0.6, 0.5],
    [0.9, -0.6, -0.5],
    [-1.1, 0.7, 0.5],
    [-1.1, 0.9, -0.4],
  ]
  holePositions.forEach((p) => {
    const h = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.5, 16), holeMat)
    h.rotation.x = p[1] < -0.1 && Math.abs(p[0]) > 0.3 ? Math.PI / 2 : 0
    if (p[0] < -0.9) {
      h.rotation.z = Math.PI / 2
    }
    h.position.set(p[0], p[1], p[2])
    group.add(h)
  })

  const markerPositions = [
    { pos: [1.25, -0.4, 0.86] as [number, number, number], sev: 'major', idx: 0 },
    { pos: [-1.1, 0.95, 0.86] as [number, number, number], sev: 'major', idx: 1 },
    { pos: [-1.1, -0.05, 0.86] as [number, number, number], sev: 'major', idx: 2 },
    { pos: [-1.1, 0.4, -0.86] as [number, number, number], sev: 'minor', idx: 3 },
    { pos: [0.3, -0.81, -0.6] as [number, number, number], sev: 'major', idx: 4 },
  ]
  const markers: THREE.Mesh[] = []
  markerPositions.forEach((m) => {
    const color = m.sev === 'major' ? 0xe4572e : 0xf5a623
    const mat = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: opts.markersHidden ? 0 : 1,
    })
    const sphere = new THREE.Mesh(new THREE.SphereGeometry(0.06, 16, 16), mat)
    sphere.position.set(...m.pos)
    sphere.userData = { findingIdx: m.idx, mat }
    sphere.visible = !opts.markersHidden
    group.add(sphere)
    markers.push(sphere)
  })

  return { solidMesh, wireMesh, solidMat, wireMat, markers }
}

export function animateOpacity(
  bracket: { solidMat: THREE.MeshStandardMaterial; wireMat: THREE.LineBasicMaterial },
  toSolid: boolean,
) {
  const startSolid = bracket.solidMat.opacity
  const endSolid = toSolid ? 1 : 0
  const startWire = bracket.wireMat.opacity
  const endWire = toSolid ? 0.12 : 0.85
  const dur = 900
  const t0 = performance.now()

  function step(now: number) {
    const p = Math.min(1, (now - t0) / dur)
    const ease = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2
    bracket.solidMat.opacity = startSolid + (endSolid - startSolid) * ease
    bracket.wireMat.opacity = startWire + (endWire - startWire) * ease
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}
