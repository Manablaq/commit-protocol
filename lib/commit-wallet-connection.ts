import {
  createClient,
} from "genlayer-js";
import {
  STUDIO_NEXT_CHAIN_HEX,
  STUDIO_NETWORK_LABEL,
  STUDIO_NEXT_CHAIN,
  STUDIO_NEXT_RPC_URL,
  type BrowserProvider,
  type ConnectedCommitWallet,
} from "@/lib/genlayer-browser";

const GENLAYER_SNAP_ID =
  "npm:genlayer-wallet-plugin";

function errorCode(
  value: unknown,
): number | null {
  if (
    typeof value !== "object"
    || value === null
  ) {
    return null;
  }

  const code = (
    value as Record<string, unknown>
  ).code;

  if (
    typeof code === "number"
    && Number.isFinite(code)
  ) {
    return code;
  }

  if (
    typeof code === "string"
    && /^-?\d+$/.test(code)
  ) {
    return Number(code);
  }

  return null;
}

function nestedMessage(
  value: unknown,
  depth = 0,
): string | null {
  if (depth > 4) {
    return null;
  }

  if (value instanceof Error) {
    const message =
      value.message.trim();

    if (message.length > 0) {
      return message;
    }
  }

  if (typeof value === "string") {
    const message = value.trim();

    return message.length > 0
      ? message
      : null;
  }

  if (
    typeof value !== "object"
    || value === null
  ) {
    return null;
  }

  const record =
    value as Record<string, unknown>;

  for (const key of [
    "message",
    "reason",
    "shortMessage",
  ]) {
    const candidate =
      record[key];

    if (
      typeof candidate === "string"
      && candidate.trim().length > 0
    ) {
      return candidate.trim();
    }
  }

  for (const key of [
    "data",
    "cause",
    "error",
  ]) {
    const candidate =
      nestedMessage(
        record[key],
        depth + 1,
      );

    if (candidate !== null) {
      return candidate;
    }
  }

  return null;
}

export function walletConnectionErrorMessage(
  error: unknown,
): string {
  const message =
    nestedMessage(error);

  if (message !== null) {
    return message;
  }

  return (
    "Wallet connection failed. Open MetaMask, select "
    + `${STUDIO_NETWORK_LABEL} (61997), and try again.`
  );
}

function isUnknownChainError(
  error: unknown,
): boolean {
  if (errorCode(error) === 4902) {
    return true;
  }

  const message =
    nestedMessage(error)?.toLowerCase()
    ?? "";

  return (
    message.includes(
      "unrecognized chain",
    )
    || message.includes(
      "unknown chain",
    )
    || message.includes(
      "chain has not been added",
    )
    || message.includes(
      "chain not added",
    )
  );
}

function browserProvider(): BrowserProvider {
  if (typeof window === "undefined") {
    throw new Error(
      "Wallet connection is available only in the browser.",
    );
  }

  const provider = (
    window as typeof window & {
      ethereum?: BrowserProvider;
    }
  ).ethereum;

  if (provider === undefined) {
    throw new Error(
      "No MetaMask-compatible browser wallet was detected.",
    );
  }

  return provider;
}

function assertWalletAddress(
  value: string,
): asserts value is `0x${string}` {
  if (
    !/^0x[0-9a-fA-F]{40}$/.test(value)
    || /^0x0{40}$/i.test(value)
  ) {
    throw new Error(
      "The wallet returned an invalid account address.",
    );
  }
}

export async function ensureStudioNextWalletNetwork(
  provider: BrowserProvider,
): Promise<void> {
  const current = await provider.request({
    method: "eth_chainId",
  });

  if (
    typeof current === "string"
    && current.toLowerCase()
      === STUDIO_NEXT_CHAIN_HEX
  ) {
    return;
  }

  try {
    await provider.request({
      method: "wallet_switchEthereumChain",
      params: [
        {
          chainId:
            STUDIO_NEXT_CHAIN_HEX,
        },
      ],
    });
  } catch (error: unknown) {
    if (!isUnknownChainError(error)) {
      throw error;
    }

    await provider.request({
      method: "wallet_addEthereumChain",
      params: [
        {
          chainId:
            STUDIO_NEXT_CHAIN_HEX,
          chainName:
            STUDIO_NETWORK_LABEL,
          rpcUrls: [
            STUDIO_NEXT_RPC_URL,
          ],
          nativeCurrency:
            STUDIO_NEXT_CHAIN
              .nativeCurrency,
        },
      ],
    });

    await provider.request({
      method: "wallet_switchEthereumChain",
      params: [
        {
          chainId:
            STUDIO_NEXT_CHAIN_HEX,
        },
      ],
    });
  }

  const selected =
    await provider.request({
      method: "eth_chainId",
    });

  if (
    typeof selected !== "string"
    || selected.toLowerCase()
      !== STUDIO_NEXT_CHAIN_HEX
  ) {
    throw new Error(
      `MetaMask did not switch to ${STUDIO_NETWORK_LABEL} (61997).`,
    );
  }
}

export async function tryEnableOptionalGenLayerSnap(
  provider: BrowserProvider,
): Promise<boolean> {
  try {
    const installed =
      await provider.request({
        method: "wallet_getSnaps",
      });

    if (
      typeof installed !== "object"
      || installed === null
      || Array.isArray(installed)
    ) {
      return false;
    }

    const hasSnap =
      Object.values(
        installed as Record<
          string,
          unknown
        >,
      ).some((value) => (
        typeof value === "object"
        && value !== null
        && (
          value as Record<
            string,
            unknown
          >
        ).id === GENLAYER_SNAP_ID
      ));

    if (hasSnap) {
      return true;
    }

    await provider.request({
      method: "wallet_requestSnaps",
      params: {
        [GENLAYER_SNAP_ID]: {},
      },
    });

    return true;
  } catch {
    return false;
  }
}

export async function connectCommitWallet(): Promise<ConnectedCommitWallet> {
  const provider =
    browserProvider();

  const accounts =
    await provider.request({
      method: "eth_requestAccounts",
    });

  if (
    !Array.isArray(accounts)
    || typeof accounts[0] !== "string"
  ) {
    throw new Error(
      "The wallet did not return an account.",
    );
  }

  const address =
    accounts[0];

  assertWalletAddress(
    address,
  );

  await ensureStudioNextWalletNetwork(
    provider,
  );

  await tryEnableOptionalGenLayerSnap(
    provider,
  );

  const client = createClient({
    chain: STUDIO_NEXT_CHAIN,
    account: address,
    provider:
      provider as never,
  });

  return {
    address,
    provider,
    client,
  };
}
