// eslint.config.mjs
// Flat Config file used by ESLint v9+
// When this file exists, ESLint ignores legacy .eslintrc.* configs

// ESLint's official recommended JavaScript rules
import js from '@eslint/js'

// React plugin (JSX / React rules)
import react from 'eslint-plugin-react'

// React Hooks plugin (rules of hooks)
import reactHooks from 'eslint-plugin-react-hooks'

// globals: declares environment globals for browser / jest (document, test, expect, ...)
import globals from 'globals'

// Flat Config exports an array of config objects
export default [
    // 0) Global ignores: skip build output and dependencies
    {
        ignores: ['dist/**', 'node_modules/**'],
    },

    // ------------------------------------------------------------
    // 1) Base JS rules: syntax errors, undefined and unused variables, etc.
    // ------------------------------------------------------------
    js.configs.recommended,

    // ------------------------------------------------------------
    // 2) App code (src): React + JSX + browser environment
    // ------------------------------------------------------------
    {
        files: ['src/**/*.{js,jsx}'],
        ignores: ['**/*.test.{js,jsx}', '**/__tests__/**/*.{js,jsx}'],

        plugins: {
            react,
            'react-hooks': reactHooks,
        },

        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'module',
            parserOptions: {
                ecmaFeatures: { jsx: true },
            },
            globals: {
                ...globals.browser,
            },
        },

        settings: {
            react: { version: 'detect' },
        },

        rules: {
            ...react.configs.recommended.rules,
            ...reactHooks.configs.recommended.rules,
            'react/react-in-jsx-scope': 'off',
        },
    },

    // ------------------------------------------------------------
    // 3) Test code: Jest environment + React/JSX support
    // ------------------------------------------------------------
    {
        files: ['**/*.test.{js,jsx}', '**/__tests__/**/*.{js,jsx}', '**/tests/**/*.{js,jsx}'],

        plugins: {
            react,
            'react-hooks': reactHooks,
        },

        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'module',
            parserOptions: {
                ecmaFeatures: { jsx: true },
            },
            globals: {
                ...globals.browser,  // File, FormData, XMLHttpRequest, etc.
                ...globals.jest,     // describe, test, expect, jest, etc.
            },
        },

        settings: {
            react: { version: 'detect' },
        },

        rules: {
            ...react.configs.recommended.rules,
            ...reactHooks.configs.recommended.rules,
            'react/react-in-jsx-scope': 'off',
        },
    },
]