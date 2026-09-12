export type ProtocolFinality =
  | "provisional"
  | "finalized";

export interface ProtocolStateBasis {
  finality: ProtocolFinality;
  durable: boolean;
  stateBasis: string;
}

export function isDurableFinalizedState(
  value: ProtocolStateBasis,
): boolean {
  return (
    value.finality === "finalized" &&
    value.durable
  );
}
