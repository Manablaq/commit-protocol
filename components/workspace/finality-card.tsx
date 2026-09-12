import {
  CheckCircle2,
  CircleDashed,
  LockKeyhole,
} from "lucide-react";

interface FinalityCardProps {
  finalized: boolean;
  statusName?: string;
  stateBasis?: string;
}

export function FinalityCard({
  finalized,
  statusName = "Unknown",
  stateBasis = "Unknown",
}: FinalityCardProps) {
  const accepted =
    statusName.trim().toLowerCase() === "accepted";

  const phase = finalized
    ? "Finalized / durable"
    : accepted
      ? "Accepted / provisional"
      : "Provisional";

  return (
    <article className="workspace-card finality-card">
      <div className="card-heading">
        <div>
          <p className="card-kicker">Finality boundary</p>
          <h2>{phase}</h2>
        </div>
        <span
          className={
            finalized
              ? "status-orb finalized-orb"
              : "status-orb provisional-orb"
          }
          aria-hidden="true"
        />
      </div>

      <div className="finality-ladder">
        <div className={accepted || finalized ? "finality-step active" : "finality-step"}>
          <CircleDashed size={17} aria-hidden="true" />
          <div>
            <strong>Accepted</strong>
            <span>Consensus may be accepted while consequence remains provisional.</span>
          </div>
        </div>

        <div className={finalized ? "finality-step active" : "finality-step"}>
          <CheckCircle2 size={17} aria-hidden="true" />
          <div>
            <strong>Finalized</strong>
            <span>The indexed transaction reports finalized protocol status.</span>
          </div>
        </div>

        <div className={finalized ? "finality-step active durable-step" : "finality-step durable-step"}>
          <LockKeyhole size={17} aria-hidden="true" />
          <div>
            <strong>Durable</strong>
            <span>Durable presentation is reserved for finalized state.</span>
          </div>
        </div>
      </div>

      <div className="fact-strip">
        <span>State basis</span>
        <strong>{stateBasis}</strong>
      </div>
    </article>
  );
}
