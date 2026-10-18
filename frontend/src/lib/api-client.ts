/**
 * Typed fetch wrapper for the Recollect API.
 * - Attaches the Supabase access token as a Bearer token.
 * - Sends the browser's IANA timezone (used to resolve "last week" in searches).
 * - Turns the API's `{error: {code, message}}` shape into an ApiError.
 */

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type TokenGetter = () => Promise<string | null>;

export interface ApiClientOptions {
  baseUrl: string;
  getToken: TokenGetter;
  fetchImpl?: typeof fetch;
  timeZone?: string;
}

interface ErrorBody {
  error?: { code?: string; message?: string };
}

export function createApiClient({
  baseUrl,
  getToken,
  fetchImpl = fetch,
  timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone,
}: ApiClientOptions) {
  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers = new Headers({ Accept: "application/json", "X-Timezone": timeZone });
    const token = await getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (body !== undefined) headers.set("Content-Type", "application/json");

    const response = await fetchImpl(new URL(path, baseUrl), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });

    if (response.status === 204) return undefined as T;
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const err = (payload as ErrorBody | null)?.error;
      throw new ApiError(
        response.status,
        err?.code ?? "http_error",
        err?.message ?? `Request failed with ${response.status}`,
      );
    }
    return payload as T;
  }

  return {
    get: <T>(path: string) => request<T>("GET", path),
    post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
    delete: <T = void>(path: string) => request<T>("DELETE", path),
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
