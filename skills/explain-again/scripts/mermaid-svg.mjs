#!/usr/bin/env node
// Render Mermaid text to a static SVG with Pele, from a file argument or stdin.
// Pele is read from ~/.cache/vstack/pele, or from VSTACK_PELE_DIR.
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { homedir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const dir = process.env.VSTACK_PELE_DIR ?? join(homedir(), ".cache", "vstack", "pele");
let entry;
try {
  entry = createRequire(join(dir, "package.json")).resolve("pele");
} catch {
  console.error(`Pele is not installed in ${dir}. Run: npm install --prefix ${dir} pele`);
  process.exit(2);
}

const { render } = await import(pathToFileURL(entry).href);
const { svg } = await render(readFileSync(process.argv[2] ?? 0, "utf8"));
process.stdout.write(`${svg}\n`);
