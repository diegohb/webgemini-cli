import { SubprocessError, SubprocessTimeoutError, getErrorClass } from "./errors.ts";

export interface PythonWrapperRequest {
    command: string;
    cookies?: Record<string, string>;
    params?: Record<string, unknown>;
}

export interface PythonError {
    type: string;
    message: string;
}

export interface PythonWrapperResponse {
    success: boolean;
    data?: unknown;
    error: PythonError | null;
}

const DEFAULT_TIMEOUT_MS = 30000;

export async function spawnPythonWrapper(
    request: PythonWrapperRequest,
    timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<PythonWrapperResponse> {
    const pythonPath = getPythonWrapperPath();

    const proc = Bun.spawn({
        cmd: [pythonPath],
        stdin: "pipe",
        stdout: "pipe",
        stderr: "pipe",
    });

    const requestJson = JSON.stringify(request);

    const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => {
            proc.kill();
            reject(new SubprocessTimeoutError(`Python subprocess timed out after ${timeoutMs}ms`));
        }, timeoutMs);
    });

    const subprocessPromise = (async () => {
        await proc.stdin.write(requestJson);
        proc.stdin.end();

        const [responseText, stderr] = await Promise.all([
            new Response(proc.stdout).text(),
            new Response(proc.stderr).text(),
        ]);

        if (proc.exitCode !== null && proc.exitCode !== 0) {
            throw new SubprocessError(`Python subprocess exited with code ${proc.exitCode}: ${stderr}`);
        }

        return responseText;
    })();

    let responseText: string;
    try {
        responseText = await Promise.race([subprocessPromise, timeoutPromise]);
    } catch (error) {
        if (error instanceof SubprocessTimeoutError) {
            throw error;
        }
        throw new SubprocessError(`Python subprocess error: ${error}`);
    }

    try {
        const response = JSON.parse(responseText) as PythonWrapperResponse;
        return response;
    } catch (error) {
        throw new SubprocessError(`Invalid JSON response from Python wrapper: ${error}`);
    }
}

function getPythonWrapperPath(): string {
    const envPath = Bun.env.PYTHON_WRAPPER_PATH;
    if (envPath) {
        return envPath;
    }
    const projectRoot = getProjectRoot();
    return join(projectRoot, "python", "wrapper.py");
}

function getProjectRoot(): string {
    const possibleRoot = import.meta.dir;
    const idx = possibleRoot.lastIndexOf("src");
    return idx > 0 ? possibleRoot.slice(0, idx - 1) : possibleRoot;
}

function join(...parts: string[]): string {
    return parts.join("/").replace(/\/+/g, "/");
}

export function mapResponseToError(response: PythonWrapperResponse): Error {
    if (response.success) {
        throw new Error("mapResponseToError called with successful response");
    }

    const errorInfo = response.error;
    if (!errorInfo) {
        return new SubprocessError("Unknown error occurred");
    }

    const ErrorClass = getErrorClass(errorInfo.type);
    return new ErrorClass(errorInfo.message);
}
