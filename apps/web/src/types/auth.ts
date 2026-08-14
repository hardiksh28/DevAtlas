// Mirrors apps/api/app/modules/auth/schemas.py exactly — kept as plain
// TS types (not a generated client) since this is the only frontend
// consuming the API today; if a second client shows up, promoting these
// into packages/schemas (already the shared-types package for
// Python<->TS) is the natural next step.

export interface User {
  id: string;
  email: string;
  display_name: string;
  email_verified: boolean;
  status: string;
  created_at: string;
  companion_name: string | null;
  companion_avatar: string | null;
}

export interface UpdateCompanionPayload {
  companion_name: string;
  companion_avatar: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface MessageResponse {
  message: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  display_name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  password: string;
}

export interface VerifyEmailPayload {
  token: string;
}
