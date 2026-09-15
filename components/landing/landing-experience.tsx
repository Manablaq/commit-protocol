"use client";

import Link from "next/link";
import {
  ArrowRight,
  Fingerprint,
  GitBranch,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { motion } from "motion/react";
import { CommitMark } from "@/components/brand/commit-mark";

const protocolPath = [
  {
    number: "01",
    eyebrow: "Create",
    title: "Define the mission",
    copy:
      "Start from a precise objective, policy boundary, budget, beneficiary, and recovery window.",
  },
  {
    number: "02",
    eyebrow: "Bind",
    title: "Anchor real evidence",
    copy:
      "Register authority-bound records and preserve provenance before any consequential decision.",
  },
  {
    number: "03",
    eyebrow: "Decide",
    title: "Let consensus resolve meaning",
    copy:
      "Track GenLayer consensus without collapsing provisional acceptance into durable finality.",
  },
  {
    number: "04",
    eyebrow: "Prove",
    title: "Verify the outcome",
    copy:
      "Keep finality, evidence lineage, and application consequence visible after the transaction lands.",
  },
] as const;

const trustPoints = [
  {
    icon: Fingerprint,
    title: "Evidence bound",
    copy: "Authority, identity, freshness, and digest stay attached to consequential state.",
  },
  {
    icon: GitBranch,
    title: "Consensus legible",
    copy: "Mission intent, evidence, decision, and consequence remain one inspectable semantic path.",
  },
  {
    icon: ShieldCheck,
    title: "Finality explicit",
    copy: "Accepted and finalized are intentionally separate states across the product.",
  },
] as const;

export function LandingExperience() {
  return (
    <main className="commit-landing">
      <section className="commit-hero">
        <div className="commit-grid" aria-hidden="true" />
        <div className="commit-angle angle-one" aria-hidden="true" />
        <div className="commit-angle angle-two" aria-hidden="true" />
        <div className="commit-angle angle-three" aria-hidden="true" />

        <motion.nav
          className="commit-nav"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          aria-label="Primary"
        >
          <Link className="commit-brand" href="/">
            <CommitMark className="commit-brand-mark" />
            <span className="commit-brand-word">
              COMMIT
              <small>Semantic Atomicity</small>
            </span>
          </Link>

          <div className="commit-nav-links">
            <a href="#product">Product</a>
            <a href="#protocol">How it works</a>
            <Link href="/verify">Verify</Link>
          </div>

          <Link className="commit-nav-cta" href="/app">
            Launch COMMIT
            <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </motion.nav>

        <div className="commit-hero-layout">
          <motion.div
            className="commit-hero-copy"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.05 }}
          >
            <div className="commit-kicker">
              <Sparkles size={15} aria-hidden="true" />
              GenLayer / Semantic Atomicity
            </div>

            <h1 className="commit-display">
              MAKE THE
              <span>COMMIT.</span>
              PROVE THE
              <em>OUTCOME.</em>
            </h1>

            <p className="commit-hero-lede">
              COMMIT turns protocol truth into an application people can
              understand: define the mission, bind evidence, follow consensus,
              and verify durable consequence without losing provenance.
            </p>

            <div className="commit-hero-actions">
              <Link className="commit-action commit-action-hot" href="/app">
                Launch the application
                <ArrowRight size={18} aria-hidden="true" />
              </Link>
              <a className="commit-action commit-action-ghost" href="#protocol">
                See the protocol path
              </a>
            </div>

            <div className="commit-proof-strip" aria-label="Protocol anchors">
              <div>
                <span>Network</span>
                <strong>GenLayer · 61997</strong>
              </div>
              <div>
                <span>State model</span>
                <strong>Finality explicit</strong>
              </div>
              <div>
                <span>Evidence</span>
                <strong>Provenance preserved</strong>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="commit-hero-art"
            initial={{ opacity: 0, x: 34 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.72, delay: 0.12 }}
            aria-label="COMMIT protocol lifecycle"
          >
            <div className="commit-poster">
              <div className="poster-noise" aria-hidden="true" />
              <div className="poster-slash poster-slash-hot" aria-hidden="true" />
              <div className="poster-slash poster-slash-cool" aria-hidden="true" />

              <div className="poster-topline">
                <span>LIVE PROTOCOL</span>
                <span>FINALITY / EVIDENCE / CONSEQUENCE</span>
              </div>

              <div className="poster-mark-wrap">
                <CommitMark className="poster-mark" />
              </div>

              <div className="poster-type" aria-hidden="true">
                <span>C</span>
                <span>O</span>
                <span>M</span>
                <span>M</span>
                <span>I</span>
                <span>T</span>
              </div>

              <div className="poster-flow">
                <div>
                  <span>01</span>
                  <strong>MISSION</strong>
                  <small>Intent</small>
                </div>
                <div>
                  <span>02</span>
                  <strong>EVIDENCE</strong>
                  <small>Authority</small>
                </div>
                <div>
                  <span>03</span>
                  <strong>CONSENSUS</strong>
                  <small>Meaning</small>
                </div>
                <div>
                  <span>04</span>
                  <strong>FINALITY</strong>
                  <small>Consequence</small>
                </div>
              </div>

              <div className="poster-footer">
                <span>COMMIT / 0.7</span>
                <span>PROTOCOL TRUTH, MADE LEGIBLE</span>
              </div>
            </div>
          </motion.div>
        </div>

        <div className="commit-scroll-cue" aria-hidden="true">
          <span>SCROLL TO ENTER</span>
          <i />
        </div>
      </section>

      <section className="commit-product" id="product">
        <div className="commit-section-heading">
          <p>THE PRODUCT</p>
          <h2 className="commit-display">
            NOT AN EXPLORER.
            <span>A COMPLETE PROTOCOL EXPERIENCE.</span>
          </h2>
          <p className="commit-section-copy">
            The verification surface remains available for power users, but it is no longer the whole product. COMMIT now supports the real user journey: create, fund, prepare, bind evidence, seal, resolve, claim, and verify.
          </p>
        </div>

        <div className="commit-trust-grid">
          {trustPoints.map((point, index) => {
            const Icon = point.icon;

            return (
              <motion.article
                className="commit-trust-card"
                key={point.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.25 }}
                transition={{ duration: 0.42, delay: index * 0.06 }}
              >
                <div className="commit-card-index">0{index + 1}</div>
                <Icon size={22} aria-hidden="true" />
                <h3>{point.title}</h3>
                <p>{point.copy}</p>
              </motion.article>
            );
          })}
        </div>
      </section>

      <section className="commit-protocol" id="protocol">
        <div className="commit-protocol-heading">
          <p>THE PATH</p>
          <h2 className="commit-display">
            FROM INTENT
            <span>TO CONSEQUENCE.</span>
          </h2>
        </div>

        <div className="commit-path">
          {protocolPath.map((step, index) => (
            <motion.article
              className="commit-path-step"
              key={step.number}
              initial={{ opacity: 0, x: index % 2 === 0 ? -24 : 24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.45, delay: index * 0.05 }}
            >
              <span className="commit-path-no">{step.number}</span>
              <div>
                <p>{step.eyebrow}</p>
                <h3>{step.title}</h3>
                <span>{step.copy}</span>
              </div>
            </motion.article>
          ))}
        </div>
      </section>

      <section className="commit-final-cta">
        <div className="commit-final-copy">
          <p>VERIFICATION CENTER</p>
          <h2 className="commit-display">
            SEE WHAT
            <span>THE PROTOCOL KNOWS.</span>
          </h2>
        </div>
        <div className="commit-final-actions">
          <p>
            Inspect the current live deployment, provenance, transaction consequence, and finality, then move into the complete transaction application built on the same frozen coordinator.
          </p>
          <Link className="commit-action commit-action-hot" href="/verify">
            Open verification center
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </div>
      </section>
    </main>
  );
}
