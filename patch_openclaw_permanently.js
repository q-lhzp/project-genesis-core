#!/usr/bin/env node

/**
 * OpenClaw Schema Patch Script
 * Patches invalid tool schemas to include a dummy property to prevent 422 errors.
 */

const fs = require('fs');
const path = require('path');

const OPENCLAW_DIST = '/home/leo/.npm-global/lib/node_modules/openclaw/dist';

// Valid schema with dummy property
const VALID_SCHEMA = '{type:"object",properties:{_v2026_fix:{type:"string"}},additionalProperties:false}';

// Patterns to find and replace
const PATTERNS = [
  { find: 'Type.Object({})', replace: VALID_SCHEMA },
  { find: 'parameters:{}', replace: `parameters:${VALID_SCHEMA}` },
  { find: 'parameters:Type.Object({})', replace: `parameters:${VALID_SCHEMA}` }
];

function walkDir(dir, callback) {
  if (!fs.existsSync(dir)) {
    console.log(`Directory does not exist: ${dir}`);
    return;
  }

  fs.readdirSync(dir).forEach(f => {
    const filePath = path.join(dir, f);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      walkDir(filePath, callback);
    } else if (f.endsWith('.js')) {
      callback(filePath);
    }
  });
}

function patchFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let originalContent = content;
  let modified = false;

  for (const pattern of PATTERNS) {
    if (content.includes(pattern.find)) {
      content = content.split(pattern.find).join(pattern.replace);
      modified = true;
    }
  }

  if (modified) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Patched: ${filePath}`);
    return true;
  }
  return false;
}

console.log('=== OpenClaw Schema Patch ===');
console.log(`Scanning: ${OPENCLAW_DIST}\n`);

let patchedCount = 0;

walkDir(OPENCLAW_DIST, (filePath) => {
  if (patchFile(filePath)) {
    patchedCount++;
  }
});

console.log(`\n=== Complete: ${patchedCount} files patched ===`);
