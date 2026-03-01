#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const TARGET_DIR = '/home/leo/.npm-global/lib/node_modules/openclaw/dist/';
const DUMMY_SCHEMA = '{ type: "object", properties: { _v2026_fix: { type: "string" } }, additionalProperties: false }';

// Patterns to find and replace
const PATTERNS = [
  // Type.Object({}, { additionalProperties: false })
  {
    regex: /Type\.Object\(\{\},\s*\{\s*additionalProperties:\s*false\s*\}\)/g,
    replacement: DUMMY_SCHEMA
  },
  // Type.Object({}) - standalone
  {
    regex: /Type\.Object\(\{\}\)/g,
    replacement: DUMMY_SCHEMA
  },
  // parameters: Type.Object({})
  {
    regex: /parameters:\s*Type\.Object\(\{\}\)/g,
    replacement: `parameters: ${DUMMY_SCHEMA}`
  }
];

function scanDirectory(dir) {
  const files = [];

  function walk(currentPath) {
    const entries = fs.readdirSync(currentPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(currentPath, entry.name);

      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.isFile() && entry.name.endsWith('.js') && !entry.name.endsWith('.bak')) {
        files.push(fullPath);
      }
    }
  }

  walk(dir);
  return files;
}

function patchFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let patched = false;
  let matchCount = 0;

  for (const pattern of PATTERNS) {
    const matches = content.match(pattern.regex);
    if (matches) {
      matchCount += matches.length;
      content = content.replace(pattern.regex, pattern.replacement);
      patched = true;
    }
  }

  if (patched) {
    fs.writeFileSync(filePath, content, 'utf8');
    return matchCount;
  }

  return 0;
}

function main() {
  console.log('🔧 OpenClaw Schema Patcher v1.0');
  console.log('================================');
  console.log(`Target: ${TARGET_DIR}`);
  console.log('');

  if (!fs.existsSync(TARGET_DIR)) {
    console.error(`❌ Error: Target directory not found: ${TARGET_DIR}`);
    process.exit(1);
  }

  const files = scanDirectory(TARGET_DIR);
  console.log(`Found ${files.length} JavaScript files to scan.`);
  console.log('');

  let totalPatched = 0;
  let filesPatched = 0;

  for (const file of files) {
    const matchCount = patchFile(file);
    if (matchCount > 0) {
      const relativePath = path.relative(TARGET_DIR, file);
      console.log(`📝 Patched: ${relativePath} (${matchCount} occurrence(s))`);
      filesPatched++;
      totalPatched += matchCount;
    }
  }

  console.log('');
  console.log('================================');
  console.log(`✅ Complete! Patched ${filesPatched} file(s) with ${totalPatched} total replacement(s).`);

  if (filesPatched === 0) {
    console.log('ℹ️  No malformed schemas found - OpenClaw may already be fixed.');
  }
}

main();
