require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: '../.env' });

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    buildbear: {
      url: process.env.ETH_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      timeout: 0,
      gas: "auto",
      gasPrice: "auto"
    }
  },
  paths: {
    sources: "./",  // Look for .sol files in the current directory
    cache: "./cache",
    artifacts: "./artifacts"
  }
};
