import {
  DEFAULT_QUESTION_COUNT,
  FEEDBACK_COPY,
  REPORT_ACTION_LIBRARY,
} from '../mocks/interviewFixtures'
import { ENV } from '../config/env.js'

const interviewStore = new Map()
const API_BASE_URL = ENV.API_BASE_URL

const STOP_WORDS = new Set([
  'about', 'after', 'again', 'also', 'among', 'and', 'been', 'being', 'both',
  'build', 'candidate', 'company', 'could', 'from', 'have', 'into', 'looking',
  'more', 'most', 'need', 'role', 'team', 'that', 'their', 'there', 'these',
  'they', 'this', 'with', 'your', 'years',
])

const delay = (ms) => new Promise((resolve) => {
  globalThis.setTimeout(resolve, ms)
})

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

const unique = (values) => [...new Set(values.filter(Boolean))]

const humanizeType = (value = 'question') => value
  .split('_')
  .filter(Boolean)
  .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
  .join(' ')

async function readJson(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

function getApiErrorMessage(errorData, fallback) {
  if (!errorData) return fallback
  if (typeof errorData.detail === 'string') return errorData.detail
  if (typeof errorData.message === 'string') return errorData.message

  if (Array.isArray(errorData.detail)) {
    const details = errorData.detail
      .map((item) => item?.msg || item?.message)
      .filter(Boolean)

    if (details.length > 0) {
      return details.join(' ')
    }
  }

  return fallback
}

function normalizeBackendQuestion(question, index) {
  const type = question?.type || 'question'
  const prompt = String(question?.prompt || question?.question || '').trim()

  if (!prompt) {
    throw new Error('The interview service returned a question without text.')
  }

  return {
    id: question?.id || `q${index + 1}`,
    type,
    label: question?.label || humanizeType(type),
    prompt,
    question: question?.question || prompt,
    focus_areas: Array.isArray(question?.focus_areas) ? question.focus_areas : [],
    resume_evidence: question?.resume_evidence || '',
    jd_evidence: question?.jd_evidence || '',
  }
}

function extractKeywords(jobDescription = '') {
  const matches = jobDescription.toLowerCase().match(/[a-z][a-z0-9+.#-]{2,}/g) || []

  return unique(
    matches
      .filter((word) => !STOP_WORDS.has(word))
      .filter((word) => word.length >= 4)
      .slice(0, 8)
  )
}

function extractAnswerSignals(answer = '', context = {}) {
  const normalized = answer.trim()
  const words = normalized ? normalized.split(/\s+/).filter(Boolean) : []
  const keywordMatches = extractKeywords(context.job_description)
    .filter((keyword) => normalized.toLowerCase().includes(keyword))

  return {
    wordCount: words.length,
    sentenceCount: normalized
      ? normalized.split(/[.!?]+/).map((part) => part.trim()).filter(Boolean).length
      : 0,
    hasMetric: /\b\d+(?:\.\d+)?(?:%|x|k|m)?\b/i.test(normalized),
    hasActionVerb: /\b(led|built|designed|launched|improved|reduced|increased|implemented|delivered|optimized|collaborated)\b/i.test(normalized),
    hasReflection: /\b(learned|realized|improved|would|next time|after that)\b/i.test(normalized),
    hasStructure: /\b(situation|task|action|result|challenge|goal|impact|outcome)\b/i.test(normalized),
    keywordMatches,
  }
}

function buildImprovedAnswer(question, context, signals) {
  const role = context.job_title?.trim() || 'the role'
  const company = context.company_name?.trim() || 'the company'
  const keywords = extractKeywords(context.job_description)
  const leadingKeyword = keywords[0] || 'the core skills in the JD'
  const metricLine = signals.hasMetric
    ? 'Keep the strongest metric you already mentioned, but move it earlier so the impact lands faster.'
    : 'Add a measurable result such as time saved, performance improved, revenue influenced, or user impact.'

  return [
    `For ${role} at ${company}, a stronger version would quickly frame the context, clarify your specific action, and end with a concrete result tied to ${leadingKeyword}.`,
    metricLine,
    'A stronger structure is: brief context, your ownership, the decision or challenge, and the final business or technical outcome.',
  ].join(' ')
}

function buildJdAlignment(signals, context) {
  const role = context.job_title?.trim() || 'the role'

  if (signals.keywordMatches.length >= 2) {
    return `Strong alignment. Your answer already echoes key language from the JD and sounds relevant to ${role}.`
  }

  if (signals.keywordMatches.length === 1) {
    return `Moderate alignment. You touched one important JD signal, but you can mirror the role language more explicitly.`
  }

  return `Low-to-moderate alignment. The example may still be relevant, but you should name the skills and priorities that matter most for ${role}.`
}

function pickFeedback(type, signalCategory, fallbackCount = 2) {
  const values = FEEDBACK_COPY[type]?.[signalCategory] || []
  return values.slice(0, fallbackCount)
}

function buildFeedback(question, answer, context) {
  const signals = extractAnswerSignals(answer, context)

  let score = 50
  score += Math.min(20, Math.round(signals.wordCount / 5))
  score += signals.sentenceCount >= 3 ? 6 : 0
  score += signals.hasMetric ? 8 : 0
  score += signals.hasActionVerb ? 6 : 0
  score += signals.hasStructure ? 6 : 0
  score += Math.min(8, signals.keywordMatches.length * 4)
  score -= signals.wordCount < 35 ? 8 : 0
  score -= signals.sentenceCount < 2 ? 5 : 0

  const normalizedScore = clamp(Math.round(score), 42, 96)

  const strengths = []
  if (signals.wordCount >= 50) strengths.push('You provided enough detail to make the example credible.')
  if (signals.hasMetric) strengths.push('You used measurable evidence, which makes the answer more convincing.')
  if (signals.keywordMatches.length > 0) strengths.push('You connected the answer to the JD instead of answering in isolation.')
  if (signals.hasActionVerb) strengths.push('Your wording shows ownership rather than passive participation.')
  strengths.push(...pickFeedback(question.type, 'strengths'))

  const weaknesses = []
  if (signals.wordCount < 45) weaknesses.push('The answer is a bit short and may leave the interviewer asking follow-up questions.')
  if (!signals.hasMetric) weaknesses.push('The impact is not quantified yet, so the result feels less memorable.')
  if (!signals.hasStructure) weaknesses.push('The story can be organized more clearly so the interviewer can follow your logic.')
  if (signals.keywordMatches.length === 0) weaknesses.push('You are not explicitly tying the example back to the JD yet.')
  weaknesses.push(...pickFeedback(question.type, 'weaknesses'))

  const suggestions = []
  if (!signals.hasMetric) suggestions.push('Add one result metric or scale indicator to show the importance of the work.')
  if (!signals.hasStructure) suggestions.push('Use a short STAR structure to separate context, action, and result.')
  if (signals.keywordMatches.length === 0) suggestions.push('Mirror 1-2 keywords from the JD so the fit feels more direct.')
  suggestions.push(...pickFeedback(question.type, 'suggestions'))

  return {
    question_id: question.id,
    score: normalizedScore,
    strengths: unique(strengths).slice(0, 4),
    weaknesses: unique(weaknesses).slice(0, 4),
    suggestions: unique(suggestions).slice(0, 4),
    improved_answer: buildImprovedAnswer(question, context, signals),
    jd_alignment: buildJdAlignment(signals, context),
  }
}

function buildReport(session) {
  const feedbackItems = session.questions
    .map((question) => session.feedbackByQuestion[question.id])
    .filter(Boolean)

  const scoreTotal = feedbackItems.reduce((total, item) => total + item.score, 0)
  const overallScore = feedbackItems.length
    ? Math.round(scoreTotal / feedbackItems.length)
    : 0

  const allStrengths = feedbackItems.flatMap((item) => item.strengths)
  const allWeaknesses = feedbackItems.flatMap((item) => item.weaknesses)

  const summary = overallScore >= 80
    ? 'You sound credible, relevant, and fairly well aligned to the target role. The next improvement is sharpening delivery and evidence.'
    : overallScore >= 68
      ? 'You already have strong raw material, but your answers will improve a lot with clearer structure, tighter JD alignment, and more measurable results.'
      : 'Your answers show potential, but they still need more structure, specificity, and role alignment to land confidently in a real interview.'

  return {
    interview_id: session.interviewId,
    overall_score: overallScore,
    summary,
    strengths: unique(allStrengths).slice(0, 4),
    areas_for_improvement: unique(allWeaknesses).slice(0, 4),
    recommended_actions: REPORT_ACTION_LIBRARY.slice(0, 4),
  }
}

export async function startInterview(payload) {
  const questionCount = payload.question_count || DEFAULT_QUESTION_COUNT
  const requestBody = {
    session_id: payload.session_id,
    job_description: payload.job_description || '',
    job_title: payload.job_title || '',
    company_name: payload.company_name || '',
    question_count: questionCount,
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}/interviews/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })
  } catch {
    throw new Error('Unable to reach the interview service. Please make sure the backend is running.')
  }

  const result = await readJson(response)
  if (!response.ok) {
    throw new Error(
      getApiErrorMessage(result, `Failed to start mock interview: ${response.status}`)
    )
  }

  const data = result?.data || result
  const interviewId = data?.interview_id
  const questions = Array.isArray(data?.questions)
    ? data.questions.map(normalizeBackendQuestion)
    : []

  if (!interviewId || questions.length === 0) {
    throw new Error('Invalid mock interview response from server.')
  }

  interviewStore.set(interviewId, {
    interviewId,
    context: payload,
    questions,
    answersByQuestion: {},
    feedbackByQuestion: {},
  })
  return {
    interview_id: interviewId,
    questions,
  }
}

export async function submitInterviewAnswer(payload) {
  const session = interviewStore.get(payload.interview_id)

  if (!session) {
    throw new Error('Interview session not found. Please start the mock interview again.')
  }

  const question = session.questions.find((item) => item.id === payload.question_id)
  if (!question) {
    throw new Error('Question not found for this interview session.')
  }

  const feedback = buildFeedback(question, payload.answer, session.context)

  session.answersByQuestion[payload.question_id] = payload.answer
  session.feedbackByQuestion[payload.question_id] = feedback

  await delay(900)

  return feedback
}

export async function getInterviewReport(payload) {
  const session = interviewStore.get(payload.interview_id)

  if (!session) {
    throw new Error('Interview session not found. Please restart the mock interview.')
  }

  await delay(650)

  return buildReport(session)
}
