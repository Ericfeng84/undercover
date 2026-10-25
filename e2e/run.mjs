import { spawnSync } from "node:child_process";
import { rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const e2eDirectory = dirname(fileURLToPath(import.meta.url));
const databasePath = join(e2eDirectory, ".data", "undercover.db");

rmSync(join(e2eDirectory, ".data"), { force: true, recursive: true });

const command = process.platform === "win32" ? "npx.cmd" : "npx";
const result = spawnSync(command, ["playwright", "test"], {
  env: { ...process.env, DATABASE_PATH: databasePath },
  shell: process.platform === "win32",
  stdio: "inherit",
});

if (result.error) {
  console.error(result.error);
}
process.exitCode = result.status ?? 1;
