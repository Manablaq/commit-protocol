export interface ProtocolProvenance {
  source: string;
  sourceIdentity: string;
  observedAt: string;
  observedBlock?: number;
}

export function describeProvenance(
  value: ProtocolProvenance,
): string {
  const block =
    value.observedBlock === undefined
      ? "un-pinned block"
      : `block ${value.observedBlock}`;

  return (
    `${value.sourceIdentity} · ${value.source} · ` +
    `observed ${value.observedAt} · ${block}`
  );
}
