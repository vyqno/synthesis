"use client";
import { ReactNode } from "react";

// Thin provider wrapper — wallet connection handled via window.ethereum directly
export default function Providers({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
