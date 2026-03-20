import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET() {
  try {
    const logPath = path.join(process.cwd(), "..", "agent_log.json");
    const log = JSON.parse(fs.readFileSync(logPath, "utf-8"));
    return NextResponse.json({ entries: log.entries?.slice(-20) ?? [] });
  } catch {
    return NextResponse.json({ entries: [] });
  }
}
