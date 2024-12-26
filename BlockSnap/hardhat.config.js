require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();
require("@matterlabs/hardhat-zksync");

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
    hardhat: {
      chainId: 1337
    },
    buildbear: {
      url: process.env.ETH_RPC_URL || "https://rpc.buildbear.io/impossible-omegared-15eaf7dd",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 22566
    }
  },
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY
  },
  paths: {
    sources: "./smart_contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
}; 