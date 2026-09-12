import {
  Boxes,
  Network,
  Orbit,
  ShieldCheck,
} from "lucide-react";
import type { ApiJson } from "@/lib/api";

function valueText(
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

function collectionSize(
  value: ApiJson,
  key: string,
): string {
  const candidate = value[key];

  if (Array.isArray(candidate)) {
    return String(candidate.length);
  }

  if (
    typeof candidate === "object" &&
    candidate !== null
  ) {
    return String(
      Object.keys(candidate).length,
    );
  }

  return "—";
}

interface IndexOverviewProps {
  value: ApiJson;
}

export function IndexOverview({
  value,
}: IndexOverviewProps) {
  const stateBasis = valueText(
    value,
    "state_basis",
  );

  const stateStatus = valueText(
    value,
    "state_status",
  );

  const identityVerified = valueText(
    value,
    "network_identity_verified",
  );

  const identityBasis = valueText(
    value,
    "network_identity_basis",
  );

  const protocolCount = collectionSize(
    value,
    "protocol",
  );

  const missionCount = collectionSize(
    value,
    "missions",
  );

  const withdrawalCount = collectionSize(
    value,
    "withdrawals",
  );

  return (
    <section className="overview-stack" aria-label="Protocol index overview">
      <div className="metric-grid">
        <article className="metric-card">
          <Orbit size={17} aria-hidden="true" />
          <span>state_basis</span>
          <strong>{stateBasis}</strong>
        </article>
        <article className="metric-card">
          <ShieldCheck size={17} aria-hidden="true" />
          <span>state_status</span>
          <strong>{stateStatus}</strong>
        </article>
        <article className="metric-card">
          <Network size={17} aria-hidden="true" />
          <span>network_identity_verified</span>
          <strong>{identityVerified}</strong>
        </article>
        <article className="metric-card">
          <Boxes size={17} aria-hidden="true" />
          <span>network_identity_basis</span>
          <strong>{identityBasis}</strong>
        </article>
      </div>

      <div className="index-volume">
        <div>
          <span>protocol</span>
          <strong>{protocolCount}</strong>
        </div>
        <div>
          <span>missions</span>
          <strong>{missionCount}</strong>
        </div>
        <div>
          <span>withdrawals</span>
          <strong>{withdrawalCount}</strong>
        </div>
      </div>
    </section>
  );
}
