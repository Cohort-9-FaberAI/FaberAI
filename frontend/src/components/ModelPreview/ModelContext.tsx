import { createContext } from 'react'
import { type AnalysisResult } from '../../types/analysis'

export const ModelContext = createContext<AnalysisResult | null>(null)
