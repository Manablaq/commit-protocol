import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const REPO = path.resolve(process.env.COMMIT_REPO ?? process.cwd());
const EVIDENCE_DIR = process.env.COMMIT_EVIDENCE_DIR;
const TX_HASH = process.env.COMMIT_DEPLOY_TX_HASH;
if (!EVIDENCE_DIR || !TX_HASH) {
  throw new Error(
    "COMMIT_EVIDENCE_DIR and COMMIT_DEPLOY_TX_HASH are required",
  );
}
if (!/^0x[0-9a-fA-F]{64}$/.test(TX_HASH)) {
  throw new Error("COMMIT_DEPLOY_TX_HASH is not a transaction hash");
}

const EXPECTED = {
  sourceSha256:
    "8b617544e3ad60d3e3f94c38bde309701f6f44795948106591223eee02ecc95f",
  sourceBytes: 19914,
  helper: "0x53405950e587Ca4F6232b4596f0992ea5aaD8Ae4",
  worker: "0x1f87Ae197af539253978d435aD45cCf28Fb95024",
  chainId: 61997,
  submissionRpc: "https://studio-next.genlayer.com/api",
  rotations: 3,
  revision: "0.7.0-reviewable-manifest",
};

const jsonSafe = (value) =>
  JSON.stringify(value, (_key, item) =>
    typeof item === "bigint" ? item.toString() : item,
  );
const sha256 = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const repoRequire = createRequire(path.join(REPO, "package.json"));
const sdkPath = repoRequire.resolve("genlayer-js");
const chainsPath = repoRequire.resolve("genlayer-js/chains");
const { createClient, isSuccessful } = await import(pathToFileURL(sdkPath).href);
const { studioDevnet } = await import(pathToFileURL(chainsPath).href);
const studioNextChain = {
  ...studioDevnet,
  name: "GenLayer Studio Next",
  rpcUrls: { default: { http: [EXPECTED.submissionRpc] } },
};
const client = createClient({ chain: studioNextChain });

fs.mkdirSync(EVIDENCE_DIR, { recursive: true, mode: 0o700 });
const receipt = await client.waitForTransactionReceipt({
  hash: TX_HASH,
  waitUntil: "finalized",
  interval: 7500,
  retries: 80,
  fullTransaction: true,
});
fs.writeFileSync(
  path.join(EVIDENCE_DIR, "finalized-receipt.json"),
  `${jsonSafe(receipt)}\n`,
);

if (String(receipt.statusName).toUpperCase() !== "FINALIZED") {
  throw new Error(`deployment did not finalize: ${receipt.statusName}`);
}
if (!isSuccessful(receipt)) {
  throw new Error("finalized deployment execution was not successful");
}

const address = receipt?.data?.contract_address;
if (!/^0x[0-9a-fA-F]{40}$/.test(String(address))) {
  throw new Error("finalized receipt has no contract address");
}
const forbidden = new Set([
  EXPECTED.helper.toLowerCase(),
  "0x597641c88a3644f2c8c5c0bad9f1072710a82e85",
  "0x7c1e450333d97cd4e02f48c3424bf10112697a60",
]);
if (forbidden.has(String(address).toLowerCase())) {
  throw new Error("deployment returned a previous or forbidden address");
}

const transaction = await client.request({
  method: "eth_getTransactionByHash",
  params: [TX_HASH],
});
fs.writeFileSync(
  path.join(EVIDENCE_DIR, "deployment-transaction.json"),
  `${jsonSafe(transaction)}\n`,
);
if (String(transaction?.from_address).toLowerCase() !== EXPECTED.worker.toLowerCase()) {
  throw new Error("deployment signer mismatch");
}
const recordedRotations = transaction?.data?.fees_distribution?.rotations;
if (
  !Array.isArray(recordedRotations) ||
  recordedRotations.length !== 1 ||
  Number(recordedRotations[0]) !== EXPECTED.rotations ||
  Number(transaction?.config_rotation_rounds) !== EXPECTED.rotations
) {
  throw new Error(
    `finalized transaction did not record the required [${EXPECTED.rotations}] rotation envelope`,
  );
}

const deployedCode = Buffer.from(await client.getContractCode(address), "utf8");
const deployedSha256 = sha256(deployedCode);
if (
  deployedCode.length !== EXPECTED.sourceBytes ||
  deployedSha256 !== EXPECTED.sourceSha256
) {
  throw new Error("deployed coordinator source does not match the release candidate");
}
const protocolInfo = await client.readContract({
  address,
  functionName: "protocol_info",
});
if (
  protocolInfo.protocol !== "commit" ||
  protocolInfo.revision !== EXPECTED.revision ||
  String(protocolInfo.helper_address).toLowerCase() !== EXPECTED.helper.toLowerCase() ||
  Number(protocolInfo.mission_count) !== 0
) {
  throw new Error("protocol_info does not match the release contract invariants");
}

fs.writeFileSync(path.join(EVIDENCE_DIR, "deployed-commit.py"), deployedCode);
fs.writeFileSync(
  path.join(EVIDENCE_DIR, "protocol-info.json"),
  `${jsonSafe(protocolInfo)}\n`,
);
console.log("FINALIZED_RECEIPT_STATUS=FINALIZED");
console.log("FINALIZED_EXECUTION_SUCCESS=YES");
console.log(`DEPLOYED_CONTRACT_ADDRESS=${address}`);
console.log(`DEPLOYED_COORDINATOR_SHA256=${deployedSha256}`);
console.log(`DEPLOYED_COORDINATOR_BYTES=${deployedCode.length}`);
console.log(`RECORDED_CONSENSUS_ROTATIONS=${transaction.config_rotation_rounds}`);
console.log(`RECORDED_FEE_ROTATIONS=${recordedRotations.join(",")}`);
console.log("PROTOCOL_INFO=PASS");
