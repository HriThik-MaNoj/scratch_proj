const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("Deploying BlockSnap NFT contract...");

  // Get the deployer's signer
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);

  // Get the contract factory
  const BlockSnapNFT = await hre.ethers.getContractFactory("BlockSnapNFT");

  // Deploy the contract
  const blockSnap = await BlockSnapNFT.deploy();
  
  // Wait for the deployment transaction to be mined
  await blockSnap.waitForDeployment();
  const contractAddress = await blockSnap.getAddress();

  console.log("BlockSnapNFT deployed to:", contractAddress);

  // Get the contract artifacts
  const artifacts = await hre.artifacts.readArtifact("BlockSnapNFT");

  // Create contract info JSON
  const contractInfo = {
    address: contractAddress,
    abi: artifacts.abi,
    network: hre.network.name,
    deploymentTime: new Date().toISOString()
  };

  // Save contract info to file
  const contractsDir = path.join(__dirname, "..", "frontend", "src", "contracts");
  if (!fs.existsSync(contractsDir)) {
    fs.mkdirSync(contractsDir, { recursive: true });
  }

  fs.writeFileSync(
    path.join(contractsDir, "BlockSnapNFT.json"),
    JSON.stringify(contractInfo, null, 2)
  );

  console.log("Contract information saved to BlockSnapNFT.json");

  // Verify contract on Etherscan if not on localhost
  if (hre.network.name !== "localhost" && hre.network.name !== "hardhat") {
    console.log("Verifying contract on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: blockSnap.address,
        constructorArguments: []
      });
      console.log("Contract verified on Etherscan");
    } catch (error) {
      console.error("Error verifying contract:", error);
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  }); 