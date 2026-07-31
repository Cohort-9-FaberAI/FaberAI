// Maps a route path to suggested question chips shown in the chat panel.
// Falls back to DEFAULT_QUESTIONS for routes with no preset list.
export const PAGE_QUESTIONS: Record<string, string[]> = {
  '/home': ['What file formats are supported?', 'How does the upload process work?'],
  '/extra-info': [
    'How does material choice affect manufacturability?',
    'What tolerance should I pick for this process?',
  ],
  '/analysis': [
    'What is the most severe issue?',
    'How can I fix the wall thickness issue?',
    'Why did this part score the way it did?',
  ],
  '/conclusion': ['Summarize the key manufacturability risks.', 'What should I fix first?'],
}

const DEFAULT_QUESTIONS = ['What can you help me with here?']

export function getPageQuestions(pathname: string): string[] {
  return PAGE_QUESTIONS[pathname] ?? DEFAULT_QUESTIONS
}
