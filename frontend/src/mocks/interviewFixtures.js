export const DEFAULT_QUESTION_COUNT = 5

export const QUESTION_TYPE_META = {
  self_intro: {
    label: 'Self Introduction',
    accent: 'blue',
  },
  resume_based: {
    label: 'Resume-based',
    accent: 'emerald',
  },
  project_followup: {
    label: 'Project Follow-up',
    accent: 'amber',
  },
  jd_skill_match: {
    label: 'JD Skill Match',
    accent: 'violet',
  },
  behavioral: {
    label: 'Behavioral',
    accent: 'rose',
  },
}

export const QUESTION_BLUEPRINTS = [
  {
    type: 'self_intro',
    focusAreas: ['motivation', 'role fit', 'career narrative'],
  },
  {
    type: 'resume_based',
    focusAreas: ['resume relevance', 'ownership', 'impact'],
  },
  {
    type: 'project_followup',
    focusAreas: ['technical depth', 'decision making', 'execution'],
  },
  {
    type: 'jd_skill_match',
    focusAreas: ['skill alignment', 'tools', 'job readiness'],
  },
  {
    type: 'behavioral',
    focusAreas: ['collaboration', 'problem solving', 'reflection'],
  },
]

export const FEEDBACK_COPY = {
  self_intro: {
    strengths: [
      'You are connecting your background to the target role rather than listing generic resume facts.',
      'The answer has a strong opening and sounds confident.',
      'You are already signaling why this opportunity makes sense for your next step.',
    ],
    weaknesses: [
      'The career story can be tightened so the listener hears a clearer beginning, middle, and goal.',
      'The role motivation is still a little generic and could sound more tailored to the employer.',
      'The answer would be stronger with one concrete result that proves credibility early.',
    ],
    suggestions: [
      'Use a 60-90 second structure: who you are, what you have done, and why this role is the logical next step.',
      'Mention one metric or outcome near the start so your introduction feels evidence-based.',
      'Name one thing about the JD or company that genuinely matches your recent experience.',
    ],
  },
  resume_based: {
    strengths: [
      'You are selecting an experience that feels relevant to the target position.',
      'The response shows responsibility rather than only describing team output.',
      'There is enough context for the interviewer to understand the business or project scope.',
    ],
    weaknesses: [
      'The most valuable impact is implied but not yet quantified clearly.',
      'Some parts still describe tasks instead of the decision you personally drove.',
      'The answer can better connect the project back to the role you are applying for.',
    ],
    suggestions: [
      'Use STAR or CAR to separate context, your action, and measurable impact.',
      'Call out your individual contribution with stronger action verbs like led, designed, improved, or delivered.',
      'Close with one sentence on why this example matters for the new role.',
    ],
  },
  project_followup: {
    strengths: [
      'The answer gives useful project detail instead of staying purely high-level.',
      'You are starting to show technical judgment and trade-off thinking.',
      'The response has the right material to support deeper follow-up questions.',
    ],
    weaknesses: [
      'The technical decision process could be more explicit.',
      'The interviewer may still wonder what constraints made the problem difficult.',
      'There is room to explain the result of your specific contribution more crisply.',
    ],
    suggestions: [
      'Explain the problem, the constraint, and why you picked one solution over another.',
      'Mention one challenge, one decision, and one measurable outcome.',
      'If possible, connect the project detail back to a core capability in the JD.',
    ],
  },
  jd_skill_match: {
    strengths: [
      'The answer is staying close to the requirements that matter for this role.',
      'You are making it easier for the interviewer to map your skills to the JD.',
      'The structure supports a clear "yes, I have done this before" message.',
    ],
    weaknesses: [
      'The JD alignment would be stronger if you named the exact tools, systems, or scope involved.',
      'The answer could sound more role-specific by mirroring the employer\'s language.',
      'You still need one concrete example that proves this skill in practice.',
    ],
    suggestions: [
      'Mirror 1-2 keywords from the JD naturally instead of paraphrasing too broadly.',
      'Pair every claimed skill with a short example of where you used it.',
      'End with the business outcome so the skill sounds applied, not theoretical.',
    ],
  },
  behavioral: {
    strengths: [
      'You are giving enough human context for a behavioral answer.',
      'The tone shows ownership and reflection rather than blame.',
      'The answer has a good foundation for showing collaboration and judgment.',
    ],
    weaknesses: [
      'The story can be more concise so the main lesson lands faster.',
      'The resolution and impact are not yet as memorable as they could be.',
      'The reflection section can better show what you learned or changed afterwards.',
    ],
    suggestions: [
      'Use a short STAR structure and spend most of the time on your action and result.',
      'Describe what made the situation difficult and how you influenced the outcome.',
      'Finish with one lesson learned that is relevant to future teamwork.',
    ],
  },
}

export const REPORT_ACTION_LIBRARY = [
  'Rehearse each answer with a tighter STAR structure and keep the result sentence explicit.',
  'Add at least one metric, scale indicator, or business outcome to your strongest examples.',
  'Mirror the JD language more directly when describing relevant skills and projects.',
  'Prepare a concise 60-second self-introduction that links your past experience to this role.',
  'Practice two deeper follow-up stories on technical decisions and collaboration trade-offs.',
]
