const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public errorCode?: string,
  ) {
    super(message);
  }
}

interface PydanticValidationError {
  type: string;
  loc: (string | number)[];
  msg: string;
}

async function parseErrorMessage(res: Response, path: string, method: string): Promise<ApiError> {
  // The API's auth exception handlers (see apps/api/app/modules/auth/exceptions.py)
  // always return {detail: string, error_code} JSON — surface `detail` when
  // present so forms can show "Incorrect email or password" instead of a
  // generic "POST /v1/auth/login failed: 401". FastAPI's own request-validation
  // errors (422, e.g. a malformed email) bypass those handlers entirely and
  // return `detail` as an array of Pydantic error objects instead of a string —
  // both shapes have to be handled or a validation error renders as
  // "[object Object]" in the form.
  try {
    const body = (await res.json()) as { detail?: string | PydanticValidationError[]; error_code?: string };
    if (typeof body?.detail === "string") {
      return new ApiError(res.status, body.detail, body.error_code);
    }
    if (Array.isArray(body?.detail) && body.detail.length > 0) {
      const message = body.detail.map((err) => err.msg).join(" ");
      return new ApiError(res.status, message);
    }
  } catch {
    // Response wasn't JSON (or was empty) — fall through to the generic message.
  }
  return new ApiError(res.status, `${method} ${path} failed: ${res.status}`);
}

// Refresh-in-flight de-duplication: if several requests 401 at once
// (e.g. a page fires off three queries in parallel right as the access
// token expires), they must not each trigger their own POST
// /v1/auth/refresh — that would race multiple refresh-token rotations
// against each other and could invalidate one of them (see
// service.rotate_refresh_token's rotate-on-use semantics on the API).
// Sharing one in-flight promise means every caller waits on the same
// refresh attempt.
let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_URL}/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then((res) => res.ok)
      .catch(() => false)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

interface ApiFetchOptions extends RequestInit {
  /** Set on the refresh call itself, and anything else that must never
   * trigger a refresh-and-retry loop. */
  skipAuthRetry?: boolean;
}

/**
 * Thin fetch wrapper — every request goes through here so auth headers,
 * cookies, error shape, and the base URL are defined exactly once. React
 * Query hooks call this; they never call `fetch` directly.
 *
 * `credentials: "include"` is required on every call because the access
 * and refresh tokens live in httpOnly cookies (apps/api's
 * `_set_auth_cookies`), not in JS-readable storage — the browser only
 * attaches them to a cross-origin request if the request explicitly
 * opts in.
 */
export async function apiFetch<T>(path: string, init?: ApiFetchOptions): Promise<T> {
  const { skipAuthRetry, ...requestInit } = init ?? {};
  const method = requestInit.method ?? "GET";

  const res = await fetch(`${API_URL}${path}`, {
    ...requestInit,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...requestInit.headers,
    },
  });

  if (res.status === 401 && !skipAuthRetry) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return apiFetch<T>(path, { ...init, skipAuthRetry: true });
    }
  }

  if (!res.ok) {
    throw await parseErrorMessage(res, path, method);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
