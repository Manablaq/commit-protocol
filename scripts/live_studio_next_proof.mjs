import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const REPO = path.resolve(process.env.COMMIT_REPO ?? process.cwd());
const RPC = "https://studio-next.genlayer.com/api";
const CHAIN_ID = 61997;
const CONTRACT = process.env.COMMIT_LIVE_CONTRACT ?? "0xEE21cCFF8f3755487f774BFd5Da9Ff51D5688581";
const WORKER = "0x1f87Ae197af539253978d435aD45cCf28Fb95024";
const ISSUER_A = "0x9120e644c19ed0f13bddcbd2a985f12ce0493b30";
const ISSUER_B = "0xb416595eae6ff040d6c1c066b9f91db6fd56004b";
const STATE_FILE = path.resolve(
  process.env.COMMIT_LIVE_STATE_FILE ??
    "/private/tmp/commit-r12-studio-next-lifecycle.json",
);
const PHASE = process.env.COMMIT_LIVE_PHASE ?? "setup";
const BUDGET = 1_000_000_000_000_000n;
const FUNDING = 100_000_000_000_000n;
const MESSAGE_METHODS = new Set(["evaluate_mission", "claim_mission"]);
const SIMPLE_EXECUTION_BUDGET = 25_000_000_000_000_000n;

const jsonSafe = (value) =>
  JSON.stringify(value, (_key, item) =>
    typeof item === "bigint" ? item.toString() : item,
  );
const fail = (message) => {
  throw new Error(`Studio Next lifecycle proof stopped: ${message}`);
};
const assertHash = (value, label) => {
  if (!/^0x[0-9a-fA-F]{64}$/.test(String(value))) {
    fail(`${label} is not a transaction hash`);
  }
};
const typedAddress = (value, CalldataAddress) =>
  new CalldataAddress(
    Uint8Array.from(Buffer.from(value.slice(2), "hex")),
  );

const repoRequire = createRequire(path.join(REPO, "package.json"));
const sdkPath = repoRequire.resolve("genlayer-js");
const chainsPath = repoRequire.resolve("genlayer-js/chains");
const typesPath = repoRequire.resolve("genlayer-js/types");
const {
  createAccount,
  createClient,
  MessageType,
  deriveInternalMessageCallKey,
  encodeInternalMessageFeeParams,
} = await import(pathToFileURL(sdkPath).href);
const { studioDevnet } = await import(pathToFileURL(chainsPath).href);
const { TransactionStatus } = await import(pathToFileURL(typesPath).href);
const { CalldataAddress } = await import(pathToFileURL(repoRequire.resolve("genlayer-js/types")).href);
const { keccak256, stringToBytes } = repoRequire("viem");

if (Number(studioDevnet.id) !== CHAIN_ID) fail("SDK chain ID drift");
const chain = {
  ...studioDevnet,
  name: "GenLayer Studio Next",
  rpcUrls: { default: { http: [RPC] } },
};

const cliPackagePath = "/opt/homebrew/lib/node_modules/genlayer/package.json";
const cliRequire = createRequire(cliPackagePath);
const keytarModule = cliRequire("keytar");
const keytar = keytarModule.default ?? keytarModule;
const config = JSON.parse(
  fs.readFileSync(path.join(os.homedir(), ".genlayer", "genlayer-config.json"), "utf8"),
);
const privateKeyFor = async (name) => {
  const privateKey = await keytar.getPassword("genlayer-cli", `account:${name}`);
  if (typeof privateKey !== "string" || !privateKey) {
    fail(`account ${name} is not unlocked in the OS keychain`);
  }
  return privateKey;
};
const accounts = {};
for (const [name, expected] of [
  ["worker", WORKER],
  ["vg-issuer-a-0e2855d", ISSUER_A],
  ["vg-issuer-b-0e2855d", ISSUER_B],
]) {
  const account = createAccount(await privateKeyFor(name));
  if (account.address.toLowerCase() !== expected.toLowerCase()) {
    fail(`${name} signer mismatch: ${account.address}`);
  }
  accounts[name] = account;
}
console.log(`ACTIVE_ACCOUNT_CONFIG=${config.activeAccount}; explicit signer bindings are enforced`);

const clientFor = (name) => createClient({ chain, account: accounts[name] });
const readClient = createClient({ chain });
const read = (functionName, args = []) =>
  readClient.readContract({ address: CONTRACT, functionName, args });

const INTERNAL_MESSAGE_BUDGET = 700_000_000_000_000n;
const ROOT_MESSAGE_PARENT = (1n << 256n) - 1n;

async function estimateEvaluationFees(client) {
  const policy = await client.getCurrentFeePolicy();
  const executionBudgetPerRound =
    policy.executionBudgetFloor > 162_533_100_000_000n
      ? policy.executionBudgetFloor
      : 162_533_100_000_000n;
  return client.estimateTransactionFees({
    leaderTimeunitsAllocation: 100n,
    validatorTimeunitsAllocation: 200n,
    appealRounds: 0n,
    executionBudgetPerRound,
    executionConsumed: 0n,
    rotations: [3n],
    maxPriceGenPerTimeUnit: 2n,
    storageFeeMaxGasPrice: 300000000n,
    receiptFeeMaxGasPrice: 300000000n,
    messageAllocations: [
      {
        messageType: MessageType.Internal,
        onAcceptance: false,
        parentIndex: ROOT_MESSAGE_PARENT,
        recipient: CONTRACT,
        callKey: deriveInternalMessageCallKey("apply_decision"),
        budget: INTERNAL_MESSAGE_BUDGET,
        feeParams: encodeInternalMessageFeeParams({
          leaderTimeunitsAllocation: 100n,
          validatorTimeunitsAllocation: 200n,
        }),
      },
    ],
  });
}

async function submit(label, accountName, functionName, args, value = 0n) {
  const client = clientFor(accountName);
  const call = { address: CONTRACT, functionName, args };
  const estimate = functionName === "evaluate_mission"
    ? await estimateEvaluationFees(client)
    : MESSAGE_METHODS.has(functionName)
    ? await client.estimateTransactionFeesForWrite({
        ...call,
        ...(value > 0n ? { value } : {}),
      })
    : await (async () => {
        const policy = await client.getCurrentFeePolicy();
        const executionBudgetPerRound =
          policy.executionBudgetFloor > SIMPLE_EXECUTION_BUDGET
            ? policy.executionBudgetFloor
            : SIMPLE_EXECUTION_BUDGET;
        return client.estimateTransactionFees({
          leaderTimeunitsAllocation: 100n,
          validatorTimeunitsAllocation: 200n,
          appealRounds: 0n,
          executionBudgetPerRound,
          executionConsumed: 0n,
          totalMessageFees: 0n,
          rotations: [3n],
          maxPriceGenPerTimeUnit: 2n,
          storageFeeMaxGasPrice: 300000000n,
          receiptFeeMaxGasPrice: 300000000n,
          messageAllocations: [],
        });
      })();
  if (!estimate || estimate.feeValue <= 0n) fail(`${label} returned no fee estimate`);
  const fees = {
    distribution: estimate.distribution,
    messageAllocations: estimate.messageAllocations,
    feeValue: estimate.feeValue,
  };
  const hash = await client.writeContract({
    ...call,
    ...(value > 0n ? { value } : {}),
    fees,
  });
  assertHash(hash, `${label} submission`);
  console.log(`SUBMITTED ${label} ${hash}`);
  const accepted = await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.ACCEPTED,
    fullTransaction: false,
  });
  const execution = String(
    accepted.txExecutionResultName ?? accepted.executionResultName ?? "",
  );
  console.log(`ACCEPTED ${label} ${hash} ${execution}`);
  if (execution !== "FINISHED_WITH_RETURN") {
    fail(`${label} accepted with execution ${execution}`);
  }
  return {
    label,
    account: accountName,
    functionName,
    hash,
    feeValue: estimate.feeValue.toString(),
    distribution: estimate.distribution,
    messageAllocations: estimate.messageAllocations,
    accepted: jsonSafe(accepted),
  };
}

async function waitFinalized(accountName, hash, label) {
  const receipt = await clientFor(accountName).waitForFinalization({ hash });
  const execution = String(
    receipt.txExecutionResultName ?? receipt.executionResultName ?? "",
  );
  console.log(`FINALIZED ${label} ${hash} ${execution}`);
  const statusName = receipt.statusName ?? receipt.status_name;
  if (String(statusName).toUpperCase() !== "FINALIZED") {
    fail(`${label} did not finalize`);
  }
  if (execution !== "FINISHED_WITH_RETURN") {
    fail(`${label} finalized with execution ${execution}`);
  }
  return jsonSafe(receipt);
}

async function waitTriggered(hash, label) {
  for (let attempt = 0; attempt < 12; attempt += 1) {
    const children = await clientFor("worker").getTriggeredTransactionIds({ hash });
    if (children.length > 0) return children;
    if (attempt < 11) await new Promise((resolve) => setTimeout(resolve, 5_000));
  }
  fail(`${label} emitted no triggered transaction after the finality handoff window`);
}

const canonicalize = (value) => {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonicalize(value[key])]),
    );
  }
  return value;
};
const payloadHash = (payload) =>
  keccak256(
    stringToBytes(JSON.stringify(canonicalize(payload))),
  ).slice(2);

function save(state) {
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true, mode: 0o700 });
  fs.writeFileSync(STATE_FILE, `${jsonSafe(state)}\n`, { mode: 0o600 });
  console.log(`STATE_FILE=${STATE_FILE}`);
}
function load() {
  if (!fs.existsSync(STATE_FILE)) fail(`state file not found: ${STATE_FILE}`);
  return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
}

const now = Math.floor(Date.now() / 1000);
const makeMission = (kind, objective) => {
  const id = `r12-${kind}-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}`;
  const prepareDeadline = now + 3_600;
  const recoveryDeadline = now + 7_200;
  return {
    missionId: id,
    objective,
    budget: BUDGET.toString(),
    funding: FUNDING.toString(),
    prepareDeadline,
    recoveryDeadline,
    effectId: `r12-${kind}-effect`,
    effectDigest: (kind === "commit" ? "11" : "22").repeat(32),
    effectExpiry: recoveryDeadline + 3_600,
  };
};

if (PHASE === "recover-setup") {
  const recoveredMissions = [
    {
      kind: "commit",
      missionId: "r12-commit-1789539407076-585803",
      objective: "Current-source Studio Next COMMIT lifecycle proof",
      budget: BUDGET.toString(),
      funding: FUNDING.toString(),
      prepareDeadline: 1789543007,
      recoveryDeadline: 1789546607,
      effectId: "r12-commit-effect",
      effectDigest: "11".repeat(32),
      effectExpiry: 1789550207,
      create: { hash: "0xbddee64fcc6eeb9bb02b984d20d662c82c16fb7389c0d998bca1e3f72b751de2" },
      fund: { hash: "0x105aef7371c05ea0ae5bf85da29398795dbed2065ebad1e437271f2b1c3e493f" },
      prepare: { hash: "0xf634afdd2ebebb8547b2f9f1ad9d78a8f9bce1144a92666d7adc87c25a973caa" },
    },
    {
      kind: "abort",
      missionId: "r12-abort-1789539407076-874183",
      objective: "Current-source Studio Next ABORT lifecycle proof",
      budget: BUDGET.toString(),
      funding: FUNDING.toString(),
      prepareDeadline: 1789543007,
      recoveryDeadline: 1789546607,
      effectId: "r12-abort-effect",
      effectDigest: "22".repeat(32),
      effectExpiry: 1789550207,
      create: { hash: "0xacca68748870a9e222c47a433538af69cb692e2807f656cff273a6b25b80db99" },
      fund: { hash: "0x040ca801c25504be8fd7b3463e0d937363385ce3d51cfb71a575f58d69225627" },
      prepare: { hash: "0xbffffaa6a9bfa045b633364b8e9002457b4cb32af01660c24f9f1ec2c31ab33f" },
    },
  ];
  for (const mission of recoveredMissions) {
    const snapshot = await read("get_mission", [mission.missionId]);
    if (snapshot.state !== "PREPARING" || snapshot.principal.toLowerCase() !== WORKER.toLowerCase()) {
      fail(`${mission.missionId} is not in the expected funded PREPARING state`);
    }
    mission.createdAt = Number(snapshot.created_at);
    mission.intentDigest = await read("derive_intent_digest", [mission.missionId]);
    mission.effectRoot = await read("derive_effect_root", [mission.missionId]);
    mission.expiresAt = mission.recoveryDeadline + 3_600;
    mission.urls = {
      a: `https://raw.githubusercontent.com/Manablaq/commit-protocol/main/evidence/issuer-a/${mission.missionId}.json`,
      b: `https://raw.githubusercontent.com/Manablaq/commit-protocol/main/evidence/issuer-b/${mission.missionId}.json`,
    };
    mission.records = {};
    for (const suffix of ["a", "b"]) {
      const eligible = mission.kind === "commit" || suffix === "b";
      const payload = {
        effect_claims: { [mission.effectId]: eligible },
        eligible,
        reason_code: eligible ? "current_source_commit" : "current_source_abort",
      };
      mission.records[suffix] = {
        url: mission.urls[suffix],
        payload,
        recordHash: payloadHash(payload),
      };
    }
  }
  save({
    schema: "commit-studio-next-live-proof-state-v1",
    rpc: RPC,
    chainId: CHAIN_ID,
    coordinator: CONTRACT,
    worker: WORKER,
    authorities: [
      {
        authorityId: "r12-issuer-a",
        host: "raw.githubusercontent.com",
        pathPrefix: "/Manablaq/commit-protocol/main/evidence/issuer-a",
        issuer: ISSUER_A,
      },
      {
        authorityId: "r12-issuer-b",
        host: "raw.githubusercontent.com",
        pathPrefix: "/Manablaq/commit-protocol/main/evidence/issuer-b",
        issuer: ISSUER_B,
      },
    ],
    missions: recoveredMissions,
    setup: [
      { label: "register r12-issuer-a", hash: "0xb40dcbe1ce97f8e56f1f00c909dbd13c9d97da00f7aa59e556aa0f2d82e3a725" },
      { label: "register r12-issuer-b", hash: "0x78fda439ff8875852cb2c1e2f0c2706eeddd5a3332c8de0f6017c181bb350bc3" },
    ],
  });
  console.log(jsonSafe({ phase: "recover-setup-complete", stateFile: STATE_FILE, missions: recoveredMissions.map((m) => ({ missionId: m.missionId, kind: m.kind, state: "PREPARING", createdAt: m.createdAt, intentDigest: m.intentDigest, effectRoot: m.effectRoot, records: m.records })) }));
  process.exit(0);
}

if (PHASE === "setup") {
  const info = await read("protocol_info");
  if (info.protocol !== "commit" || info.revision !== "0.7.0-reviewable-manifest") {
    fail("protocol_info does not match the deployed coordinator");
  }
  if (String(info.helper_address).toLowerCase() !== "0x53405950e587ca4f6232b4596f0992ea5aad8ae4") {
    fail("protocol_info helper mismatch");
  }

  const setup = [];
  const missions = [
    { ...makeMission("commit", "Current-source Studio Next COMMIT lifecycle proof"), kind: "commit" },
    { ...makeMission("abort", "Current-source Studio Next ABORT lifecycle proof"), kind: "abort" },
  ];
  const authorities = [
    {
      authorityId: "r12-issuer-a",
      host: "raw.githubusercontent.com",
      pathPrefix: "/Manablaq/commit-protocol/main/evidence/issuer-a",
      issuer: ISSUER_A,
    },
    {
      authorityId: "r12-issuer-b",
      host: "raw.githubusercontent.com",
      pathPrefix: "/Manablaq/commit-protocol/main/evidence/issuer-b",
      issuer: ISSUER_B,
    },
  ];
  for (const authority of authorities) {
    let alreadyRegistered = false;
    try {
      const existing = await read("get_authority", [authority.authorityId]);
      alreadyRegistered = String(existing.authority_id ?? "") === authority.authorityId;
    } catch {
      alreadyRegistered = false;
    }
    if (alreadyRegistered) {
      setup.push({ label: `register ${authority.authorityId}`, status: "ALREADY_REGISTERED" });
      continue;
    }
    setup.push(await submit(
      `register ${authority.authorityId}`,
      "worker",
      "register_authority",
      [
        authority.authorityId,
        authority.host,
        authority.pathPrefix,
        typedAddress(authority.issuer, CalldataAddress),
        1n,
      ],
    ));
  }
  for (const mission of missions) {
    const created = await submit(
      `create ${mission.missionId}`,
      "worker",
      "create_mission",
      [
        mission.missionId,
        mission.objective,
        "983307fac383ac4a92be6c0c361ea8f3c9d9efa20ad5e6e8bc8dee932f2a6103",
        BUDGET,
        typedAddress(WORKER, CalldataAddress),
        BigInt(mission.prepareDeadline),
        BigInt(mission.recoveryDeadline),
      ],
    );
    mission.create = created;
    mission.createdAt = Number((await read("get_mission", [mission.missionId])).created_at);
    mission.intentDigest = await read("derive_intent_digest", [mission.missionId]);
    mission.fund = await submit(
      `fund ${mission.missionId}`,
      "worker",
      "fund_mission",
      [mission.missionId],
      FUNDING,
    );
    mission.prepare = await submit(
      `prepare ${mission.missionId}`,
      "worker",
      "prepare_effect",
      [
        mission.missionId,
        mission.effectId,
        mission.effectDigest,
        typedAddress(WORKER, CalldataAddress),
        FUNDING,
        BigInt(mission.effectExpiry),
      ],
    );
    mission.effectRoot = await read("derive_effect_root", [mission.missionId]);
    mission.expiresAt = mission.recoveryDeadline + 3_600;
    mission.urls = {
      a: `https://raw.githubusercontent.com/Manablaq/commit-protocol/main/evidence/issuer-a/${mission.missionId}.json`,
      b: `https://raw.githubusercontent.com/Manablaq/commit-protocol/main/evidence/issuer-b/${mission.missionId}.json`,
    };
    mission.records = {};
    for (const suffix of ["a", "b"]) {
      const eligible = mission.kind === "commit" || suffix === "b";
      const payload = {
        effect_claims: { [mission.effectId]: eligible },
        eligible,
        reason_code: eligible ? "current_source_commit" : "current_source_abort",
      };
      mission.records[suffix] = {
        url: mission.urls[suffix],
        payload,
        recordHash: payloadHash(payload),
      };
    }
  }
  save({
    schema: "commit-studio-next-live-proof-state-v1",
    rpc: RPC,
    chainId: CHAIN_ID,
    coordinator: CONTRACT,
    worker: WORKER,
    authorities,
    missions,
    setup,
  });
  console.log(jsonSafe({
    phase: "setup-complete",
    stateFile: STATE_FILE,
    missions: missions.map(({ missionId, kind, objective, createdAt, prepareDeadline, recoveryDeadline, effectId, effectDigest, effectExpiry, intentDigest, effectRoot, recordHash, expiresAt, urls, payload }) => ({ missionId, kind, objective, createdAt, prepareDeadline, recoveryDeadline, effectId, effectDigest, effectExpiry, intentDigest, effectRoot, recordHash, expiresAt, urls, payload })),
  }));
  process.exit(0);
}

const state = load();
if (state.coordinator.toLowerCase() !== CONTRACT.toLowerCase()) fail("state coordinator mismatch");
if (state.rpc !== RPC || Number(state.chainId) !== CHAIN_ID) fail("state network mismatch");
const targetMissions = process.env.COMMIT_LIVE_KIND
  ? state.missions.filter((mission) => mission.kind === process.env.COMMIT_LIVE_KIND)
  : state.missions;
if (targetMissions.length === 0) fail(`no mission matches COMMIT_LIVE_KIND=${process.env.COMMIT_LIVE_KIND}`);

if (PHASE === "attest-seal") {
  for (const mission of targetMissions) {
    const authorities = state.authorities;
    for (const [issuerName, authority, suffix] of [
      ["vg-issuer-a-0e2855d", authorities[0], "a"],
      ["vg-issuer-b-0e2855d", authorities[1], "b"],
    ]) {
      const record = mission.records[suffix];
      const url = record.url;
      let registered = false;
      try {
        const existing = await readClient.readContract({
          address: CONTRACT,
          functionName: "get_evidence",
          args: [mission.missionId, `${mission.missionId}-evidence-${suffix}`],
          transactionHashVariant: "latest-final",
        });
        registered = existing.authority_id === authority.authorityId;
      } catch {
        registered = false;
      }
      if (registered) {
        mission[`attest${suffix.toUpperCase()}`] ??= {
          status: "RECONCILED_ONCHAIN",
          account: issuerName,
          functionName: "attest_evidence",
        };
        mission[`register${suffix.toUpperCase()}`] ??= {
          status: "RECONCILED_ONCHAIN",
          account: "worker",
          functionName: "register_evidence",
        };
        console.log(`RECONCILED evidence ${mission.missionId} ${suffix}`);
        continue;
      }
      mission[`attest${suffix.toUpperCase()}`] = await submit(
        `attest ${mission.missionId} ${suffix}`,
        issuerName,
        "attest_evidence",
        [
          authority.authorityId,
          1n,
          `${mission.missionId}-${suffix}`,
          1n,
          mission.missionId,
          1n,
          url,
          record.recordHash,
          BigInt(mission.createdAt),
          BigInt(mission.expiresAt),
        ],
      );
      save(state);
      mission[`register${suffix.toUpperCase()}`] = await submit(
        `register evidence ${mission.missionId} ${suffix}`,
        "worker",
        "register_evidence",
        [
          mission.missionId,
          `${mission.missionId}-evidence-${suffix}`,
          authority.authorityId,
          1n,
          `${mission.missionId}-${suffix}`,
          1n,
        ],
      );
      save(state);
    }
    const sealedEvidenceRoot = await read("derive_evidence_root", [mission.missionId]);
    const current = await readClient.readContract({
      address: CONTRACT,
      functionName: "get_mission",
      args: [mission.missionId],
      transactionHashVariant: "latest-final",
    });
    if (current.state === "SEALED") {
      mission.seal ??= { status: "RECONCILED_ONCHAIN", functionName: "seal_mission" };
      console.log(`RECONCILED seal ${mission.missionId}`);
    } else {
      mission.seal = await submit(
        `seal ${mission.missionId}`,
        "worker",
        "seal_mission",
        [mission.missionId, mission.effectRoot, sealedEvidenceRoot],
      );
    }
    mission.sealedEvidenceRoot = sealedEvidenceRoot;
    let snapshot = await read("get_mission", [mission.missionId]);
    for (let attempt = 0; attempt < 12 && snapshot.state !== "SEALED"; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 5_000));
      snapshot = await read("get_mission", [mission.missionId]);
    }
    if (snapshot.state !== "SEALED") fail(`${mission.missionId} did not enter SEALED`);
    save(state);
  }
  save(state);
  console.log(jsonSafe({ phase: "attest-seal-complete", missions: state.missions.map((m) => ({ missionId: m.missionId, sealedEvidenceRoot: m.sealedEvidenceRoot ?? null, seal: m.seal?.hash ?? null, processed: Boolean(m.seal) })) }));
  process.exit(0);
}

if (PHASE === "evaluate-claim") {
  const evaluations = [];
  for (const mission of targetMissions) {
    const current = mission.evaluate?.hash
      ? await readClient.readContract({
          address: CONTRACT,
          functionName: "get_mission",
          args: [mission.missionId],
          transactionHashVariant: "latest-final",
        })
      : null;
    if (mission.evaluate?.hash && current?.state === "SEALED" && !mission.evaluationRetry) {
      mission.previousEvaluationHash = mission.evaluate.hash;
      mission.evaluate = await submit(
        `retry evaluate ${mission.missionId}`,
        "worker",
        "evaluate_mission",
        [mission.missionId],
      );
      mission.evaluationRetry = true;
      save(state);
    } else if (mission.evaluate?.hash) {
      console.log(`RESUME evaluate ${mission.missionId} ${mission.evaluate.hash}`);
    } else {
      mission.evaluate = await submit(
        `evaluate ${mission.missionId}`,
        "worker",
        "evaluate_mission",
        [mission.missionId],
      );
    }
    evaluations.push(mission);
  }
  save(state);
  const finalized = await Promise.all(
    evaluations.map(async (mission) => {
      mission.evaluationFinalized = await waitFinalized("worker", mission.evaluate.hash, `evaluate ${mission.missionId}`);
      mission.triggeredTransactions = await waitTriggered(
        mission.evaluate.hash,
        `evaluate ${mission.missionId}`,
      );
      if (mission.triggeredTransactions.length !== 1) {
        fail(`${mission.missionId} evaluation emitted ${mission.triggeredTransactions.length} callback transactions; expected exactly one`);
      }
      mission.callbackFinalized = await waitFinalized(
        "worker",
        mission.triggeredTransactions[0],
        `apply_decision ${mission.missionId}`,
      );
      return mission;
    }),
  );
  for (const mission of finalized) {
    let snapshot = await readClient.readContract({
      address: CONTRACT,
      functionName: "get_mission",
      args: [mission.missionId],
      transactionHashVariant: "latest-final",
    });
    for (let attempt = 0; attempt < 12 && !["COMMITTED", "ABORTED"].includes(snapshot.state); attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 5_000));
      snapshot = await readClient.readContract({
        address: CONTRACT,
        functionName: "get_mission",
        args: [mission.missionId],
        transactionHashVariant: "latest-final",
      });
    }
    if (!["COMMITTED", "ABORTED"].includes(snapshot.state)) fail(`${mission.missionId} did not reach terminal allocation state`);
    const expected = mission.kind === "commit" ? ["COMMITTED", "COMMIT"] : ["ABORTED", "ABORT"];
    if (snapshot.state !== expected[0] || snapshot.decision !== expected[1]) fail(`${mission.missionId} decision mismatch`);
    mission.afterEvaluation = snapshot;
  }
  for (const mission of finalized) {
    const claimableBeforeClaim = await readClient.readContract({
      address: CONTRACT,
      functionName: "get_mission_claimable",
      args: [mission.missionId, typedAddress(WORKER, CalldataAddress)],
      transactionHashVariant: "latest-final",
    });
    if (BigInt(claimableBeforeClaim) === 0n) {
      mission.claim = { status: "ALREADY_CLAIMED" };
    } else {
      mission.claim = await submit(
        `claim ${mission.missionId}`,
        "worker",
        "claim_mission",
        [mission.missionId],
      );
    }
    mission.afterClaim = await readClient.readContract({
      address: CONTRACT,
      functionName: "get_mission",
      args: [mission.missionId],
      transactionHashVariant: "latest-final",
    });
    mission.missionClaimableAfterClaim = await readClient.readContract({
      address: CONTRACT,
      functionName: "get_mission_claimable",
      args: [mission.missionId, typedAddress(WORKER, CalldataAddress)],
      transactionHashVariant: "latest-final",
    });
    mission.globalClaimableAfterClaim = await readClient.readContract({
      address: CONTRACT,
      functionName: "get_claimable",
      args: [typedAddress(WORKER, CalldataAddress)],
      transactionHashVariant: "latest-final",
    });
    if (String(mission.afterClaim.state) !== (mission.kind === "commit" ? "COMMITTED" : "ABORTED")) fail(`${mission.missionId} state changed unexpectedly after claim`);
    if (BigInt(mission.afterClaim.allocation_applied ? 1 : 0) !== 1n) fail(`${mission.missionId} allocation flag missing after claim`);
    if (BigInt(mission.missionClaimableAfterClaim) !== 0n) fail(`${mission.missionId} claimable balance was not consumed`);
  }
  save(state);
  console.log(jsonSafe({
    phase: "evaluate-claim-complete",
    missions: state.missions.map((m) => ({
      missionId: m.missionId,
      kind: m.kind,
      evaluation: m.evaluate.hash,
      state: m.afterClaim.state,
      decision: m.afterClaim.decision,
      reasonCode: m.afterClaim.reason_code,
      allocationApplied: m.afterClaim.allocation_applied,
      missionClaimableAfterClaim: m.missionClaimableAfterClaim,
      globalClaimableAfterClaim: m.globalClaimableAfterClaim,
      claim: m.claim?.hash ?? m.claim?.status ?? null,
    })),
  }));
  process.exit(0);
}

fail(`unknown COMMIT_LIVE_PHASE: ${PHASE}`);
