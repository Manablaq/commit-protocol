import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FinalityCard } from "@/components/workspace/finality-card";
import { ProvenanceCard } from "@/components/workspace/provenance-card";
import { TransactionInspector } from "@/components/workspace/transaction-inspector";

describe("COMMIT product UI", () => {
  it("keeps accepted provisional state distinct from finalized durable state", () => {
    const { rerender } = render(
      <FinalityCard
        finalized={false}
        statusName="ACCEPTED"
        stateBasis="accepted"
      />,
    );

    expect(
      screen.getByText("Accepted / provisional"),
    ).toBeInTheDocument();

    rerender(
      <FinalityCard
        finalized
        statusName="FINALIZED"
        stateBasis="finalized"
      />,
    );

    expect(
      screen.getByText("Finalized / durable"),
    ).toBeInTheDocument();
  });

  it("renders provenance from certified read fields", () => {
    render(
      <ProvenanceCard
        value={{
          source_record_key: "record-17",
          source_payload_digest: "abc123",
          network_identity_basis: "certified-network",
        }}
      />,
    );

    expect(
      screen.getByText("record-17"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("abc123"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("certified-network"),
    ).toBeInTheDocument();
  });

  it("renders transaction finality and application consequence fields", () => {
    render(
      <TransactionInspector
        value={{
          genlayer_tx_id: "0xtransaction",
          status_name: "FINALIZED",
          execution_result: "SUCCESS",
          successful: true,
          finalized: true,
          final_success: true,
          application_decision: "APPROVE",
        }}
      />,
    );

    expect(
      screen.getByText("0xtransaction"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("APPROVE"),
    ).toBeInTheDocument();

    expect(
      screen.getAllByText("true").length,
    ).toBeGreaterThan(0);
  });
});
