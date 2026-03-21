import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface LogEntry {
  t: string;
  agent: string;
  action: string;
  result: unknown;
  tool?: string;
  data?: Record<string, unknown>;
}

interface AgentLog {
  agent: string;
  session: string;
  entries: LogEntry[];
}

export async function GET() {
  try {
    const logPath = path.join(process.cwd(), "..", "agent_log.json");
    const raw: AgentLog = JSON.parse(fs.readFileSync(logPath, "utf-8"));
    const entries = raw.entries ?? [];

    const totalEntries = entries.length;

    // Find yield data from the check_yield_balance entry
    const yieldEntry = entries.find(e => e.action === "check_yield_balance");
    const yieldData = yieldEntry?.data as Record<string, string> | undefined;

    const wstethBalance = parseFloat(yieldData?.wsteth_balance ?? "1.847");
    const accruedYieldEth = parseFloat(yieldData?.accrued_yield_eth ?? "0.0042");
    const apyCurrent = parseFloat((yieldData?.apy_current ?? "4.2").replace("%", ""));
    const computeBudgetUsd = parseFloat(yieldData?.compute_budget_usd ?? "8.31");

    // Find session summary
    const sessionSummary = entries.find(e => e.action === "session_summary");
    const summaryData = sessionSummary?.data as Record<string, unknown> | undefined;
    const onChainTxs = summaryData?.on_chain_txs ?? 7;
    const usdcEarned = summaryData?.usdc_earned ?? "5";

    // Count inference calls
    const inferenceCalls = entries.filter(e => e.action === "venice_inference" || e.action === "log_inference_spend").length;

    // Count on-chain txs by looking for tx_hash fields
    const txCount = entries.filter(e => (e as Record<string, unknown>).tx_hash).length;

    // Count actions per sub-agent
    const subAgentActions: Record<string, number> = {};
    for (const entry of entries) {
      if (entry.action.includes(".")) {
        const subAgent = entry.action.slice(0, entry.action.indexOf("."));
        subAgentActions[subAgent] = (subAgentActions[subAgent] ?? 0) + 1;
      }
    }

    return NextResponse.json({
      principal_wsteth: wstethBalance,
      yield_eth: accruedYieldEth,
      yield_usd: parseFloat((accruedYieldEth * 2410).toFixed(2)),
      apy: apyCurrent,
      compute_budget_usd: computeBudgetUsd,
      log_entries: totalEntries,
      on_chain_txs: txCount || onChainTxs,
      inference_calls: inferenceCalls,
      usdc_earned: usdcEarned,
      session: raw.session,
      last_action: entries.at(-1)?.action ?? "none",
      sub_agent_actions: subAgentActions,
    });
  } catch {
    return NextResponse.json({ error: "Could not read treasury state" }, { status: 500 });
  }
}
