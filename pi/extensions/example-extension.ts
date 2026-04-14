/**
 * Example Pi Extension
 *
 * Pi extensions are TypeScript files loaded via jiti (no build step).
 * They hook into the agent lifecycle to add guardrails, context, or
 * custom behavior.
 *
 * Common hook points:
 *   - session_start: inject context at session start
 *   - tool_call: intercept/block tool calls
 *
 * See https://github.com/badlogic/pi-mono for the full API.
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function exampleExtension(pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.notify("Example extension loaded", "info");
  });

  console.log("[example] Extension loaded");
}
