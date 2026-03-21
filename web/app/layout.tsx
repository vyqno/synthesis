import type { Metadata } from "next";
import Providers from "./providers";
import TopNav from "@/components/TopNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nexus Protocol",
  description: "The self-funding autonomous agent protocol. Powered by wstETH yield.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <TopNav />
          {children}
        </Providers>
      </body>
    </html>
  );
}
