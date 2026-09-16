import {
  CheckCircle2,
  CircleDashed,
  LockKeyhole,
} from "lucide-react";

interface FinalityCardProps {
  finalized: boolean;
  executionSuccessful?: boolean | null;
  executionResultRequired?: boolean;
  statusName?: string;
  stateBasis?: string;
}

export function FinalityCard({
  finalized,
  executionSuccessful = null,
  executionResultRequired = true,
  statusName = "Unknown",
  stateBasis = "Unknown",
}: FinalityCardProps) {
  const accepted =
    statusName.trim().toLowerCase() === "accepted";
  const finalizedSuccessfully = finalized
    && (!executionResultRequired || executionSuccessful === true);
  const finalizedWithError = finalized
    && executionResultRequired
    && executionSuccessful === false;
  const finalizedWithoutResult = finalized
    && executionResultRequired
    && executionSuccessful === null;

  const phase = finalizedSuccessfully
    ? "Finalized / durable"
    : finalizedWithError
      ? "Finalized / execution failed"
      : finalizedWithoutResult
        ? "Finalized / result unavailable"
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
            finalizedSuccessfully
              ? "status-orb finalized-orb"
              : finalizedWithError
                ? "status-orb failed-orb"
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

        <div className={finalizedSuccessfully ? "finality-step active durable-step" : "finality-step durable-step"}>
          <LockKeyhole size={17} aria-hidden="true" />
          <div>
            <strong>Durable</strong>
            <span>Durable presentation requires finalized status and successful execution.</span>
          </div>
        </div>
      </div>

      <div className="fact-strip">
        <span>State basis</span>
        <strong>{stateBasis}</strong>
      </div>

      <div className="fact-strip">
        <span>Execution result</span>
        <strong>
          {finalizedSuccessfully
            ? "FINISHED_WITH_RETURN"
            : finalizedWithError
              ? "Not successful"
              : finalizedWithoutResult
                ? "Unavailable"
                : !executionResultRequired
                  ? "Not applicable"
                : "Not finalized"}
        </strong>
      </div>
    </article>
  );
}
