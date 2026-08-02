import initializeOcctImportJs, { type OcctImporter } from 'occt-import-js'

import wasmUrl from 'occt-import-js/dist/occt-import-js.wasm?url'

let importerPromise: Promise<OcctImporter> | undefined

export function getOcctImporter(): Promise<OcctImporter> {
  importerPromise ??= initializeOcctImportJs({
    locateFile: (path) => (path.endsWith('.wasm') ? wasmUrl : path),
  })

  return importerPromise
}
