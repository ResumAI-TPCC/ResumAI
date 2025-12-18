import express from 'express'
import cors from 'cors'
import multer from 'multer'
import { promises as fs } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { v4 as uuid } from 'uuid'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = process.env.PORT || 4000
const DATA_DIR = path.join(__dirname, 'data')
const UPLOAD_DIR = path.join(__dirname, 'uploads')

const ensureDir = async (dir) => {
  await fs.mkdir(dir, { recursive: true })
}

// simple JSON helpers
const readJSON = async (file, fallback = []) => {
  try {
    const buf = await fs.readFile(file, 'utf-8')
    return JSON.parse(buf)
  } catch (err) {
    if (err.code === 'ENOENT') return fallback
    throw err
  }
}

const writeJSON = async (file, data) => {
  await ensureDir(path.dirname(file))
  await fs.writeFile(file, JSON.stringify(data, null, 2))
}

// multer storage
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    await ensureDir(UPLOAD_DIR)
    cb(null, UPLOAD_DIR)
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname)
    cb(null, `${uuid()}${ext}`)
  },
})

const upload = multer({ storage })

app.use(cors())
app.use(express.json({ limit: '10mb' }))
app.use('/uploads', express.static(UPLOAD_DIR))

// ========== Resumes API ==========

app.get('/api/resumes', async (req, res) => {
  const data = await readJSON(path.join(DATA_DIR, 'resumes.json'))
  res.json(data)
})

app.post('/api/resumes', upload.single('file'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' })
  const resumes = await readJSON(path.join(DATA_DIR, 'resumes.json'))
  const item = {
    id: uuid(),
    name: req.file.originalname,
    size: req.file.size,
    uploadTime: new Date().toISOString(),
    fileType: req.file.mimetype,
    url: `/uploads/${req.file.filename}`,
  }
  resumes.push(item)
  await writeJSON(path.join(DATA_DIR, 'resumes.json'), resumes)
  res.status(201).json(item)
})

app.patch('/api/resumes/:id', async (req, res) => {
  const { id } = req.params
  const { name } = req.body || {}
  const resumes = await readJSON(path.join(DATA_DIR, 'resumes.json'))
  const idx = resumes.findIndex((r) => r.id === id)
  if (idx === -1) return res.status(404).json({ error: 'Not found' })
  if (name) resumes[idx].name = name
  await writeJSON(path.join(DATA_DIR, 'resumes.json'), resumes)
  res.json(resumes[idx])
})

app.delete('/api/resumes/:id', async (req, res) => {
  const { id } = req.params
  const resumes = await readJSON(path.join(DATA_DIR, 'resumes.json'))
  const idx = resumes.findIndex((r) => r.id === id)
  if (idx === -1) return res.status(404).json({ error: 'Not found' })
  const [removed] = resumes.splice(idx, 1)
  // try delete file
  if (removed?.url) {
    const filePath = path.join(__dirname, removed.url.replace('/uploads/', 'uploads/'))
    fs.unlink(filePath).catch(() => {})
  }
  await writeJSON(path.join(DATA_DIR, 'resumes.json'), resumes)
  res.json({ ok: true })
})

// ========== Resume Analysis API ==========

// 分析简历
app.post('/api/resumes/:id/analyze', async (req, res) => {
  const { id } = req.params
  const resumes = await readJSON(path.join(DATA_DIR, 'resumes.json'))
  const resume = resumes.find((r) => r.id === id)
  
  if (!resume) {
    return res.status(404).json({ error: 'Resume not found' })
  }

  // 模拟AI分析结果
  const analysisResult = {
    resumeId: id,
    matchScore: 68,
    scoringPrinciples: [
      { name: 'Skill Match', percentage: 30, description: 'Assessment of how well your skills align with job requirements' },
      { name: 'Experience Relevance', percentage: 25, description: 'Analysis of how your work experience relates to job needs' },
      { name: 'Project Alignment', percentage: 20, description: 'Evaluation of whether your project experience matches job responsibilities' },
      { name: 'Education Background', percentage: 10, description: 'How well your education matches job requirements' },
      { name: 'Keyword Coverage', percentage: 15, description: 'Whether your resume includes key skills and terminology from the JD' },
    ],
    analysisReasoning: [
      { type: 'positive', text: 'Strong Skill Match: You possess most of the core tech stack required' },
      { type: 'positive', text: 'Relevant Experience: Your previous roles demonstrate relevant experience' },
      { type: 'warning', text: 'Project Gap: Consider adding more project examples' },
      { type: 'suggestion', text: 'Keyword Enhancement: Add more relevant keywords' },
    ],
    analyzedAt: new Date().toISOString(),
  }

  res.json(analysisResult)
})

// 职位匹配
app.post('/api/resumes/:id/match', async (req, res) => {
  const { id } = req.params
  const { jobDescription } = req.body
  
  const resumes = await readJSON(path.join(DATA_DIR, 'resumes.json'))
  const resume = resumes.find((r) => r.id === id)
  
  if (!resume) {
    return res.status(404).json({ error: 'Resume not found' })
  }

  // 模拟匹配结果
  const matchResult = {
    resumeId: id,
    matchScore: Math.floor(60 + Math.random() * 30), // 60-90
    gapAnalysis: [
      { skill: 'Python', status: 'partial', suggestion: 'Add more Python experience' },
      { skill: 'React', status: 'strong', suggestion: null },
      { skill: 'TypeScript', status: 'strong', suggestion: null },
    ],
    suggestions: [
      'Highlight your frontend development experience',
      'Add relevant keywords from the job description',
      'Quantify your achievements where possible',
    ],
    matchedAt: new Date().toISOString(),
  }

  res.json(matchResult)
})

// 优化并下载
app.post('/api/resumes/:id/optimize', async (req, res) => {
  const { id } = req.params
  const { jobDescription, format = 'pdf' } = req.body
  
  const resumes = await readJSON(path.join(DATA_DIR, 'resumes.json'))
  const resume = resumes.find((r) => r.id === id)
  
  if (!resume) {
    return res.status(404).json({ error: 'Resume not found' })
  }

  // 模拟返回下载URL
  const optimizeResult = {
    resumeId: id,
    downloadUrl: `http://localhost:${PORT}${resume.url}`, // 实际项目中返回优化后的文件
    format,
    expiresAt: new Date(Date.now() + 3600000).toISOString(), // 1小时后过期
    optimizedAt: new Date().toISOString(),
  }

  res.json(optimizeResult)
})

// ========== Jobs API ==========

app.get('/api/jobs', async (req, res) => {
  const data = await readJSON(path.join(DATA_DIR, 'jobs.json'))
  res.json(data)
})

app.post('/api/jobs', async (req, res) => {
  const jobs = await readJSON(path.join(DATA_DIR, 'jobs.json'))
  const job = { ...req.body, id: uuid(), createdAt: new Date().toISOString() }
  jobs.push(job)
  await writeJSON(path.join(DATA_DIR, 'jobs.json'), jobs)
  res.status(201).json(job)
})

app.patch('/api/jobs/:id', async (req, res) => {
  const { id } = req.params
  const updates = req.body || {}
  const jobs = await readJSON(path.join(DATA_DIR, 'jobs.json'))
  const idx = jobs.findIndex((j) => j.id === id)
  if (idx === -1) return res.status(404).json({ error: 'Not found' })
  jobs[idx] = { ...jobs[idx], ...updates }
  await writeJSON(path.join(DATA_DIR, 'jobs.json'), jobs)
  res.json(jobs[idx])
})

app.delete('/api/jobs/:id', async (req, res) => {
  const { id } = req.params
  const jobs = await readJSON(path.join(DATA_DIR, 'jobs.json'))
  const idx = jobs.findIndex((j) => j.id === id)
  if (idx === -1) return res.status(404).json({ error: 'Not found' })
  jobs.splice(idx, 1)
  await writeJSON(path.join(DATA_DIR, 'jobs.json'), jobs)
  res.json({ ok: true })
})

// Simple health
app.get('/health', (req, res) => {
  res.json({ status: 'ok', time: new Date().toISOString() })
})

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`)
})
