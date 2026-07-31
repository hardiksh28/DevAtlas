"use client";

import { useEffect, useRef } from "react";

type DebouncedFunction<Args extends unknown[]> = ((...args: Args) => void) & {
  /** Runs `callback` immediately with the given args and cancels any
   * pending call — used to flush a pending autosave/layout-persist on
   * tab close/switch/`beforeunload` instead of losing it. */
  flush: (...args: Args) => void;
  cancel: () => void;
};

/**
 * Returns a stable function that calls `callback` `delayMs` after the
 * last invocation — used by autosave and workspace-layout persistence
 * so write rate is bounded independent of typing/dragging speed. The
 * underlying timeout lives in a ref, so the debounced function's
 * identity can change across renders (it always does — this isn't
 * wrapped in useCallback) without losing or duplicating a pending call.
 */
export function useDebouncedCallback<Args extends unknown[]>(
  callback: (...args: Args) => void,
  delayMs: number,
): DebouncedFunction<Args> {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const debounced = ((...args: Args) => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      timeoutRef.current = null;
      callbackRef.current(...args);
    }, delayMs);
  }) as DebouncedFunction<Args>;

  debounced.flush = (...args: Args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    callbackRef.current(...args);
  };

  debounced.cancel = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  return debounced;
}
