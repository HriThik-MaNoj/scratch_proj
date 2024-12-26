import { InjectedConnector } from '@web3-react/injected-connector';

export const injected = new InjectedConnector({
  supportedChainIds: [
    22566, // BuildBear testnet
    1337,  // Local network
  ],
});