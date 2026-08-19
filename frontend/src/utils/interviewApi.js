import {
  DEFAULT_QUESTION_COUNT,
  REPORT_ACTION_LIBRARY,
} from '../mocks/interviewFixtures'
import { ENV } from '../config/env.js'
import { pollJobResult } from './api.js'

const interviewStore = new Map()
const API_BASE_URL = ENV.API_BASE_URL

const delay = (ms) => new Promise((resolve) => {
  globalThis.setTimeout(resolve, ms)
})

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

function normalizeTextArray(value) {
  return Array.isArray(value)
    ? value.map((item) => String(item).trim()).filter(Boolean)
    : []
}

function normalizeAnswerFeedback(feedback, fallbackQuestionId) {
  const score = Number(feedback?.score)

  if (!Number.isFinite(score)) {
    throw new Error('The interview service returned feedback without a valid score.')
  }

  return {
    question_id: feedback?.question_id || fallbackQuestionId,
    score,
    strengths: normalizeTextArray(feedback?.strengths),
    weaknesses: normalizeTextArray(feedback?.weaknesses),
    suggestions: normalizeTextArray(feedback?.suggestions),
    improved_answer: feedback?.improved_answer || '',
    jd_alignment: feedback?.jd_alignment || '',
    scoring_breakdown: feedback?.scoring_breakdown || null,
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

  const jobId = result?.data?.job_id
  if (!jobId) {
    throw new Error('Invalid mock interview submission response from server.')
  }

  const data = await pollJobResult(jobId)
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

  const requestBody = {
    interview_id: session.interviewId,
    session_id: session.context.session_id,
    question_id: question.id,
    question_type: question.type,
    question: question.question || question.prompt,
    resume_evidence: question.resume_evidence || '',
    jd_evidence: question.jd_evidence || '',
    focus_areas: question.focus_areas || [],
    answer: payload.answer,
    job_description: session.context.job_description || '',
    job_title: session.context.job_title || '',
    company_name: session.context.company_name || '',
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}/interviews/answer`, {
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
      getApiErrorMessage(result, `Failed to evaluate your answer: ${response.status}`)
    )
  }

  const jobId = result?.data?.job_id
  if (!jobId) {
    throw new Error('Invalid answer evaluation submission response from server.')
  }

  const feedback = normalizeAnswerFeedback(
    await pollJobResult(jobId),
    payload.question_id
  )

  session.answersByQuestion[payload.question_id] = payload.answer
  session.feedbackByQuestion[payload.question_id] = feedback

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
