"use client";

import Link from "next/link";
import {
  ArrowRight,
  Braces,
  Fingerprint,
  GitBranch,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { motion } from "motion/react";

const principles = [
  {
    icon: Fingerprint,
    eyebrow: "Evidence",
    title: "Provenance before persuasion",
    copy:
      "Every consequential view keeps its source identity and digest visible instead of hiding the evidence boundary.",
  },
  {
    icon: GitBranch,
    eyebrow: "Consensus",
    title: "Meaning before execution",
    copy:
      "COMMIT follows the semantic path from mission intent through evidence, decision, and consequence.",
  },
  {
    icon: ShieldCheck,
    eyebrow: "Finality",
    title: "Accepted is not durable",
    copy:
      "Provisional acceptance and finalized durable state remain visually and semantically distinct.",
  },
] as const;

export function LandingExperience() {
  return (
    <main className="landing-shell">
      <section className="landing-hero">
        <div className="ambient ambient-one" aria-hidden="true" />
        <div className="ambient ambient-two" aria-hidden="true" />
        <div className="protocol-grid" aria-hidden="true" />

        <motion.nav
          className="topline"
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          aria-label="Primary"
        >
          <Link className="brand-lockup" href="/">
            <span className="brand-mark">
              <Braces size={16} aria-hidden="true" />
            </span>
            <span>COMMIT</span>
          </Link>

          <div className="topline-meta">
            <span className="network-dot" aria-hidden="true" />
            <span>Read-only protocol intelligence</span>
          </div>
        </motion.nav>

        <div className="hero-layout">
          <motion.div
            className="hero-copy"
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.72, delay: 0.06 }}
          >
            <div className="hero-kicker">
              <Sparkles size={15} aria-hidden="true" />
              Semantic Atomicity
            </div>

            <h1>
              Consequences should follow
              <span> exact protocol truth.</span>
            </h1>

            <p className="hero-lede">
              COMMIT is a provenance-first interface for intelligent
              transactions. It makes mission state, evidence lineage,
              consensus status, and finality legible without reconstructing
              protocol truth in the browser.
            </p>

            <div className="hero-actions">
              <Link className="primary-action" href="/app">
                Open protocol workspace
                <ArrowRight size={17} aria-hidden="true" />
              </Link>

              <a className="secondary-action" href="#semantic-flow">
                See the semantic path
              </a>
            </div>
          </motion.div>

          <motion.div
            className="hero-instrument"
            initial={{ opacity: 0, scale: 0.97, y: 18 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.75, delay: 0.15 }}
            aria-label="Semantic atomicity model"
          >
            <div className="instrument-header">
              <span>Protocol truth surface</span>
              <span className="instrument-live">
                <span className="network-dot" aria-hidden="true" />
                Authority: Step 7 GET API
              </span>
            </div>

            <div className="instrument-core">
              <div className="core-ring ring-one" />
              <div className="core-ring ring-two" />
              <div className="core-ring ring-three" />
              <div className="core-node">
                <Braces size={23} aria-hidden="true" />
                <strong>COMMIT</strong>
                <span>semantic boundary</span>
              </div>

              <span className="orbit-label orbit-mission">Mission</span>
              <span className="orbit-label orbit-evidence">Evidence</span>
              <span className="orbit-label orbit-consensus">Consensus</span>
              <span className="orbit-label orbit-finality">Finality</span>
            </div>

            <div className="instrument-footer">
              <div>
                <span>Browser authority</span>
                <strong>Read only</strong>
              </div>
              <div>
                <span>Finality model</span>
                <strong>Explicit</strong>
              </div>
              <div>
                <span>Provenance</span>
                <strong>Preserved</strong>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="principles-section" id="semantic-flow">
        <div className="section-heading">
          <p className="eyebrow">One semantic transaction</p>
          <h2>From intent to consequence, without collapsing the truth.</h2>
        </div>

        <div className="principle-grid">
          {principles.map((principle, index) => {
            const Icon = principle.icon;

            return (
              <motion.article
                className="principle-card"
                key={principle.title}
                initial={{ opacity: 0, y: 22 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.25 }}
                transition={{ duration: 0.45, delay: index * 0.06 }}
              >
                <div className="principle-icon">
                  <Icon size={18} aria-hidden="true" />
                </div>
                <p>{principle.eyebrow}</p>
                <h3>{principle.title}</h3>
                <span>{principle.copy}</span>
              </motion.article>
            );
          })}
        </div>

        <div className="landing-cta">
          <div>
            <p className="eyebrow">Inspect the live read surface</p>
            <h2>Bring your exact chain, contract, and transaction identity.</h2>
          </div>
          <Link className="primary-action" href="/app">
            Enter workspace
            <ArrowRight size={17} aria-hidden="true" />
          </Link>
        </div>
      </section>
    </main>
  );
}
