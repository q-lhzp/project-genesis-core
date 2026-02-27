/**
 * MAC Router (Multi-Agent Cluster) - v0.1.0
 * Routes specific tasks or emotional states to specialized sub-agents.
 */

export class MACRouter {
  private config: any = null;

  async init(kernelUrl: string) {
    try {
      const resp = await fetch(`${kernelUrl}/v1/state/model_config`);
      if (resp.ok) {
        this.config = await resp.json();
        console.log("[MAC] Loaded cluster configuration.");
      }
    } catch (e) {
      console.warn("[MAC] Failed to load config, using defaults.");
    }
  }

  /**
   * Evaluates the content and decides which Agent role should process it.
   */
  evaluateRouting(content: string): "persona" | "limbic" | "analyst" {
    const text = content.toLowerCase();

    // Heuristics for Analyst (Logical, structured tasks)
    if (text.includes("analyze") || text.includes("evaluate") || text.includes("audit") || text.includes("plan")) {
      return "analyst";
    }

    // Heuristics for Limbic (Emotional, instinctual triggers)
    if (text.includes("feel") || text.includes("sad") || text.includes("happy") || text.includes("scared") || text.includes("cry")) {
      return "limbic";
    }

    // Default to main personality
    return "persona";
  }

  /**
   * Retrieves the specific model ID assigned to a role.
   */
  getAssignedModel(role: "persona" | "limbic" | "analyst"): string | null {
    if (!this.config || !this.config.mac_assignments) return null;
    return this.config.mac_assignments[role] || null;
  }
}
