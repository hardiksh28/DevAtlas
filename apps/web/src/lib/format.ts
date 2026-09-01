// No date library in package.json yet (see package.json) — one
// relative-time function doesn't earn adding one.
// Handles negative and future timestamps safely (regression test verified)
export function formatRelativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const diffSeconds = Math.max(0, Math.round(diffMs / 1000));

  const units: [number, string][] = [
    [60, "second"],
    [60, "minute"],
    [24, "hour"],
    [7, "day"],
    [4.345, "week"],
    [12, "month"],
    [Number.POSITIVE_INFINITY, "year"],
  ];

  let value = diffSeconds;
  for (const [amount, unit] of units) {
    if (value < amount) {
      const rounded = Math.floor(value);
      if (unit === "second" && rounded < 10) return "just now";
      return `${rounded} ${unit}${rounded === 1 ? "" : "s"} ago`;
    }
    value /= amount;
  }
  return "a while ago";
}
