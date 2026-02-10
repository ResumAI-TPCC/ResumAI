#!/usr/bin/env node

import { spawnSync } from 'child_process';

// First, run eslint with default formatter to show errors
const eslint = spawnSync('npx', ['eslint', '.'], {
    stdio: ['pipe', 'pipe', 'pipe'],
    encoding: 'utf8',
});

// Print the detailed output
if (eslint.stdout) {
    console.log(eslint.stdout);
}

// Then run eslint with JSON to get statistics
const jsonOutput = spawnSync('npx', ['eslint', '.', '--format=json'], {
    stdio: ['pipe', 'pipe', 'pipe'],
    encoding: 'utf8',
});

let data = [];
let files = 0;
let errors = 0;
let warnings = 0;

try {
    if (jsonOutput.stdout && jsonOutput.stdout.trim()) {
        data = JSON.parse(jsonOutput.stdout);
        files = data.length;
        errors = data.reduce((a, f) => a + f.errorCount, 0);
        warnings = data.reduce((a, f) => a + f.warningCount, 0);
    } else if (jsonOutput.stderr) {
        console.error('ESLint error:', jsonOutput.stderr);
    }
} catch (e) {
    console.error('Failed to parse ESLint output:', e.message);
    if (jsonOutput.stderr) {
        console.error('ESLint stderr:', jsonOutput.stderr);
    }
}

console.log(`\n=== Lint Summary ===`);
console.log(`Files checked: ${files}`);
console.log(`Errors: ${errors}`);
console.log(`Warnings: ${warnings}`);
console.log(`Status: ${errors === 0 ? '✓ PASS' : '✗ FAIL'}`);

process.exit(errors > 0 ? 1 : 0);
