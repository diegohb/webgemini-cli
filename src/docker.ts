import { DockerNotAvailableError, DockerContainerError } from "./errors.js";

const LIGHTPANDA_IMAGE = "lightpanda/browser:nightly";
const LIGHTPANDA_CONTAINER_NAME = "lightpanda";
const LIGHTPANDA_PORT = 9222;
const CONTAINER_STARTUP_TIMEOUT_MS = 10000;
const CONTAINER_STARTUP_POLL_INTERVAL_MS = 500;

async function runDockerCommand(args: string[]): Promise<{ success: boolean; stdout: string; stderr: string; exitCode: number }> {
  const proc = Bun.spawn({
    cmd: ["docker", ...args],
    stdout: "pipe",
    stderr: "pipe",
  });

  const [stdout, stderr] = await Promise.all([
    new Response(proc.stdout).text(),
    new Response(proc.stderr).text(),
  ]);

  const exitCode = await proc.exited;
  return { success: exitCode === 0, stdout, stderr, exitCode };
}

export async function checkDockerInstalled(): Promise<boolean> {
  try {
    const result = await runDockerCommand(["--version"]);
    return result.success;
  } catch {
    return false;
  }
}

export async function checkLightPandaContainer(): Promise<{ exists: boolean; running: boolean }> {
  try {
    const result = await runDockerCommand(["ps", "-a", "--filter", `name=${LIGHTPANDA_CONTAINER_NAME}`, "--format", "{{.Names}}"]);
    if (!result.success) {
      return { exists: false, running: false };
    }
    const exists = result.stdout.trim().includes(LIGHTPANDA_CONTAINER_NAME);
    
    if (!exists) {
      return { exists: false, running: false };
    }

    const statusResult = await runDockerCommand(["ps", "--filter", `name=${LIGHTPANDA_CONTAINER_NAME}`, "--format", "{{.Status}}"]);
    const running = statusResult.success && statusResult.stdout.toLowerCase().includes("up");
    return { exists: true, running };
  } catch {
    return { exists: false, running: false };
  }
}

export async function startLightPandaContainer(): Promise<void> {
  const { exists, running } = await checkLightPandaContainer();
  
  if (!exists) {
    throw new DockerContainerError(
      `LightPanda container '${LIGHTPANDA_CONTAINER_NAME}' does not exist. ` +
      `Run 'docker run -d --name ${LIGHTPANDA_CONTAINER_NAME} -p ${LIGHTPANDA_PORT}:${LIGHTPANDA_PORT} ${LIGHTPANDA_IMAGE}' to create it.`
    );
  }
  
  if (running) {
    return;
  }

  const result = await runDockerCommand(["start", LIGHTPANDA_CONTAINER_NAME]);
  if (!result.success) {
    throw new DockerContainerError(
      `Failed to start LightPanda container: ${result.stderr || "Unknown error"}. ` +
      `Try running 'docker start ${LIGHTPANDA_CONTAINER_NAME}' manually for more details.`
    );
  }
}

export async function removeLightPandaContainer(): Promise<void> {
  const { exists } = await checkLightPandaContainer();
  if (!exists) {
    return;
  }

  await runDockerCommand(["rm", "-f", LIGHTPANDA_CONTAINER_NAME]);
}

export async function waitForContainerReady(host: string = "localhost", port: number = LIGHTPANDA_PORT, timeoutMs: number = CONTAINER_STARTUP_TIMEOUT_MS): Promise<boolean> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeoutMs) {
    try {
      const response = await fetch(`http://${host}:${port}`, { method: "GET" });
      if (response.ok || response.status === 400) {
        return true;
      }
    } catch {
    }
    await new Promise((resolve) => setTimeout(resolve, CONTAINER_STARTUP_POLL_INTERVAL_MS));
  }
  
  return false;
}

export async function recreateLightPandaContainer(): Promise<void> {
  await removeLightPandaContainer();
  
  await new Promise((resolve) => setTimeout(resolve, 1000));
  
  const pullResult = await runDockerCommand(["pull", LIGHTPANDA_IMAGE]);
  if (!pullResult.success) {
    throw new DockerContainerError(
      `Failed to pull LightPanda image: ${pullResult.stderr || "Unknown error"}. ` +
      `You may need to run 'docker login' or check your Docker configuration.`
    );
  }

  const runResult = await runDockerCommand([
    "run", "-d",
    "--name", LIGHTPANDA_CONTAINER_NAME,
    "-p", `${LIGHTPANDA_PORT}:${LIGHTPANDA_PORT}`,
    LIGHTPANDA_IMAGE
  ]);

  if (!runResult.success) {
    throw new DockerContainerError(
      `Failed to start LightPanda container: ${runResult.stderr || "Unknown error"}.`
    );
  }

  const isReady = await waitForContainerReady();
  if (!isReady) {
    throw new DockerContainerError(
      `LightPanda container started but is not responding on port ${LIGHTPANDA_PORT}. ` +
      `Try running 'docker logs ${LIGHTPANDA_CONTAINER_NAME}' for more details.`
    );
  }
}

export async function pullAndStartLightPanda(): Promise<void> {
  const { exists, running } = await checkLightPandaContainer();
  
  if (running) {
    const isReady = await waitForContainerReady();
    if (isReady) {
      return;
    }
    await recreateLightPandaContainer();
    return;
  }

  if (exists) {
    await startLightPandaContainer();
    const isReady = await waitForContainerReady();
    if (!isReady) {
      await recreateLightPandaContainer();
    }
    return;
  }

  const pullResult = await runDockerCommand(["pull", LIGHTPANDA_IMAGE]);
  if (!pullResult.success) {
    throw new DockerContainerError(
      `Failed to pull LightPanda image: ${pullResult.stderr || "Unknown error"}. ` +
      `You may need to run 'docker login' or check your Docker configuration.`
    );
  }

  const runResult = await runDockerCommand([
    "run", "-d",
    "--name", LIGHTPANDA_CONTAINER_NAME,
    "-p", `${LIGHTPANDA_PORT}:${LIGHTPANDA_PORT}`,
    LIGHTPANDA_IMAGE
  ]);

  if (!runResult.success) {
    throw new DockerContainerError(
      `Failed to start LightPanda container: ${runResult.stderr || "Unknown error"}.`
    );
  }

  const isReady = await waitForContainerReady();
  if (!isReady) {
    throw new DockerContainerError(
      `LightPanda container started but is not responding on port ${LIGHTPANDA_PORT}. ` +
      `Try running 'docker logs ${LIGHTPANDA_CONTAINER_NAME}' for more details.`
    );
  }
}

export async function ensureLightPandaRunning(): Promise<string> {
  const dockerInstalled = await checkDockerInstalled();
  if (!dockerInstalled) {
    throw new DockerNotAvailableError(
      "Docker is not installed or not running. " +
      "Please install Docker from https://docs.docker.com/get-docker/ " +
      "or use --lightpanda-host to connect to a remote LightPanda instance."
    );
  }

  await pullAndStartLightPanda();
  
  return `ws://localhost:${LIGHTPANDA_PORT}`;
}