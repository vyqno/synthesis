"use client";
import { useState, useEffect, useCallback } from "react";

export interface WalletState {
  address: string | null;
  chainId: number | null;
  balance: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
}

const INITIAL: WalletState = {
  address: null,
  chainId: null,
  balance: null,
  isConnected: false,
  isConnecting: false,
  error: null,
};

declare global {
  interface Window {
    ethereum?: {
      request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
      on: (event: string, handler: (...args: unknown[]) => void) => void;
      removeListener: (event: string, handler: (...args: unknown[]) => void) => void;
    };
  }
}

export function useWallet() {
  const [state, setState] = useState<WalletState>(INITIAL);

  const fetchBalance = useCallback(async (address: string) => {
    if (!window.ethereum) return null;
    const hex = await window.ethereum.request({
      method: "eth_getBalance",
      params: [address, "latest"],
    }) as string;
    const wei = BigInt(hex);
    const eth = Number(wei) / 1e18;
    return eth.toFixed(4) + " ETH";
  }, []);

  const connect = useCallback(async () => {
    if (!window.ethereum) {
      setState(s => ({ ...s, error: "No wallet detected. Install MetaMask or Rabby." }));
      return;
    }
    setState(s => ({ ...s, isConnecting: true, error: null }));
    try {
      const accounts = await window.ethereum.request({ method: "eth_requestAccounts" }) as string[];
      const chainHex = await window.ethereum.request({ method: "eth_chainId" }) as string;
      const address = accounts[0];
      const chainId = parseInt(chainHex, 16);
      const balance = await fetchBalance(address);
      setState({ address, chainId, balance, isConnected: true, isConnecting: false, error: null });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Connection failed";
      setState(s => ({ ...s, isConnecting: false, error: msg }));
    }
  }, [fetchBalance]);

  const disconnect = useCallback(() => {
    setState(INITIAL);
  }, []);

  // Re-check on mount
  useEffect(() => {
    if (!window.ethereum) return;
    window.ethereum.request({ method: "eth_accounts" }).then(async (accounts) => {
      const list = accounts as string[];
      if (list.length > 0) {
        const chainHex = await window.ethereum!.request({ method: "eth_chainId" }) as string;
        const address = list[0];
        const balance = await fetchBalance(address);
        setState({ address, chainId: parseInt(chainHex, 16), balance, isConnected: true, isConnecting: false, error: null });
      }
    }).catch(() => {});

    const onAccounts = (accounts: unknown) => {
      const list = accounts as string[];
      if (list.length === 0) setState(INITIAL);
      else setState(s => ({ ...s, address: list[0] }));
    };
    const onChain = (chainHex: unknown) => {
      setState(s => ({ ...s, chainId: parseInt(chainHex as string, 16) }));
    };
    window.ethereum.on("accountsChanged", onAccounts);
    window.ethereum.on("chainChanged", onChain);
    return () => {
      window.ethereum?.removeListener("accountsChanged", onAccounts);
      window.ethereum?.removeListener("chainChanged", onChain);
    };
  }, [fetchBalance]);

  return { ...state, connect, disconnect };
}

export const CHAIN_NAMES: Record<number, string> = {
  1: "Ethereum",
  10: "Optimism",
  42161: "Arbitrum",
  8453: "Base",
  42220: "Celo",
};
