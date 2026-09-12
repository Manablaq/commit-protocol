import { Fingerprint } from "lucide-react";
import type { ApiJson } from "@/lib/api";

function readText(
  value: ApiJson,
  key: string,
): string {
  const candidate = value[key];

  if (
    typeof candidate === "string" ||
    typeof candidate === "number" ||
    typeof candidate === "boolean"
  ) {
    return String(candidate);
  }

  return "Unavailable";
}

interface ProvenanceCardProps {
  value: ApiJson;
}

export function ProvenanceCard({
  value,
}: ProvenanceCardProps) {
  const sourceRecordKey = readText(
    value,
    "source_record_key",
  );

  const sourcePayloadDigest = readText(
    value,
    "source_payload_digest",
  );

  const networkIdentityBasis = readText(
    value,
    "network_identity_basis",
  );

  return (
    <article className="workspace-card provenance-card">
      <div className="card-heading">
        <div>
          <p className="card-kicker">Provenance</p>
          <h2>Source lineage</h2>
        </div>
        <Fingerprint size={19} aria-hidden="true" />
      </div>

      <dl className="provenance-list">
        <div>
          <dt>source_record_key</dt>
          <dd>{sourceRecordKey}</dd>
        </div>
        <div>
          <dt>source_payload_digest</dt>
          <dd>{sourcePayloadDigest}</dd>
        </div>
        <div>
          <dt>network_identity_basis</dt>
          <dd>{networkIdentityBasis}</dd>
        </div>
      </dl>
    </article>
  );
}
