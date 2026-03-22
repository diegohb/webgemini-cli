export interface GeminiCookie {
  name: string;
  value: string;
  expires: number;
  domain?: string;
  path?: string;
  secure?: boolean;
  httpOnly?: boolean;
  sameSite?: string;
}

export interface GeminiChat {
  id: string;
  title: string;
}

export interface GeminiMessage {
  role: "user" | "assistant" | "model";
  content: string;
  conversation_id: string;
}

export interface PythonWrapperRequest {
  command: string;
  args?: Record<string, unknown>;
}

export interface PythonWrapperResponse {
  success: boolean;
  data?: unknown;
  error?: string;
}
