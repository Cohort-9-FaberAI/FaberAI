declare module 'occt-import-js' {
  export interface OcctModuleOptions {
    locateFile?: (path: string, prefix: string) => string
  }

  export type LinearUnit = 'millimeter' | 'centimeter' | 'meter' | 'inch' | 'foot'

  export type LinearDeflectionType = 'bounding_box_ratio' | 'absolute_value'

  export interface ImportParameters {
    linearUnit?: LinearUnit
    linearDeflectionType?: LinearDeflectionType
    linearDeflection?: number
    angularDeflection?: number
  }

  export interface NumericAttribute {
    array: number[]
  }

  export interface ImportedMesh {
    name: string
    color?: [number, number, number]
    attributes: {
      position: NumericAttribute
      normal?: NumericAttribute
    }
    index: NumericAttribute
  }

  export interface ImportResult {
    success: boolean
    meshes: ImportedMesh[]
  }

  export interface OcctImporter {
    ReadStepFile(content: Uint8Array, parameters: ImportParameters | null): ImportResult
  }

  export default function initializeOcctImportJs(options?: OcctModuleOptions): Promise<OcctImporter>
}
