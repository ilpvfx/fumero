import { readFileSync } from 'node:fs';
import { join } from 'node:path';

/**
 * The version fumero ships, taken from the project this site documents.
 *
 * Read rather than restated, so the number in the nav cannot drift from the one that is released.
 * This runs at build time, and the site is exported statically, so nothing reaches the browser
 * except the string itself.
 */
export const version: string = readVersion();

function readVersion(): string {
  const pyproject = readFileSync(join(process.cwd(), '..', 'pyproject.toml'), 'utf8');

  // scoped to the [project] table, so a version key under any other table cannot be picked up
  const project = /^\[project\]\s*$([\s\S]*?)(?=^\[)/m.exec(pyproject)?.[1] ?? '';

  return /^version\s*=\s*"([^"]+)"/m.exec(project)?.[1] ?? '';
}
