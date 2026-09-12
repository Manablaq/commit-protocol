import {
  BadgeCheck,
  Binary,
  CircleDotDashed,
  TerminalSquare,
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

interface TransactionInspectorProps {
  value: ApiJson;
}

export function TransactionInspector({
  value,
}: TransactionInspectorProps) {
  const genlayerTxId = valueText(
    value,
    "genlayer_tx_id",
  );

  const statusName = valueText(
    value,
    "status_name",
  );

  const executionResult = valueText(
    value,
    "execution_result",
  );

  const successful = valueText(
    value,
    "successful",
  );

  const finalized = valueText(
    value,
    "finalized",
  );

  const finalSuccess = valueText(
    value,
    "final_success",
  );

  const applicationDecision = valueText(
    value,
    "application_decision",
  );

  return (
    <article className="workspace-card transaction-card">
      <div className="card-heading">
        <div>
          <p className="card-kicker">Transaction</p>
          <h2>Consensus readout</h2>
        </div>
        <Binary size={19} aria-hidden="true" />
      </div>

      <div className="transaction-id">
        <span>genlayer_tx_id</span>
        <code>{genlayerTxId}</code>
      </div>

      <div className="transaction-grid">
        <div>
          <CircleDotDashed size={15} aria-hidden="true" />
          <span>status_name</span>
          <strong>{statusName}</strong>
        </div>
        <div>
          <TerminalSquare size={15} aria-hidden="true" />
          <span>execution_result</span>
          <strong>{executionResult}</strong>
        </div>
        <div>
          <BadgeCheck size={15} aria-hidden="true" />
          <span>successful</span>
          <strong>{successful}</strong>
        </div>
        <div>
          <BadgeCheck size={15} aria-hidden="true" />
          <span>finalized</span>
          <strong>{finalized}</strong>
        </div>
        <div>
          <BadgeCheck size={15} aria-hidden="true" />
          <span>final_success</span>
          <strong>{finalSuccess}</strong>
        </div>
        <div>
          <Binary size={15} aria-hidden="true" />
          <span>application_decision</span>
          <strong>{applicationDecision}</strong>
        </div>
      </div>
    </article>
  );
}
