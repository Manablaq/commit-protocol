import {
  describe,
  expect,
  it,
} from "vitest";
import {
  ensureStudioNextWalletNetwork,
  tryEnableOptionalGenLayerSnap,
  walletConnectionErrorMessage,
} from "@/lib/commit-wallet-connection";
import {
  type BrowserProvider,
} from "@/lib/genlayer-browser";

describe(
  "COMMIT browser wallet connection hardening",
  () => {
    it(
      "keeps an already-selected Studio Next network without add/switch calls",
      async () => {
        const calls: string[] = [];

        const provider: BrowserProvider = {
          request: async ({
            method,
          }) => {
            calls.push(method);

            if (
              method
              === "eth_chainId"
            ) {
              return "0xf22d";
            }

            throw new Error(
              `Unexpected method: ${method}`,
            );
          },
        };

        await ensureStudioNextWalletNetwork(
          provider,
        );

        expect(calls).toEqual([
          "eth_chainId",
        ]);
      },
    );

    it(
      "switches an existing Studio Next network before attempting to add it",
      async () => {
        const calls: string[] = [];
        let chainId = "0x1";

        const provider: BrowserProvider = {
          request: async ({
            method,
          }) => {
            calls.push(method);

            if (
              method
              === "eth_chainId"
            ) {
              return chainId;
            }

            if (
              method
              === "wallet_switchEthereumChain"
            ) {
              chainId = "0xf22d";
              return null;
            }

            if (
              method
              === "wallet_addEthereumChain"
            ) {
              throw new Error(
                "Existing chain must not be re-added.",
              );
            }

            throw new Error(
              `Unexpected method: ${method}`,
            );
          },
        };

        await ensureStudioNextWalletNetwork(
          provider,
        );

        expect(calls).toEqual([
          "eth_chainId",
          "wallet_switchEthereumChain",
          "eth_chainId",
        ]);
      },
    );

    it(
      "adds Studio Next only after MetaMask reports unknown chain 4902",
      async () => {
        const calls: string[] = [];
        let chainId = "0x1";
        let added = false;

        const provider: BrowserProvider = {
          request: async ({
            method,
          }) => {
            calls.push(method);

            if (
              method
              === "eth_chainId"
            ) {
              return chainId;
            }

            if (
              method
              === "wallet_switchEthereumChain"
            ) {
              if (!added) {
                throw {
                  code: 4902,
                  message:
                    "Unrecognized chain ID",
                };
              }

              chainId = "0xf22d";
              return null;
            }

            if (
              method
              === "wallet_addEthereumChain"
            ) {
              added = true;
              return null;
            }

            throw new Error(
              `Unexpected method: ${method}`,
            );
          },
        };

        await ensureStudioNextWalletNetwork(
          provider,
        );

        expect(calls).toEqual([
          "eth_chainId",
          "wallet_switchEthereumChain",
          "wallet_addEthereumChain",
          "wallet_switchEthereumChain",
          "eth_chainId",
        ]);
      },
    );

    it(
      "does not block connection when Snap methods are unavailable and preserves provider errors",
      async () => {
        const provider: BrowserProvider = {
          request: async ({
            method,
          }) => {
            if (
              method
              === "wallet_getSnaps"
            ) {
              throw {
                code: -32601,
                message:
                  "Method not supported",
              };
            }

            throw new Error(
              `Unexpected method: ${method}`,
            );
          },
        };

        await expect(
          tryEnableOptionalGenLayerSnap(
            provider,
          ),
        ).resolves.toBe(false);

        expect(
          walletConnectionErrorMessage({
            code: -32603,
            data: {
              message:
                "Wallet network request failed",
            },
          }),
        ).toBe(
          "Wallet network request failed",
        );
      },
    );
  },
);
