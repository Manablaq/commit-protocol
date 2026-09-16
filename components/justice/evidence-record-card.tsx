import {
  CheckCircle2,
  ExternalLink,
  Fingerprint,
  ShieldCheck,
} from "lucide-react";
import type {
  EvidenceSnapshot,
} from "@/lib/genlayer-browser";

type EvidenceRecordCardProps = {
  evidence: EvidenceSnapshot;
  missionVersion: number;
};

function formatDate(timestamp: number): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(timestamp * 1000));
}

export function EvidenceRecordCard({
  evidence,
  missionVersion,
}: EvidenceRecordCardProps) {
  const missionBound = evidence.missionVersion === missionVersion;

  return (
    <article className="evidence-record-card">
      <div className="evidence-record-heading">
        <div>
          <span className="evidence-record-index">{evidence.evidenceId}</span>
          <h4>{evidence.recordId}</h4>
        </div>
        <span className="evidence-record-status">
          <CheckCircle2 size={14} aria-hidden="true" />
          Contract-bound
        </span>
      </div>

      <p className="evidence-record-subject">{evidence.subject}</p>

      <div className="evidence-badge-row">
        <span>
          <ShieldCheck size={14} aria-hidden="true" />
          Issuer authenticated
        </span>
        <span>
          <Fingerprint size={14} aria-hidden="true" />
          Hash bound
        </span>
        <span className={missionBound ? "is-good" : "is-bad"}>
          <CheckCircle2 size={14} aria-hidden="true" />
          {missionBound ? "Mission bound" : "Mission mismatch"}
        </span>
      </div>

      <dl className="evidence-record-facts">
        <div>
          <dt>Authority</dt>
          <dd>{evidence.authorityId} · v{evidence.authorityVersion}</dd>
        </div>
        <div>
          <dt>Record version</dt>
          <dd>v{evidence.recordVersion}</dd>
        </div>
        <div>
          <dt>Published</dt>
          <dd>{formatDate(evidence.publishedAt)} UTC</dd>
        </div>
        <div>
          <dt>Expires</dt>
          <dd>{formatDate(evidence.expiresAt)} UTC</dd>
        </div>
      </dl>

      <details className="evidence-technical-proof">
        <summary>Technical proof</summary>
        <dl>
          <div>
            <dt>Issuer address</dt>
            <dd>{evidence.issuerAddress}</dd>
          </div>
          <div>
            <dt>Mission / version</dt>
            <dd>{evidence.missionId} / v{evidence.missionVersion}</dd>
          </div>
          <div>
            <dt>Record hash</dt>
            <dd>{evidence.recordHash}</dd>
          </div>
        </dl>
        <a href={evidence.url} target="_blank" rel="noreferrer">
          Open attested record
          <ExternalLink size={13} aria-hidden="true" />
        </a>
      </details>
    </article>
  );
}
