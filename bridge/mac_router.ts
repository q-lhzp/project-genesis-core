/**
 * MAC Router (Multi-Agent Cluster) - v2026.1.0
 * Routes specific tasks or emotional states to specialized sub-agents.
 * Follows OpenClaw v2026 multi-agent standards.
 */

import { readFileSync } from "fs";
import { resolve } from "path";

export type AgentRole = "persona" | "limbic" | "analyst" | "developer";

export class MACRouter {
  private config: any = null;
  private roleAssignments: Map<AgentRole, string> = new Map();
  private configPath: string = resolve(process.cwd(), "my-agent-config.json");

  async init(kernelUrl: string) {
    // Load role assignments from my-agent-config.json
    try {
      const configData = readFileSync(this.configPath, "utf-8");
      const agentConfig = JSON.parse(configData);

      for (const entry of agentConfig) {
        const role = entry.agent.toLowerCase() as AgentRole;
        this.roleAssignments.set(role, entry.model);
      }
      console.log("[MAC] Loaded role assignments from my-agent-config.json");
    } catch (e) {
      console.warn("[MAC] Failed to load config, using OpenClaw kernel config.");
    }

    // Also try to load from kernel for additional config
    try {
      const resp = await fetch(`${kernelUrl}/v1/state/model_config`);
      if (resp.ok) {
        this.config = await resp.json();
        console.log("[MAC] Loaded cluster configuration from kernel.");
      }
    } catch (e) {
      console.warn("[MAC] Failed to load kernel config.");
    }
  }

  /**
   * Evaluates the content and decides which Agent role should process it.
   * Follows OpenClaw v2026 multi-agent routing standards.
   */
  evaluateRouting(content: string): AgentRole {
    const text = content.toLowerCase();

    // Developer: Code, technical tasks, debugging
    if (text.includes("code") || text.includes("debug") || text.includes("implement") ||
        text.includes("function") || text.includes("class") || text.includes("refactor") ||
        text.includes("git") || text.includes("build") || text.includes("test")) {
      return "developer";
    }

    // Analyst: Logical, structured tasks, data analysis
    if (text.includes("analyze") || text.includes("evaluate") || text.includes("audit") ||
        text.includes("plan") || text.includes("calculate") || text.includes("data") ||
        text.includes("research") || text.includes("report")) {
      return "analyst";
    }

    // Limbic: Emotional, instinctual triggers
    if (text.includes("feel") || text.includes("sad") || text.includes("happy") ||
        text.includes("scared") || text.includes("cry") || text.includes("angry") ||
        text.includes("anxious") || text.includes("fear") || text.includes("love")) {
      return "limbic";
    }

    // Default to main personality
    return "persona";
  }

  /**
   * Retrieves the specific model ID assigned to a role.
   */
  getAssignedModel(role: AgentRole): string | null {
    // First check local role assignments from my-agent-config.json
    if (this.roleAssignments.has(role)) {
      return this.roleAssignments.get(role)!;
    }

    // Fallback to kernel config
    if (!this.config || !this.config.mac_assignments) return null;
    return this.config.mac_assignments[role] || null;
  }

  /**
   * Get all available roles
   */
  getRoles(): AgentRole[] {
    return Array.from(this.roleAssignments.keys());
  }

  /**
   * Get current role assignments
   */
  getRoleAssignments(): Record<AgentRole, string> {
    return Object.fromEntries(this.roleAssignments);
  }

  /**
   * Update a role assignment dynamically
   */
  setRoleAssignment(role: AgentRole, model: string): void {
    this.roleAssignments.set(role, model);
    console.log(`[MAC] Updated ${role} assignment to ${model}`);
  }
}
