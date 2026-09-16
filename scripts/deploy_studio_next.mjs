import crypto from "node:crypto";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const REPO = path.resolve(process.env.COMMIT_REPO ?? process.cwd());
const CLI_REAL = process.env.COMMIT_CLI_REAL;
const PREFLIGHT_ONLY = process.env.COMMIT_DEPLOY_PREFLIGHT_ONLY !== "0";
const DEPLOY_CONFIRM = process.env.COMMIT_DEPLOY_CONFIRM;
const DEPLOY_MARKER = process.env.COMMIT_DEPLOY_MARKER;

const EXPECTED = {
  sourceSha256:
    "e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6",
  sourceBytes: 19873,
  helper: "0x53405950e587Ca4F6232b4596f0992ea5aaD8Ae4",
  worker: "0x1f87Ae197af539253978d435aD45cCf28Fb95024",
  chainId: 61997,
  sdkRpc: "https://studio-dev.genlayer.com/api",
  submissionRpc: "https://studio-next.genlayer.com/api",
  sdkVersion: "2.0.0-rc.1",
  rotations: 3,
  constructorSha256:
    "9829922e2163a437f2d98abf6c1bc269b667125107c0d16a3054e882900d1e34",
  deploymentDataSha256:
    "6d2280e6e4b0f6d6c8941732e7d4c3a5dd0a48a8e85b7a22ae070a94d74985d1",
  deploymentDataBytes: 19909,
  executionBudgetPerRound: 153643200000000n,
  maxPriceGenPerTimeUnit: 2n,
  storageFeeMaxGasPrice: 300000000n,
  receiptFeeMaxGasPrice: 300000000n,
};

const sha256 = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const jsonSafe = (value) =>
  JSON.stringify(value, (_key, item) =>
    typeof item === "bigint" ? item.toString() : item,
  );
const fail = (message) => {
  throw new Error(`Studio Next deployment stopped: ${message}`);
};

const requirePackage = (start, packageName) => {
  let current = path.dirname(start);
  while (true) {
    const packagePath = path.join(current, "package.json");
    if (fs.existsSync(packagePath)) {
      try {
        const packageJson = JSON.parse(fs.readFileSync(packagePath, "utf8"));
        if (packageJson.name === packageName) {
          return { path: packagePath, packageJson };
        }
      } catch {
        // Continue walking if an unrelated package file is malformed.
      }
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  fail(`could not locate ${packageName} from ${start}`);
};

if (!fs.existsSync(path.join(REPO, "package.json"))) {
  fail(`repository does not contain package.json: ${REPO}`);
}
if (!CLI_REAL) {
  fail("COMMIT_CLI_REAL must point to the resolved genlayer CLI binary");
}
const cliEntry = fs.realpathSync(CLI_REAL);

const worktree = execFileSync("git", ["-C", REPO, "status", "--porcelain"], {
  encoding: "utf8",
});
if (worktree.trim()) fail("repository worktree is not clean");

const repoRequire = createRequire(path.join(REPO, "package.json"));
const sdkPath = repoRequire.resolve("genlayer-js");
const chainsPath = repoRequire.resolve("genlayer-js/chains");
const typesPath = repoRequire.resolve("genlayer-js/types");
const sdkPackage = JSON.parse(
  fs.readFileSync(path.join(REPO, "node_modules/genlayer-js/package.json"), "utf8"),
);
if (sdkPackage.version !== EXPECTED.sdkVersion) {
  fail(`genlayer-js drift: ${sdkPackage.version} != ${EXPECTED.sdkVersion}`);
}

const sdk = await import(pathToFileURL(sdkPath).href);
const chains = await import(pathToFileURL(chainsPath).href);
const types = await import(pathToFileURL(typesPath).href);
const { abi, createAccount, createClient } = sdk;
const { studioDevnet } = chains;
const { CalldataAddress } = types;

if (Number(studioDevnet.id) !== EXPECTED.chainId) fail("SDK chain ID drift");
if (studioDevnet.rpcUrls?.default?.http?.[0] !== EXPECTED.sdkRpc) {
  fail("SDK compatibility RPC drift");
}
if (Number(studioDevnet.defaultConsensusMaxRotations) !== EXPECTED.rotations) {
  fail("SDK default consensus rotations drift");
}

const studioNextChain = {
  ...studioDevnet,
  name: "GenLayer Studio Next",
  rpcUrls: { default: { http: [EXPECTED.submissionRpc] } },
};
if (
  Number(studioNextChain.id) !== EXPECTED.chainId ||
  studioNextChain.rpcUrls.default.http[0] !== EXPECTED.submissionRpc
) {
  fail("Studio Next chain override mismatch");
}

const cliPackage = requirePackage(cliEntry, "genlayer");
const cliRequire = createRequire(cliPackage.path);
const keytarModule = cliRequire("keytar");
const keytar = keytarModule.default ?? keytarModule;
const configPath = path.join(os.homedir(), ".genlayer", "genlayer-config.json");
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
const activeAccount = config.activeAccount;
if (typeof activeAccount !== "string" || !activeAccount) {
  fail("active GenLayer account is missing");
}
const signerAccount = "worker";

const keystorePath = path.join(
  os.homedir(),
  ".genlayer",
  "keystores",
  `${signerAccount}.json`,
);
const keystore = JSON.parse(fs.readFileSync(keystorePath, "utf8"));
const rawKeystoreAddress = String(keystore.address ?? "");
const keystoreAddress = rawKeystoreAddress.startsWith("0x")
  ? rawKeystoreAddress
  : `0x${rawKeystoreAddress}`;
if (keystoreAddress.toLowerCase() !== EXPECTED.worker.toLowerCase()) {
  fail(`worker keystore is not the authorized worker: ${keystoreAddress}`);
}

let privateKey = await keytar.getPassword("genlayer-cli", `account:${signerAccount}`);
if (typeof privateKey !== "string" || !privateKey) {
  fail("authorized worker account is not unlocked in the OS keychain");
}
const account = createAccount(privateKey);
privateKey = null;
if (String(account.address).toLowerCase() !== EXPECTED.worker.toLowerCase()) {
  fail("keychain signer does not derive the authorized worker");
}

const sourceBytes = fs.readFileSync(path.join(REPO, "contracts/commit.py"));
if (
  sourceBytes.length !== EXPECTED.sourceBytes ||
  sha256(sourceBytes) !== EXPECTED.sourceSha256
) {
  fail("coordinator source bytes or SHA-256 do not match the release candidate");
}

const typedHelper = new CalldataAddress(
  Uint8Array.from(Buffer.from(EXPECTED.helper.slice(2), "hex")),
);
const constructorCalldata = abi.calldata.encode(
  abi.calldata.makeCalldataObject(undefined, [typedHelper], undefined),
);
const serializedDeployment = abi.transactions.serialize([
  new Uint8Array(sourceBytes),
  constructorCalldata,
  false,
]);
const deploymentBytes = Buffer.from(serializedDeployment.slice(2), "hex");
if (sha256(Buffer.from(constructorCalldata)) !== EXPECTED.constructorSha256) {
  fail("constructor calldata changed");
}
if (
  deploymentBytes.length !== EXPECTED.deploymentDataBytes ||
  sha256(deploymentBytes) !== EXPECTED.deploymentDataSha256
) {
  fail("serialized deployment data changed");
}

const client = createClient({ chain: studioNextChain, account });
const policy = await client.getCurrentFeePolicy();
if (!policy.enabled) fail("Studio Next fee policy is disabled");
if (policy.genPerTimeUnit > EXPECTED.maxPriceGenPerTimeUnit) {
  fail("live GEN time-unit price exceeds the pinned fee cap");
}
if (policy.storageUnitPrice > EXPECTED.storageFeeMaxGasPrice) {
  fail("live storage price exceeds the pinned fee cap");
}
if (policy.receiptGasPrice > EXPECTED.receiptFeeMaxGasPrice) {
  fail("live receipt price exceeds the pinned fee cap");
}

const executionBudgetPerRound =
  policy.executionBudgetFloor > EXPECTED.executionBudgetPerRound
    ? policy.executionBudgetFloor
    : EXPECTED.executionBudgetPerRound;
const fees = await client.estimateTransactionFees({
  leaderTimeunitsAllocation: 100n,
  validatorTimeunitsAllocation: 200n,
  appealRounds: 0n,
  executionBudgetPerRound,
  executionConsumed: 0n,
  totalMessageFees: 0n,
  rotations: [BigInt(EXPECTED.rotations)],
  maxPriceGenPerTimeUnit: EXPECTED.maxPriceGenPerTimeUnit,
  storageFeeMaxGasPrice: EXPECTED.storageFeeMaxGasPrice,
  receiptFeeMaxGasPrice: EXPECTED.receiptFeeMaxGasPrice,
  messageAllocations: [],
});
const distributionRotations = fees.distribution?.rotations ?? [];
if (
  distributionRotations.length !== 1 ||
  distributionRotations[0] !== BigInt(EXPECTED.rotations)
) {
  fail(`fee distribution rotations are not [${EXPECTED.rotations}]`);
}
if (fees.feeValue <= 0n) fail("live fee estimate is zero");

const balance = await client.getBalance({
  address: account.address,
  blockTag: "pending",
});
if (balance <= fees.feeValue) {
  fail(`worker balance ${balance} does not cover fee ${fees.feeValue}`);
}
const pendingNonce = await client.getTransactionCount({
  address: account.address,
  blockTag: "pending",
});

const summary = {
  schema: "commit-studio-next-deployment-preflight-v1",
  preflightOnly: PREFLIGHT_ONLY,
  repository: REPO,
  activeAccount,
  signerAccount,
  signer: account.address.toLowerCase(),
  sdkVersion: sdkPackage.version,
  submissionRpc: EXPECTED.submissionRpc,
  chainId: EXPECTED.chainId,
  sourceSha256: EXPECTED.sourceSha256,
  sourceBytes: sourceBytes.length,
  helper: EXPECTED.helper,
  constructorSha256: EXPECTED.constructorSha256,
  deploymentDataSha256: EXPECTED.deploymentDataSha256,
  deploymentDataBytes: deploymentBytes.length,
  pendingNonce,
  balanceWei: balance.toString(),
  feePolicy: policy,
  fees,
  consensusMaxRotations: EXPECTED.rotations,
  feeDistributionRotations: distributionRotations,
};
console.log(`STUDIO_NEXT_PREFLIGHT=${jsonSafe(summary)}`);
console.log("SOURCE_BINDING=PASS");
console.log("SIGNER_BINDING=PASS");
console.log("STUDIO_NEXT_CHAIN=PASS");
console.log("LIVE_FEE_POLICY=PASS");
console.log("ROTATION_ENVELOPE=PASS");

if (PREFLIGHT_ONLY) {
  console.log("DEPLOYMENT_SUBMISSION_PERFORMED=NO");
  process.exit(0);
}
if (DEPLOY_CONFIRM !== "ONE_STUDIO_NEXT_DEPLOYMENT") {
  fail(
    "write mode requires COMMIT_DEPLOY_CONFIRM=ONE_STUDIO_NEXT_DEPLOYMENT",
  );
}
if (!DEPLOY_MARKER) fail("write mode requires COMMIT_DEPLOY_MARKER");

const markerPayload = {
  schema: "commit-studio-next-single-use-marker-v1",
  createdAt: new Date().toISOString(),
  submissionStarted: false,
  repository: REPO,
  sourceSha256: EXPECTED.sourceSha256,
  signer: account.address.toLowerCase(),
  submissionRpc: EXPECTED.submissionRpc,
  chainId: EXPECTED.chainId,
  pendingNonce,
  feeValue: fees.feeValue.toString(),
  consensusMaxRotations: EXPECTED.rotations,
  feeDistributionRotations: distributionRotations.map(String),
};
fs.mkdirSync(path.dirname(DEPLOY_MARKER), { recursive: true, mode: 0o700 });
let markerFd;
try {
  markerFd = fs.openSync(DEPLOY_MARKER, "wx", 0o600);
  fs.writeFileSync(markerFd, `${jsonSafe(markerPayload)}\n`);
  fs.closeSync(markerFd);
} catch (error) {
  if (markerFd !== undefined) fs.closeSync(markerFd);
  fail(`single-use deployment marker already exists or is not writable: ${error}`);
}

try {
  const txHash = await client.deployContract({
    account,
    code: new Uint8Array(sourceBytes),
    args: [typedHelper],
    leaderOnly: false,
    consensusMaxRotations: EXPECTED.rotations,
    fees: {
      distribution: fees.distribution,
      messageAllocations: fees.messageAllocations,
      feeValue: fees.feeValue,
    },
  });
  if (!/^0x[0-9a-fA-F]{64}$/.test(txHash)) {
    fail("SDK did not return a transaction hash");
  }
  fs.writeFileSync(
    DEPLOY_MARKER,
    `${jsonSafe({ ...markerPayload, submissionStarted: true, txHash })}\n`,
  );
  console.log(`DEPLOYMENT_TRANSACTION_HASH=${txHash.toLowerCase()}`);
  console.log("DEPLOYMENT_SUBMISSION_PERFORMED=YES");
} catch (error) {
  fs.writeFileSync(
    DEPLOY_MARKER,
    `${jsonSafe({ ...markerPayload, submissionStarted: true, outcome: "unknown" })}\n`,
  );
  throw error;
}
