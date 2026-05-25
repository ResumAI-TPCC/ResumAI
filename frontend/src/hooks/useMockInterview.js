import { useMemo, useState } from 'react'
import {
  getInterviewReport,
  startInterview,
  submitInterviewAnswer,
} from '../utils/interviewApi'

const INITIAL_STATE = {
  status: 'idle',
  interviewId: null,
  questions: [],
  currentQuestionIndex: 0,
  draftAnswer: '',
  answersByQuestion: {},
  feedbackByQuestion: {},
  finalReport: null,
  error: null,
  startContext: null,
}

export function useMockInterview() {
  const [state, setState] = useState(INITIAL_STATE)

  const currentQuestion = useMemo(
    () => state.questions[state.currentQuestionIndex] || null,
    [state.currentQuestionIndex, state.questions]
  )

  const currentFeedback = currentQuestion
    ? state.feedbackByQuestion[currentQuestion.id] || null
    : null

  const submittedAnswer = currentQuestion
    ? state.answersByQuestion[currentQuestion.id] || ''
    : ''

  const isStarting = state.status === 'starting'
  const isSubmitting = state.status === 'submitting'
  const isGeneratingReport = state.status === 'generatingReport'
  const isCompleted = state.status === 'completed'
  const hasActiveInterview = Boolean(state.interviewId)

  const resetInterview = () => {
    setState(INITIAL_STATE)
  }

  const updateDraftAnswer = (value) => {
    setState((previous) => ({
      ...previous,
      draftAnswer: value,
      error: null,
    }))
  }

  const startInterviewSession = async (context) => {
    setState({
      ...INITIAL_STATE,
      status: 'starting',
      startContext: context,
    })

    try {
      const response = await startInterview(context)
      const firstQuestion = response.questions[0] || null

      setState({
        status: firstQuestion ? 'questionReady' : 'idle',
        interviewId: response.interview_id,
        questions: response.questions,
        currentQuestionIndex: 0,
        draftAnswer: '',
        answersByQuestion: {},
        feedbackByQuestion: {},
        finalReport: null,
        error: null,
        startContext: context,
      })

      return response
    } catch (error) {
      setState((previous) => ({
        ...previous,
        status: 'idle',
        error: error.message || 'Failed to start mock interview.',
      }))
      throw error
    }
  }

  const submitCurrentAnswer = async () => {
    if (!state.interviewId || !currentQuestion) return null

    const trimmedAnswer = state.draftAnswer.trim()
    if (!trimmedAnswer) {
      setState((previous) => ({
        ...previous,
        error: 'Please enter your answer before submitting.',
      }))
      return null
    }

    setState((previous) => ({
      ...previous,
      status: 'submitting',
      error: null,
    }))

    try {
      const feedback = await submitInterviewAnswer({
        interview_id: state.interviewId,
        question_id: currentQuestion.id,
        answer: trimmedAnswer,
      })

      setState((previous) => ({
        ...previous,
        status: 'feedbackReady',
        draftAnswer: trimmedAnswer,
        answersByQuestion: {
          ...previous.answersByQuestion,
          [currentQuestion.id]: trimmedAnswer,
        },
        feedbackByQuestion: {
          ...previous.feedbackByQuestion,
          [currentQuestion.id]: feedback,
        },
        error: null,
      }))

      return feedback
    } catch (error) {
      setState((previous) => ({
        ...previous,
        status: 'questionReady',
        error: error.message || 'Failed to evaluate your answer.',
      }))
      throw error
    }
  }

  const goToNextStep = async () => {
    if (!currentQuestion) return null

    const isLastQuestion = state.currentQuestionIndex >= state.questions.length - 1
    if (!isLastQuestion) {
      const nextQuestion = state.questions[state.currentQuestionIndex + 1]
      const savedAnswer = nextQuestion
        ? state.answersByQuestion[nextQuestion.id] || ''
        : ''

      setState((previous) => ({
        ...previous,
        status: previous.feedbackByQuestion[nextQuestion?.id] ? 'feedbackReady' : 'questionReady',
        currentQuestionIndex: previous.currentQuestionIndex + 1,
        draftAnswer: savedAnswer,
        error: null,
      }))

      return nextQuestion
    }

    setState((previous) => ({
      ...previous,
      status: 'generatingReport',
      error: null,
    }))

    try {
      const report = await getInterviewReport({
        interview_id: state.interviewId,
      })

      setState((previous) => ({
        ...previous,
        status: 'completed',
        finalReport: report,
        error: null,
      }))

      return report
    } catch (error) {
      setState((previous) => ({
        ...previous,
        status: 'feedbackReady',
        error: error.message || 'Failed to generate the interview report.',
      }))
      throw error
    }
  }

  const restartInterview = async () => {
    if (!state.startContext) return null
    return startInterviewSession(state.startContext)
  }

  return {
    ...state,
    currentQuestion,
    currentFeedback,
    submittedAnswer,
    isStarting,
    isSubmitting,
    isGeneratingReport,
    isCompleted,
    hasActiveInterview,
    updateDraftAnswer,
    startInterviewSession,
    submitCurrentAnswer,
    goToNextStep,
    restartInterview,
    resetInterview,
  }
}
