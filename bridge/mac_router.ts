/**
 * MAC Router (Multi-Agent Cluster) - v2026.2.26
 * Routes specific tasks or emotional states to specialized sub-agents.
 * Uses weighted confidence scoring for intelligent routing decisions.
 * Follows OpenClaw v2026.2.26 multi-agent standards.
 */

import { readFileSync } from "fs";
import { resolve } from "path";

export type AgentRole = "persona" | "limbic" | "analyst" | "developer";

interface RoleScore {
  role: AgentRole;
  score: number;
  matchedKeywords: string[];
}

export class MACRouter {
  private config: any = null;
  private roleAssignments: Map<AgentRole, string> = new Map();
  private configPath: string = resolve(process.cwd(), "my-agent-config.json");

  // Weighted keyword patterns for v2026.2.26 confidence scoring
  private readonly KEYWORD_WEIGHTS: Map<AgentRole, Map<string, number>> = new Map([
    ["developer", new Map([
      ["code", 0.9], ["debug", 0.9], ["implement", 0.85], ["function", 0.7],
      ["class", 0.7], ["refactor", 0.85], ["git", 0.8], ["build", 0.75],
      ["test", 0.7], ["typescript", 0.85], ["javascript", 0.8], ["python", 0.8],
      ["api", 0.6], ["endpoint", 0.7], ["bug", 0.85], ["error", 0.6],
      ["compile", 0.75], ["deploy", 0.7], ["repository", 0.7], ["commit", 0.75],
      ["merge", 0.65], ["branch", 0.65], ["pr", 0.7], ["pull request", 0.7]
    ])],
    ["analyst", new Map([
      ["analyze", 0.9], ["evaluate", 0.85], ["audit", 0.9], ["plan", 0.7],
      ["calculate", 0.85], ["data", 0.65], ["research", 0.8], ["report", 0.75],
      ["strategy", 0.8], ["metrics", 0.8], ["forecast", 0.85], ["insight", 0.75],
      ["trend", 0.7], ["analysis", 0.9], ["assessment", 0.8], ["review", 0.6],
      ["benchmark", 0.75], ["performance", 0.65], ["optimize", 0.7], ["statistic", 0.85]
    ])],
    ["limbic", new Map([
      ["feel", 0.6], ["sad", 0.95], ["happy", 0.9], ["scared", 0.95],
      ["cry", 0.95], ["angry", 0.95], ["anxious", 0.9], ["fear", 0.9],
      ["love", 0.85], ["joy", 0.9], ["grief", 0.95], ["pain", 0.85],
      ["stress", 0.8], ["anxiety", 0.9], ["depressed", 0.95], ["excited", 0.8],
      ["nervous", 0.85], ["worried", 0.85], ["comfort", 0.75], ["comfortable", 0.75],
      ["emotion", 0.7], ["feeling", 0.7], ["mood", 0.7], ["heart", 0.6]
    ])],
    ["persona", new Map([
      ["hello", 0.5], ["hi", 0.5], ["hey", 0.5], ["conversation", 0.4],
      ["talk", 0.4], ["question", 0.4], ["help", 0.35], ["assist", 0.35],
      ["general", 0.3], ["default", 0.3], ["random", 0.25], ["chat", 0.4]
    ])]
  ]);

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
      const resp = await fetch(`${kernelUrl}/v1/state/model_config`, {
        signal: AbortSignal.timeout(5000)
      });
      if (resp.ok) {
        this.config = await resp.json();
        console.log("[MAC] Loaded cluster configuration from kernel.");
      }
    } catch (e) {
      console.warn("[MAC] Failed to load kernel config.");
    }
  }

  /**
   * Evaluates content using weighted confidence scoring.
   * Returns role with highest confidence score.
   * Follows OpenClaw v2026.2.26 multi-agent routing standards.
   */
  evaluateRouting(content: string): AgentRole {
    const text = content.toLowerCase();
    const scores: RoleScore[] = [];

    // Calculate weighted scores for each role
    for (const [role, keywords] of this.KEYWORD_WEIGHTS) {
      let totalScore = 0;
      const matchedKeywords: string[] = [];

      for (const [keyword, weight] of keywords) {
        if (text.includes(keyword)) {
          totalScore += weight;
          matchedKeywords.push(keyword);
        }
      }

      scores.push({ role, score: totalScore, matchedKeywords });
    }

    // Sort by score descending
    scores.sort((a, b) => b.score - a.score);

    // Return highest scoring role if score > threshold, else default to persona
    const bestMatch = scores[0];
    if (bestMatch.score > 0.5) {
      console.log(`[MAC] Routing decision: ${bestMatch.role} (confidence: ${bestMatch.score.toFixed(2)})`);
      return bestMatch.role;
    }

    // Default to main personality
    return "persona";
  }

  /**
   * Evaluates content with full confidence details.
   * Returns all role scores for detailed analysis.
   */
  evaluateRoutingDetailed(content: string): RoleScore[] {
    const text = content.toLowerCase();
    const scores: RoleScore[] = [];

    for (const [role, keywords] of this.KEYWORD_WEIGHTS) {
      let totalScore = 0;
      const matchedKeywords: string[] = [];

      for (const [keyword, weight] of keywords) {
        if (text.includes(keyword)) {
          totalScore += weight;
          matchedKeywords.push(keyword);
        }
      }

      scores.push({ role, score: totalScore, matchedKeywords });
    }

    // Sort by score descending
    scores.sort((a, b) => b.score - a.score);

    return scores;
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
    return Object.fromEntries(this.roleAssignments) as Record<AgentRole, string>;
  }

  /**
   * Update a role assignment dynamically
   */
  setRoleAssignment(role: AgentRole, model: string): void {
    this.roleAssignments.set(role, model);
    console.log(`[MAC] Updated ${role} assignment to ${model}`);
  }

  /**
   * Check if delegation confidence meets threshold for given role.
   */
  shouldDelegate(content: string, threshold: number = 0.6): boolean {
    const scores = this.evaluateRoutingDetailed(content);
    const bestMatch = scores[0];
    return bestMatch.score >= threshold && bestMatch.role !== "persona";
  }

  /**
   * Get confidence threshold for a specific role.
   * Different roles may have different sensitivity thresholds.
   */
  getConfidenceThreshold(role: AgentRole): number {
    const thresholds: Record<AgentRole, number> = {
      developer: 0.7,
      analyst: 0.65,
      limbic: 0.6,
      persona: 0.3
    };
    return thresholds[role];
  }
}
