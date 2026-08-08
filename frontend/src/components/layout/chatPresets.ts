// Routes where the chat panel and its trigger button are shown at all.
// Per product decision, chat is scoped to the analysis workspace (which now
// covers the old Extra Info / Conclusion steps internally) — everywhere else
// (login, upload, projects, library, history) has no chat entry point.
const CHAT_ENABLED_ROUTES = ['/analysis']

export function isChatEnabledForRoute(pathname: string): boolean {
  return CHAT_ENABLED_ROUTES.includes(pathname)
}

// Maps a route path to suggested question chips shown in the chat panel.
// Falls back to DEFAULT_QUESTIONS for routes with no preset list.
export const PAGE_QUESTIONS: Record<string, string[]> = {
  '/analysis': [
    'What is the most severe issue?',
    'How can I fix the wall thickness issue?',
    'Why did this part score the way it did?',
  ],
}

const DEFAULT_QUESTIONS = ['What can you help me with here?']

export function getPageQuestions(pathname: string): string[] {
  return PAGE_QUESTIONS[pathname] ?? DEFAULT_QUESTIONS
}
