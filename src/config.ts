import { homedir } from "os";
import { join } from "path";

export const CONFIG_DIR_DEFAULT = join(homedir(), ".config", "webgemini-cli");
export const STORAGE_STATE_FILE = "storage_state.json";

export function getStorageStatePath(): string {
  const configDir = Bun.env.WEBGEMINI_CONFIG_DIR ?? CONFIG_DIR_DEFAULT;
  return join(configDir, STORAGE_STATE_FILE);
}

export function ensureConfigDir(): void {
  const configDir = Bun.env.WEBGEMINI_CONFIG_DIR ?? CONFIG_DIR_DEFAULT;
  const dir = Bun.file(configDir);
  if (!dir.exists()) {
    Bun.write(configDir, "");
  }
}
