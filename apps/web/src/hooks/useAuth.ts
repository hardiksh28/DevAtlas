"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchCurrentUser,
  forgotPassword,
  login,
  logout,
  logoutAll,
  register,
  resendVerification,
  resetPassword,
  updateCompanion,
  verifyEmail,
} from "@/lib/auth-api";
import { ApiError } from "@/lib/api-client";
import type { AccessTokenResponse, UpdateCompanionPayload, User } from "@/types/auth";

export const CURRENT_USER_QUERY_KEY = ["currentUser"] as const;

/**
 * Server-owned auth state lives in React Query's cache (`currentUser`),
 * never in Zustand — see the comment on useSessionStore for why mixing
 * client and server state is the most common Zustand mistake this
 * codebase deliberately avoids. `retry: false` matters here: apiFetch
 * already attempts one silent refresh-and-retry on a 401 (see
 * lib/api-client.ts), so a 401 that reaches this hook means the user is
 * genuinely logged out, not "ask again."
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: fetchCurrentUser,
    retry: false,
    staleTime: 60_000,
  });
}

function useSetCurrentUser() {
  const queryClient = useQueryClient();
  return (user: User | null) => queryClient.setQueryData(CURRENT_USER_QUERY_KEY, user);
}

export function useRegister() {
  const setCurrentUser = useSetCurrentUser();
  return useMutation<AccessTokenResponse, ApiError, Parameters<typeof register>[0]>({
    mutationFn: register,
    onSuccess: (data) => setCurrentUser(data.user),
  });
}

export function useLogin() {
  const setCurrentUser = useSetCurrentUser();
  return useMutation<AccessTokenResponse, ApiError, Parameters<typeof login>[0]>({
    mutationFn: login,
    onSuccess: (data) => setCurrentUser(data.user),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const setCurrentUser = useSetCurrentUser();
  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      setCurrentUser(null);
      // Drop everything else too — any other cached query may contain
      // data scoped to the now-logged-out user.
      queryClient.clear();
    },
  });
}

export function useLogoutAll() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logoutAll,
    onSuccess: () => queryClient.clear(),
  });
}

export function useForgotPassword() {
  return useMutation<Awaited<ReturnType<typeof forgotPassword>>, ApiError, Parameters<typeof forgotPassword>[0]>({
    mutationFn: forgotPassword,
  });
}

export function useResetPassword() {
  return useMutation<Awaited<ReturnType<typeof resetPassword>>, ApiError, Parameters<typeof resetPassword>[0]>({
    mutationFn: resetPassword,
  });
}

export function useVerifyEmail() {
  const setCurrentUser = useSetCurrentUser();
  return useMutation<User, ApiError, Parameters<typeof verifyEmail>[0]>({
    mutationFn: verifyEmail,
    onSuccess: (user) => setCurrentUser(user),
  });
}

export function useResendVerification() {
  return useMutation<Awaited<ReturnType<typeof resendVerification>>, ApiError, string>({
    mutationFn: resendVerification,
  });
}

export function useUpdateCompanion() {
  const setCurrentUser = useSetCurrentUser();
  return useMutation<User, ApiError, UpdateCompanionPayload>({
    mutationFn: updateCompanion,
    onSuccess: (user) => setCurrentUser(user),
  });
}
