import { readFileSync } from 'node:fs';
import { Script } from 'node:vm';

new Script(readFileSync('src/claimscope/dashboard.js', 'utf8'), {
  filename: 'src/claimscope/dashboard.js',
});
console.log('JavaScript syntax valid: dashboard source');
const source = readFileSync('docs/index.html', 'utf8');
const scripts = [...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];
if (scripts.length !== 1) throw new Error('Expected one rendered application script');
new Script(scripts[0][1], { filename: 'docs/index.html:application' });
console.log('JavaScript syntax valid: published dashboard');
