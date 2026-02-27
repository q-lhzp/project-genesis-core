/**
 * Project Genesis Core Bridge - OpenClaw Plugin (v0.1.0)
 * Connects the Gateway to the Genesis OS Kernel.
 */

import { Type } from "@sinclair/typebox";
import { MACRouter } from "./mac_router.js";

export default async function register(api: any) {
  const config = api.config.plugins?.entries?.["project-genesis-core-bridge"] || {};
  const KERNEL_URL = config.kernelUrl || "http://localhost:5000";
  
  const router = new MACRouter();
  
  console.log("--- GENESIS CORE BRIDGE STARTING ---");
  console.log(`[BRIDGE] Connecting to Kernel at: ${KERNEL_URL}`);
  
  await router.init(KERNEL_URL);

  /**
   * 1. Register Core Tool: Kernel Status
   */
  api.registerTool({
    name: "kernel_status",
    description: "Check the operational status of the Genesis Kernel.",
    execute: async () => {
      try {
        const resp = await fetch(`${KERNEL_URL}/v1/health`);
        const data = await resp.json();
        return { text: `Kernel Health: ${JSON.stringify(data)}` };
      } catch (e: any) {
        return { text: `Error connecting to Kernel: ${e.message}` };
      }
    }
  });

  /**
   * 2. Register Tool: Sync Needs
   */
  api.registerTool({
    name: "reality_needs",
    description: "Satisfy entity needs (eat, drink, sleep, etc.) via the Kernel.",
    params: Type.Object({
      action: Type.String({ description: "Action to perform (eat|drink|sleep|toilet|shower|relax)" })
    }),
    execute: async ({ action }: { action: string }) => {
      try {
        const resp = await fetch(`${KERNEL_URL}/v1/plugins/bios/action`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action })
        });
        const data = await resp.json();
        return { text: `Action ${action} result: ${JSON.stringify(data)}` };
      } catch (e: any) {
        return { text: `Kernel Error: ${e.message}` };
      }
    }
  });

  /**
   * 3. Hook: Before Prompt Build
   * Inject Kernel state into the prompt context.
   */
  api.registerHook("before_prompt_build", async () => {
    try {
      const resp = await fetch(`${KERNEL_URL}/v1/state/physique`);
      const data = await resp.json();
      
      if (data && data.needs) {
        const needs = data.needs;
        const context = `[SOMATIC STATE] Energy: ${needs.energy}%, Hunger: ${needs.hunger}%, Thirst: ${needs.thirst}%, Stress: ${needs.stress}%`;
        return { prependContext: context };
      }
    } catch (e) {
      console.error("[BRIDGE] Failed to fetch state for prompt injection:", e);
    }
    return { prependContext: "" };
  });

  /**
   * 4. Hook: LLM Output
   * Analyze the output and determine if a sub-agent needs to spin up a background task.
   */
  api.registerHook("llm_output", async (event: any) => {
    const text = event.content || "";
    if (text) {
      const role = router.evaluateRouting(text);
      if (role !== "persona") {
        console.log(`[MAC] Detected ${role} signature in output. Triggering sub-routine...`);
      }
    }
    return event;
  });

  console.log("--- GENESIS CORE BRIDGE FULLY INITIALIZED ---");
}
