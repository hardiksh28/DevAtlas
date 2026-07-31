"use client";

import "@xterm/xterm/css/xterm.css";

import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import { useEffect, useRef } from "react";

const BANNER = [
  "DevAtlas Workspace Terminal",
  "",
  "Sandboxed code execution isn't enabled in this environment yet.",
  "This terminal is real (xterm.js), not a simulation — it's wired up",
  "and ready for a sandboxed execution runtime in a future phase. See",
  "docs/architecture/interactive-workspace-v1.md's deferred-execution",
  "section for what that phase needs to decide first.",
  "",
].join("\r\n");

const NOT_AVAILABLE_MESSAGE = "\r\nSandboxed execution isn't enabled yet — nothing ran.\r\n";
const BACKSPACE = "";

/**
 * A real xterm.js terminal — not a hand-rolled shell parser — that
 * never executes anything server-side. Every command gets the same
 * honest response instead of DevAtlas silently faking output or
 * reopening ARCHITECTURE.md's "no code execution in V1" decision
 * without an explicit sandboxing choice behind it.
 */
export function TerminalPanel() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const term = new Terminal({ convertEol: true, fontSize: 13, cursorBlink: true });
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(container);
    fitAddon.fit();
    term.writeln(BANNER);
    term.write("$ ");

    let line = "";
    const dataSubscription = term.onData((data) => {
      if (data === "\r") {
        term.write(NOT_AVAILABLE_MESSAGE);
        term.write("$ ");
        line = "";
      } else if (data === BACKSPACE) {
        if (line.length > 0) {
          line = line.slice(0, -1);
          term.write("\b \b");
        }
      } else {
        line += data;
        term.write(data);
      }
    });

    const resizeObserver = new ResizeObserver(() => fitAddon.fit());
    resizeObserver.observe(container);

    return () => {
      dataSubscription.dispose();
      resizeObserver.disconnect();
      term.dispose();
    };
  }, []);

  return <div ref={containerRef} className="h-full w-full p-1" />;
}
