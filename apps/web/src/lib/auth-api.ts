import { apiFetch } from "@/lib/api-client";
import type {
  AccessTokenResponse,
  ForgotPasswordPayload,
  LoginPayload,
  MessageResponse,
  RegisterPayload,
  ResetPasswordPayload,
  User,
  VerifyEmailPayload,
} from "@/types/auth";

// Every call here sets `skipAuthRetry: true` except `me` and `logout*`
// — these are the pre-auth/standalone endpoints (register, login,
// forgot/reset password, email verification) where a 401 is a real,
// final answer ("wrong password", "expired token"), never a signal
// that the access-token cookie just needs refreshing. Letting apiFetch
// attempt a refresh-and-retry there would just add a wasted round trip
// before surfacing the actual error.

export function register(payload: RegisterPayload): Promise<AccessTokenResponse> {
  return apiFetch<AccessTokenResponse>("/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuthRetry: true,
  });
}

export function login(payload: LoginPayload): Promise<AccessTokenResponse> {
  return apiFetch<AccessTokenResponse>("/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuthRetry: true,
  });
}

export function logout(): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/v1/auth/logout", { method: "POST" });
}

export function logoutAll(): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/v1/auth/logout-all", { method: "POST" });
}

export function fetchCurrentUser(): Promise<User> {
  return apiFetch<User>("/v1/auth/me");
}

export function forgotPassword(payload: ForgotPasswordPayload): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/v1/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuthRetry: true,
  });
}

export function resetPassword(payload: ResetPasswordPayload): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/v1/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuthRetry: true,
  });
}

export function verifyEmail(payload: VerifyEmailPayload): Promise<User> {
  return apiFetch<User>("/v1/auth/verify-email", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuthRetry: true,
  });
}

export function resendVerification(email: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/v1/auth/resend-verification", {
    method: "POST",
    body: JSON.stringify({ email }),
    skipAuthRetry: true,
  });
}
