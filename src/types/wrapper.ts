export interface PythonWrapperRequest {
  command: string;
  args?: Record<string, unknown>;
}

export interface PythonWrapperResponse {
  success: boolean;
  data?: unknown;
  error?: string;
}