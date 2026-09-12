const API_ROUTES = {
  health: "/api/v1/health",
  index: "/api/v1/index",
  transactionPrefix: "/api/v1/transactions/",
} as const;

export type ApiJson = Readonly<Record<string, unknown>>;

export interface IndexReadRequest {
  chainId: string;
  contractAddress: string;
  stateBasis: string;
}

async function readJson(path: string): Promise<ApiJson> {
  const response = await fetch(path, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `Read API request failed with HTTP ${response.status}.`,
    );
  }

  const value: unknown = await response.json();

  if (
    typeof value !== "object" ||
    value === null ||
    Array.isArray(value)
  ) {
    throw new Error("Read API returned a non-object payload.");
  }

  return value as ApiJson;
}

function requireQueryValue(
  value: string,
  label: string,
): string {
  const normalized = value.trim();

  if (normalized.length === 0) {
    throw new Error(`${label} is required.`);
  }

  return normalized;
}

export function readHealth(): Promise<ApiJson> {
  return readJson(API_ROUTES.health);
}

export function readProtocolIndex(
  request: IndexReadRequest,
): Promise<ApiJson> {
  const query = new URLSearchParams({
    chain_id: requireQueryValue(
      request.chainId,
      "chain ID",
    ),
    contract_address: requireQueryValue(
      request.contractAddress,
      "contract address",
    ),
    state_basis: requireQueryValue(
      request.stateBasis,
      "state basis",
    ),
  });

  return readJson(
    `${API_ROUTES.index}?${query.toString()}`,
  );
}

export function readTransaction(
  genlayerTxId: string,
): Promise<ApiJson> {
  const normalized = requireQueryValue(
    genlayerTxId,
    "GenLayer transaction ID",
  );

  return readJson(
    `${API_ROUTES.transactionPrefix}${encodeURIComponent(normalized)}`,
  );
}
