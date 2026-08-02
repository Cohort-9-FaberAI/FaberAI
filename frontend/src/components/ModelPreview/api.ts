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

async function getSTEPGeometry(url: string) {
  url = 'https://jody-web-server.vercel.app/api/cad/step'

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
