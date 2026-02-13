#!/usr/bin/env node
/**
 * deploy.mjs — Compile + deploy BountyLedger.sol to opBNB
 *
 * Usage:
 *   node scripts/deploy.mjs                 # Full compile + deploy
 *   node scripts/deploy.mjs --compile-only  # Just compile, save ABI
 *
 * Reads private key from macOS Keychain (same key Crusty uses everywhere).
 * Writes deployed address to deployed.json and ABI to abi/BountyLedger.json.
 */

import { execSync } from "child_process";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import solc from "solc";
import { ethers } from "ethers";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = resolve(__dirname, "..");

// --- Config ---
const OPBNB_RPC = "https://opbnb-mainnet-rpc.bnbchain.org";
const OPBNB_CHAIN_ID = 204;
const KEYCHAIN_SERVICE = "evm-wallet-metamask-privkey";

// --- Helpers ---
function getPrivateKey() {
  try {
    const key = execSync(
      `security find-generic-password -s "${KEYCHAIN_SERVICE}" -w`,
      { encoding: "utf-8" }
    ).trim();
    return key.startsWith("0x") ? key : `0x${key}`;
  } catch (e) {
    console.error("Failed to read private key from Keychain.");
    console.error("Expected keychain service:", KEYCHAIN_SERVICE);
    process.exit(1);
  }
}

function compileSolidity() {
  const contractPath = resolve(ROOT, "contracts", "BountyLedger.sol");
  const source = readFileSync(contractPath, "utf-8");

  const input = {
    language: "Solidity",
    sources: {
      "BountyLedger.sol": { content: source },
    },
    settings: {
      optimizer: { enabled: true, runs: 200 },
      outputSelection: {
        "*": {
          "*": ["abi", "evm.bytecode.object"],
        },
      },
    },
  };

  console.log("Compiling BountyLedger.sol...");
  const output = JSON.parse(solc.compile(JSON.stringify(input)));

  if (output.errors) {
    const fatal = output.errors.filter((e) => e.severity === "error");
    if (fatal.length > 0) {
      console.error("Compilation errors:");
      fatal.forEach((e) => console.error(e.formattedMessage));
      process.exit(1);
    }
    // Show warnings but don't fail
    output.errors
      .filter((e) => e.severity === "warning")
      .forEach((e) => console.warn("Warning:", e.message));
  }

  const contract = output.contracts["BountyLedger.sol"]["BountyLedger"];
  const abi = contract.abi;
  const bytecode = "0x" + contract.evm.bytecode.object;

  // Save ABI
  const abiDir = resolve(ROOT, "abi");
  if (!existsSync(abiDir)) mkdirSync(abiDir, { recursive: true });
  writeFileSync(
    resolve(abiDir, "BountyLedger.json"),
    JSON.stringify(abi, null, 2)
  );
  console.log(`ABI saved to abi/BountyLedger.json (${abi.length} entries)`);

  return { abi, bytecode };
}

async function deploy(abi, bytecode) {
  const privateKey = getPrivateKey();

  console.log(`\nConnecting to opBNB (chain ${OPBNB_CHAIN_ID})...`);
  const provider = new ethers.JsonRpcProvider(OPBNB_RPC, OPBNB_CHAIN_ID);
  const wallet = new ethers.Wallet(privateKey, provider);

  const address = wallet.address;
  const balance = await provider.getBalance(address);
  const balBNB = ethers.formatEther(balance);
  console.log(`Wallet: ${address}`);
  console.log(`Balance: ${balBNB} BNB`);

  if (balance === 0n) {
    console.error("\nNo BNB in wallet! Need ~0.001 BNB for deployment on opBNB.");
    console.error("Send BNB to:", address);
    process.exit(1);
  }

  console.log("\nDeploying BountyLedger...");
  const factory = new ethers.ContractFactory(abi, bytecode, wallet);
  const contract = await factory.deploy();
  console.log("Tx hash:", contract.deploymentTransaction().hash);

  console.log("Waiting for confirmation...");
  await contract.waitForDeployment();

  const deployedAddress = await contract.getAddress();
  console.log(`\nDeployed at: ${deployedAddress}`);
  console.log(`Explorer: https://opbnbscan.com/address/${deployedAddress}`);

  // Save deployment info
  const deployInfo = {
    contract: "BountyLedger",
    address: deployedAddress,
    network: "opbnb",
    chainId: OPBNB_CHAIN_ID,
    rpc: OPBNB_RPC,
    deployer: address,
    deployTx: contract.deploymentTransaction().hash,
    deployedAt: new Date().toISOString(),
    explorer: `https://opbnbscan.com/address/${deployedAddress}`,
  };

  writeFileSync(
    resolve(ROOT, "deployed.json"),
    JSON.stringify(deployInfo, null, 2)
  );
  console.log("Deployment info saved to deployed.json");

  return deployInfo;
}

// --- Main ---
const compileOnly = process.argv.includes("--compile-only");
const { abi, bytecode } = compileSolidity();
console.log(`Bytecode: ${bytecode.length} chars`);

if (compileOnly) {
  console.log("\n--compile-only: skipping deployment.");
  process.exit(0);
}

deploy(abi, bytecode).catch((err) => {
  console.error("Deployment failed:", err.message);
  process.exit(1);
});
