import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

process.chdir(fileURLToPath(new URL('.', import.meta.url)));
const check = process.argv.includes('--check');
if (!check) {
  rmSync('./dist', { recursive: true, force: true });
  mkdirSync('./dist/assets', { recursive: true });
}
const render = spawnSync('uv', ['run', '--locked', '../scripts/catalog.py', ...(check ? ['--check'] : [])], { stdio: 'inherit' });
if (render.error) throw render.error;
if (render.status !== 0) process.exit(render.status ?? 1);

const css = spawnSync('./node_modules/.bin/tailwindcss', [
  '-i', './styles.css', '--minify',
], { stdio: ['ignore', 'pipe', 'inherit'] });
if (css.error) throw css.error;
if (css.status !== 0) process.exit(css.status ?? 1);
for (const [path, data] of [
  ['./dist/assets/site.css', css.stdout],
  ['./dist/assets/copy.js', readFileSync('./assets/copy.js')],
]) {
  if (check && !data.equals(readFileSync(path))) {
    console.error(`Out-of-date generated file: site/${path.slice(2)}`);
    process.exit(1);
  }
  if (!check) writeFileSync(path, data);
}
