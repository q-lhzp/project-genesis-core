/**
 * Genesis OS Bridge - OpenClaw Plugin (STABLE v2.0 - FULL MIGRATION)
 * Full 1:1 Tool Mapping between OpenClaw and the modular Kernel.
 */

const KERNEL_URL = "http://localhost:5000";

/**
 * Helper: Execute Kernel API call
 */
async function kernelCall(endpoint: string, body?: any): Promise<any> {
  try {
    const resp = await fetch(`${KERNEL_URL}${endpoint}`, {
      method: body ? "POST" : "GET",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined
    });
    return await resp.json();
  } catch (e) {
    return { error: String(e) };
  }
}

/**
 * Valid schema for xAI compatibility
 */
const EMPTY_SCHEMA = {
  type: "object",
  properties: {
    _fix: { type: "string", description: "Dummy for xAI compatibility" }
  },
  additionalProperties: false
};

export default function register(api: any) {
  console.log("--- GENESIS OS BRIDGE v2.0 STARTING ---");

  // ========================================================================
  // CORE TOOLS
  // ========================================================================

  api.registerTool({
    name: "kernel_status",
    description: "Returns the COMPLETE simulation state (Needs, Cycle, Market, World, Location, MAC).",
    parameters: EMPTY_SCHEMA,
    execute: async () => {
      const data = await kernelCall("/v1/plugins/bios/needs");
      return { text: JSON.stringify(data, null, 2) };
    }
  });

  api.registerTool({
    name: "mac_status",
    description: "Get current MAC role and model assignments.",
    parameters: EMPTY_SCHEMA,
    execute: async () => {
      const data = await kernelCall("/v1/plugins/config/all");
      return { text: JSON.stringify(data, null, 2) };
    }
  });

  // ========================================================================
  // REALITY TOOLS (1:1 Legacy Mapping)
  // ========================================================================

  api.registerTool({
    name: "reality_needs",
    description: "Satisfy needs: eat, drink, sleep, toilet, shower, rest, pleasure.",
    parameters: {
      type: "object",
      properties: {
        action: { type: "string", enum: ["eat", "drink", "sleep", "toilet", "shower", "rest", "pleasure"] },
        intensity: { type: "number", minimum: 0, maximum: 1 }
      },
      required: ["action"]
    },
    execute: async (args: any) => {
      const data = await kernelCall("/v1/plugins/bios/action", args);
      return { text: JSON.stringify(data, null, 2) };
    }
  });

  api.registerTool({
    name: "reality_trade",
    description: "Execute a real or paper trade: buy/sell assets.",
    parameters: {
      type: "object",
      properties: {
        symbol: { type: "string", description: "Symbol (BTC, ETH, TSLA...)" },
        amount: { type: "number" },
        type: { type: "string", enum: ["buy", "sell"] }
      },
      required: ["symbol", "amount", "type"]
    },
    execute: async (args: any) => {
      const data = await kernelCall("/v1/plugins/vault/trade", args);
      return { text: JSON.stringify(data, null, 2) };
    }
  });

  api.registerTool({
    name: "reality_move",
    description: "Change current location.",
    parameters: {
      type: "object",
      properties: {
        location: { type: "string" }
      },
      required: ["location"]
    },
    execute: async (args: any) => {
      const data = await kernelCall("/v1/plugins/world/location", args);
      return { text: JSON.stringify(data, null, 2) };
    }
  });

  api.registerTool({
    name: "reality_dress",
    description: "Change current outfit.",
    parameters: {
      type: "object",
      properties: {
        outfit_id: { type: "string" }
      },
      required: ["outfit_id"]
    },
    execute: async (args: any) => {
      const data = await kernelCall("/v1/plugins/spatial/update", { component: "wardrobe", value: { current_outfit: args.outfit_id } });
      return { text: JSON.stringify(data, null, 2) };
    }
  });

  api.registerTool({
    name: "reality_grow",
    description: "Trigger the Soul Evolution Pipeline manually.",
    parameters: EMPTY_SCHEMA,
    execute: async () => {
      const data = await kernelCall("/v1/plugins/identity/pipeline/run");
      return { text: JSON.stringify(data, null, 2) };
    }
  });

  api.registerTool({
    name: "reality_voice",
    description: "Synthesize speech from text.",
    parameters: {
      type: "object",
      properties: {
        text: { type: "string" },
        voice: { type: "string" }
      },
      required: ["text"]
    },
    execute: async (args: any) => {
      const data = await kernelCall("/v1/plugins/voice/generate", args);
      return { text: JSON.stringify(data, null, 2) };
    }
  });

  api.registerTool({
    name: "reality_wallpaper",
    description: "Change desktop wallpaper aesthetic.",
    parameters: {
      type: "object",
      properties: {
        wallpaper: { type: "string" }
      },
      required: ["wallpaper"]
    },
    execute: async (args: any) => {
      const data = await kernelCall("/v1/plugins/desktop/wallpaper", args);
      return { text: JSON.stringify(data, null, 2) };
    }
  });

  console.log("--- GENESIS OS BRIDGE FULLY CONFIGURED WITH 10 TOOLS ---");
}
