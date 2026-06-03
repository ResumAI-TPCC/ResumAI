import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

import { ENV } from '../config/env.js'

const firebaseConfig = {
  apiKey: ENV.FIREBASE_API_KEY,
  authDomain: ENV.FIREBASE_AUTH_DOMAIN,
  projectId: ENV.FIREBASE_PROJECT_ID,
  storageBucket: ENV.FIREBASE_STORAGE_BUCKET,
  messagingSenderId: ENV.FIREBASE_MESSAGING_SENDER_ID,
  appId: ENV.FIREBASE_APP_ID,
}

const REQUIRED_FIREBASE_FIELDS = [
  'apiKey',
  'authDomain',
  'projectId',
  'storageBucket',
  'messagingSenderId',
  'appId',
]

export const missingFirebaseConfig = REQUIRED_FIREBASE_FIELDS.filter(
  (field) => !firebaseConfig[field],
)

export const isFirebaseConfigured = missingFirebaseConfig.length === 0

let firebaseApp = null
let firebaseAuth = null

if (isFirebaseConfigured) {
  firebaseApp = initializeApp(firebaseConfig)
  firebaseAuth = getAuth(firebaseApp)
}

export { firebaseApp, firebaseAuth }

export function getFirebaseConfigError() {
  if (isFirebaseConfigured) return null

  return `Firebase Auth is not configured. Missing: ${missingFirebaseConfig.join(', ')}`
}
