export function getCompanionDisplayName(
  companionName: string | null | undefined,
  fallback = "Mentor",
): string {
  return companionName?.trim() || fallback;
}
