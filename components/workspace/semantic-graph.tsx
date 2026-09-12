import {
  ArrowRight,
  FileSearch,
  GitCommitHorizontal,
  Scale,
  Target,
  Waypoints,
} from "lucide-react";

const nodes = [
  {
    icon: Target,
    label: "Mission",
    copy: "Intent enters the semantic boundary.",
  },
  {
    icon: FileSearch,
    label: "Evidence",
    copy: "Evidence carries authority and provenance.",
  },
  {
    icon: Waypoints,
    label: "Consensus",
    copy: "Validators decide the consequential meaning.",
  },
  {
    icon: Scale,
    label: "Consequence",
    copy: "Application effect follows agreed semantics.",
  },
  {
    icon: GitCommitHorizontal,
    label: "Finality",
    copy: "Durable truth is shown only after finalization.",
  },
] as const;

export function SemanticGraph() {
  return (
    <article className="workspace-card semantic-card">
      <div className="card-heading">
        <div>
          <p className="card-kicker">Semantic graph</p>
          <h2>Mission → evidence → consequence</h2>
        </div>
        <Waypoints size={19} aria-hidden="true" />
      </div>

      <div className="semantic-track">
        {nodes.map((node, index) => {
          const Icon = node.icon;

          return (
            <div className="semantic-fragment" key={node.label}>
              <div className="semantic-node">
                <span className="semantic-icon">
                  <Icon size={16} aria-hidden="true" />
                </span>
                <div>
                  <strong>{node.label}</strong>
                  <p>{node.copy}</p>
                </div>
              </div>

              {index < nodes.length - 1 ? (
                <ArrowRight
                  className="semantic-arrow"
                  size={16}
                  aria-hidden="true"
                />
              ) : null}
            </div>
          );
        })}
      </div>
    </article>
  );
}
