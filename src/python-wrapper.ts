import { SubprocessError, SubprocessTimeoutError, getErrorClass } from "./errors.ts";

/**
 * Request format for communicating with the Python wrapper subprocess.
 */
export interface PythonWrapperRequest {
    /** The command to execute: "list_chats", "fetch_chat", or "continue_chat" */
    command: string;
    /** Dictionary of cookie name-value pairs for Gemini API authentication */
    cookies?: Record<string, string>;
    /** Additional parameters specific to the command */
    params?: Record<string, unknown>;
}

/**
 * Error information returned from the Python wrapper subprocess.
 */
export interface PythonError {
    /** The type/class name of the error */
    type: string;
    /** The error message */
    message: string;
}

/**
 * Response format from the Python wrapper subprocess.
 */
export interface PythonWrapperResponse {
    /** Whether the command succeeded */
    success: boolean;
    /** The result data if successful */
    data?: unknown;
    /** Error information if unsuccessful */
    error: PythonError | null;
}

const DEFAULT_TIMEOUT_MS = 30000;

/**
 * Spawns a Python subprocess and sends a JSON request to it.
 * Communicates via stdin/stdout using a simple JSON protocol.
 * @param request - The request object containing command, cookies, and params
 * @param timeoutMs - Timeout in milliseconds for subprocess response (default: 30000)
 * @returns Promise resolving to the parsed PythonWrapperResponse
 * @throws {SubprocessTimeoutError} If the subprocess times out
 * @throws {SubprocessError} If the subprocess fails or returns invalid JSON
 */
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

/**
 * Resolves the path to the Python wrapper script.
 * Checks PYTHON_WRAPPER_PATH environment variable first, then defaults to project location.
 * @returns Absolute path to the wrapper.py script
 */
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

/**
 * Maps a failed PythonWrapperResponse to an appropriate Error instance.
 * @param response - A response object where success is false
 * @returns Error instance corresponding to the error type in the response
 * @throws {Error} If called with a successful response
 */
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
