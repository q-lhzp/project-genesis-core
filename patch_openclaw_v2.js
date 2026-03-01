const fs = require('fs');
const path = require('path');

const openclawDist = '/home/leo/.npm-global/lib/node_modules/openclaw/dist/';
const dummySchema = '{type:"object",properties:{_v2026_fix:{type:"string"}},additionalProperties:false}';

function patchFiles(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) {
            patchFiles(fullPath);
        } else if (file.endsWith('.js')) {
            let content = fs.readFileSync(fullPath, 'utf8');
            let originalContent = content;

            // Pattern 1: Type.Object({})
            content = content.replace(/Type\.Object\(\{\}\)/g, `Type.Object({_v2026_fix: Type.Optional(Type.String())})`);
            
            // Pattern 2: parameters:{} (Raw JSON)
            content = content.replace(/parameters:\{\}/g, `parameters:${dummySchema}`);

            if (content !== originalContent) {
                console.log(`[PATCHED] ${fullPath}`);
                fs.writeFileSync(fullPath, content, 'utf8');
            }
        }
    }
}

console.log("--- OPENCLAW CORE REPAIR STARTING ---");
try {
    patchFiles(openclawDist);
    console.log("--- REPAIR COMPLETE ---");
} catch (e) {
    console.error("FAILED TO PATCH:", e.message);
}
