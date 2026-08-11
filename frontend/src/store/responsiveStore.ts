//a second zustand store made to separate frequently updating things (setHighlighted) from infrequently updated things.
//from my brief readings, it appears that we are using the zustand Slices pattern incorrectly, resulting in any change to the store
//causing a re-render of all things relying on the store. This is the source of many of our performance issues regarding the 3d-viewport,
//which previously would update the setHighlighted store frequently. I believe that a general fix is in order for future maintenanability
//but for the scope of our MVP, I am moving the "responsive" store components here instead. -Jody

import { create, type StateCreator } from 'zustand'

interface SelectedIssueSlice {
  highlightedIssue: string | null
  setHighlightedIssue: (issue: string | null) => void
  focusedIssueId: string | null
  focusNonce: number
  setFocusedIssue: (issue: string | null) => void
}

export const createSelectedIssueSlice: StateCreator<
  SelectedIssueSlice,
  [],
  [],
  SelectedIssueSlice
> = (set) => ({
  highlightedIssue: null,
  setHighlightedIssue: (issue) => set({ highlightedIssue: issue }),
  focusedIssueId: null,
  focusNonce: 0,
  setFocusedIssue: (issue) =>
    set((s) => ({
      focusedIssueId: issue,
      focusNonce: issue ? s.focusNonce + 1 : s.focusNonce,
    })),
})

type StoreState = SelectedIssueSlice

export const useStore = create<StoreState>((...args) => ({
  ...createSelectedIssueSlice(...args),
}))
