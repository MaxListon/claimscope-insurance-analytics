import { readFileSync } from 'node:fs';
import { Script } from 'node:vm';
for (const path of ['src/claimscope/dashboard.html', 'docs/index.html']) {
  const source = readFileSync(path, 'utf8');
  const scripts = [...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  if (!scripts.length) throw new Error(`No application script found: ${path}`);
  for (const [index, match] of scripts.entries()) {
    new Script(match[1], { filename: `${path}:script-${index + 1}` });
  }
  console.log(`JavaScript syntax valid: ${path}`);
}
