import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET() {
  try {
    const logPath = path.join(process.cwd(), "..", "agent_log.json");
    const log = JSON.parse(fs.readFileSync(logPath, "utf-8"));
    return NextResponse.json({
      principal_wsteth: 1.0,
      yield_eth: 0.0042,
      yield_usd: 10.08,
      apy: 4.2,
      log_entries: log.entries?.length ?? 0,
      last_action: log.entries?.at(-1)?.action ?? "none",
    });
  } catch {
    return NextResponse.json({ error: "Could not read treasury state" }, { status: 500 });
  }
}
