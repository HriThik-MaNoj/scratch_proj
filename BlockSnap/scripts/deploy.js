const hre = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("Deploying BlockSnap NFT contract...");

  // Get the contract factory
  const BlockSnapNFT = await hre.ethers.getContractFactory("BlockSnapNFT");
  console.log("Contract factory created");

  // Deploy the contract
  const blockSnap = await BlockSnapNFT.deploy();
  console.log("Contract deployment initiated");

  // Wait for deployment
  await blockSnap.waitForDeployment();
  const contractAddress = await blockSnap.getAddress();
  console.log("Contract deployed to:", contractAddress);

  // Get the contract artifacts
  const artifacts = await hre.artifacts.readArtifact("BlockSnapNFT");

  // Create contract info JSON
  const contractInfo = {
    address: contractAddress,
    abi: artifacts.abi,
    network: hre.network.name,
    deploymentTime: new Date().toISOString()
  };

  // Save contract info to JSON file
  const contractInfoPath = './BlockSnapNFT.json';
  fs.writeFileSync(
    contractInfoPath,
    JSON.stringify(contractInfo, null, 2)
  );

  console.log("Contract information saved to BlockSnapNFT.json");

  // Update the .env file with the new contract address
  const envPath = '../.env';
  const envContent = fs.readFileSync(envPath, 'utf8');
  const updatedContent = envContent.replace(
    /^CONTRACT_ADDRESS=.*/m,
    `CONTRACT_ADDRESS=${contractAddress}`
  );
  fs.writeFileSync(envPath, updatedContent);
  console.log("Updated .env file with new contract address");

  // Verify contract on Etherscan if not on localhost
  if (hre.network.name !== "localhost" && hre.network.name !== "hardhat") {
    console.log("Verifying contract on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: contractAddress,
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