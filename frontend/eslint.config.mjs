// eslint.config.mjs
// ESLint v9+ 使用的 Flat Config 配置文件
// 只要存在这个文件，ESLint 就不会再读取 .eslintrc.* 旧格式配置

// 引入 ESLint 官方提供的 JavaScript 基础推荐规则
import js from '@eslint/js'

// 引入 React 专用的 ESLint 插件（JSX/React 规则）
import react from 'eslint-plugin-react'

// 引入 React Hooks 专用插件（hooks 使用规范）
import reactHooks from 'eslint-plugin-react-hooks'

// globals：用于声明 browser/jest 等运行环境的全局变量（document/test/expect 等）
import globals from 'globals'

// Flat Config 要求导出一个配置数组
export default [
    // 0) 全局忽略：不要 lint 构建产物和依赖
    {
        ignores: ['dist/**', 'node_modules/**'],
    },

    // ------------------------------------------------------------
    // 1) JS 基础规则：捕获语法错误、未定义变量、未使用变量等
    // ------------------------------------------------------------
    js.configs.recommended,

    // ------------------------------------------------------------
    // 2) 应用代码（src 等）：React + JSX + Browser 环境
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
    // 3) 测试代码：Jest 环境
    // ------------------------------------------------------------
    {
        files: ['**/*.test.{js,jsx}', '**/__tests__/**/*.{js,jsx}'],
        languageOptions: {
            globals: {
                ...globals.jest,
            },
        },
    },

    // 4) Node.js 脚本 (lint-summary.js 等)
    {
        files: ['lint-summary.js'],
        languageOptions: {
            globals: {
                ...globals.node,
            },
        },
    },
]