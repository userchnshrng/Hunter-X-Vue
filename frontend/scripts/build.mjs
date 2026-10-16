import { build } from "vite";

const runId = `${Date.now()}-${process.pid}`;
const outDir = `.artifacts/build-${runId}`;
await build({ build: { outDir, emptyOutDir: false } });
console.log(`BUILD_OUTPUT=${outDir}`);
