import type { AnalysisResult } from '../../types/analysis'
import { API_BASE } from '../../lib/api'
import { STLLoader } from 'three/examples/jsm/Addons.js'
import { getOcctImporter } from './occt-importer'
import type { ImportedMesh } from 'occt-import-js'
import { BufferGeometry, Float32BufferAttribute } from 'three'

export async function fetchAnalysis() {
  const res = await fetch(`${API_BASE}/analyze-mock`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  })
  const result = (await res.json()) as AnalysisResult
  return result
}

export async function getGeometry(url: string, type: 'STL' | 'STEP') {
  if (type === 'STL') {
    return [await new STLLoader().loadAsync(url)]
  } else {
    return getSTEPGeometry(url)
  }
}

export async function stepBufferToGeometry(arrayBuffer: ArrayBuffer): Promise<BufferGeometry> {
  const importer = await getOcctImporter()
  const result = importer.ReadStepFile(new Uint8Array(arrayBuffer), null)

  if (!result.success) throw new Error(`Occt Importer failed to read step file!`)

  return mergeGeometries(result.meshes.map((x) => importedMeshToGeometry(x)))
}

function mergeGeometries(geometries: BufferGeometry[]): BufferGeometry {
  if (geometries.length === 1) return geometries[0]

  const merged = new BufferGeometry()
  const position: number[] = []
  const normal: number[] = []
  const index: number[] = []

  let vertexOffset = 0

  for (const geometry of geometries) {
    const posAttr = geometry.getAttribute('position')
    const normAttr = geometry.getAttribute('normal')
    const indexAttr = geometry.getIndex()

    if (!posAttr) continue
    const posArray = posAttr.array as ArrayLike<number>
    const normArray = normAttr && (normAttr.array as ArrayLike<number>)

    for (let i = 0; i < posAttr.count; i++) {
      position.push(posArray[i * 3], posArray[i * 3 + 1], posArray[i * 3 + 2])
      if (normArray) {
        normal.push(normArray[i * 3], normArray[i * 3 + 1], normArray[i * 3 + 2])
      }
    }

    if (indexAttr) {
      const indexArray = indexAttr.array as ArrayLike<number>
      for (let i = 0; i < indexAttr.count; i++) {
        index.push(indexArray[i] + vertexOffset)
      }
    }

    vertexOffset += posAttr.count
  }

  merged.setAttribute('position', new Float32BufferAttribute(position, 3))
  merged.setIndex(index)
  if (normal.length > 0) {
    merged.setAttribute('normal', new Float32BufferAttribute(normal, 3))
  }
  merged.computeBoundingBox()
  merged.computeBoundingSphere()
  merged.computeVertexNormals()

  return merged
}

async function getSTEPGeometry(url: string) {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP error! Status: ${response.status}`)
  }
  const arrayBuffer = await response.arrayBuffer()

  const importer = await getOcctImporter()
  const result = importer.ReadStepFile(new Uint8Array(arrayBuffer), null)

  if (!result.success) throw new Error(`Occt Importer failed to read step file!`)

  return result.meshes.map((x) => importedMeshToGeometry(x))
}

function importedMeshToGeometry(mesh: ImportedMesh): BufferGeometry {
  const geometry = new BufferGeometry()

  geometry.setAttribute('position', new Float32BufferAttribute(mesh.attributes.position.array, 3))

  if (mesh.attributes.normal) {
    geometry.setAttribute('normal', new Float32BufferAttribute(mesh.attributes.normal.array, 3))
  } else {
    geometry.computeVertexNormals()
  }

  geometry.setIndex(mesh.index.array)

  geometry.computeBoundingBox()
  geometry.computeBoundingSphere()

  return geometry
}
