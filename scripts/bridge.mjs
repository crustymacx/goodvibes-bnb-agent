import { ethers } from "ethers";
import { execSync } from "child_process";

const params = new URLSearchParams({
  fromChain: "8453",
  toChain: "204",
  fromToken: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  toToken: "0x0000000000000000000000000000000000000000",
  fromAmount: "2000000",
  fromAddress: "0xa31232040883e551E0390B0c621f1e689b0b8814",
});

console.log("Getting fresh quote...");
const resp = await fetch("https://li.quest/v1/quote?" + params);
const data = await resp.json();

if (!data.estimate || !data.transactionRequest) {
  console.log("Bad response:", JSON.stringify(data).slice(0, 500));
  process.exit(1);
}

const txReq = data.transactionRequest;
const toAmt = parseFloat(data.estimate.toAmount) / 1e18;
console.log("Bridge: 2 USDC (Base) ->", toAmt.toFixed(6), "BNB (opBNB)");

const privkey = execSync(
  'security find-generic-password -s evm-wallet-metamask-privkey -w',
  { encoding: "utf-8" }
).trim();
const provider = new ethers.JsonRpcProvider("https://mainnet.base.org", 8453);
const wallet = new ethers.Wallet(privkey, provider);

console.log("Sending bridge tx...");
const tx = await wallet.sendTransaction({
  to: txReq.to,
  data: txReq.data,
  value: txReq.value || "0x0",
  gasLimit: txReq.gasLimit,
});
console.log("TX hash:", tx.hash);
console.log("Waiting for confirmation...");
const receipt = await tx.wait();
console.log("Confirmed! Block:", receipt.blockNumber);
console.log("Gas used:", receipt.gasUsed.toString());
console.log("");
console.log("Bridge tx on Base: https://basescan.org/tx/" + tx.hash);
console.log("BNB should arrive on opBNB in ~1-5 minutes.");
