import React from 'react';
import {
  Box,
  Flex,
  Button,
  Text,
  useColorModeValue,
  HStack,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
} from '@chakra-ui/react';
import { useWeb3React } from '@web3-react/core';
import { injected } from '../utils/connectors';
import { ChevronDownIcon } from '@chakra-ui/icons';

function Navbar() {
  const { active, account, activate, deactivate } = useWeb3React();

  const connectWallet = async () => {
    console.log('Attempting to connect wallet...');
    try {
      // Check if MetaMask is installed
      if (!window.ethereum) {
        throw new Error('Please install MetaMask to connect your wallet');
      }

      // Try to switch to BuildBear network first
      try {
        await window.ethereum.request({
          method: 'wallet_switchEthereumChain',
          params: [{ chainId: '0x5826' }], // BuildBear chainId in hex (22566)
        });
      } catch (switchError) {
        // This error code indicates that the chain has not been added to MetaMask
        if (switchError.code === 4902) {
          try {
            await window.ethereum.request({
              method: 'wallet_addEthereumChain',
              params: [
                {
                  chainId: '0x5826',
                  chainName: 'BuildBear Testnet',
                  nativeCurrency: {
                    name: 'ETH',
                    symbol: 'ETH',
                    decimals: 18
                  },
                  rpcUrls: ['https://rpc.buildbear.io/impossible-omegared-15eaf7dd'],
                  blockExplorerUrls: ['https://explorer.buildbear.io/impossible-omegared-15eaf7dd']
                },
              ],
            });
          } catch (addError) {
            throw new Error('Failed to add BuildBear network to MetaMask');
          }
        } else {
          throw new Error('Please switch to BuildBear network in MetaMask');
        }
      }

      // Request account access
      await window.ethereum.request({ method: 'eth_requestAccounts' });
      
      // Activate the injected connector
      await activate(injected);
      console.log('Wallet connected:', account);
    } catch (error) {
      console.error('Error connecting wallet:', error);
      alert(error.message || 'Failed to connect wallet. Please try again.');
    }
  };

  const disconnectWallet = async () => {
    try {
      deactivate();
      console.log('Wallet disconnected');
    } catch (error) {
      console.error('Error disconnecting wallet:', error);
    }
  };

  const formatAddress = (address) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <Box
      px={4}
      bg={useColorModeValue('gray.800', 'gray.900')}
      borderBottom="1px"
      borderColor={useColorModeValue('gray.700', 'gray.700')}
    >
      <Flex h={16} alignItems="center" justifyContent="space-between">
        <Text
          fontSize="xl"
          fontWeight="bold"
          bgGradient="linear(to-r, cyan.400, blue.500, purple.600)"
          bgClip="text"
        >
          BlockSnap
        </Text>

        <HStack spacing={4}>
          {active ? (
            <Menu>
              <MenuButton
                as={Button}
                rightIcon={<ChevronDownIcon />}
                colorScheme="blue"
                variant="outline"
              >
                {formatAddress(account)}
              </MenuButton>
              <MenuList bg="gray.800" borderColor="gray.700">
                <MenuItem
                  bg="gray.800"
                  _hover={{ bg: 'gray.700' }}
                  onClick={disconnectWallet}
                >
                  Disconnect Wallet
                </MenuItem>
              </MenuList>
            </Menu>
          ) : (
            <Button
              colorScheme="blue"
              onClick={connectWallet}
              leftIcon={
                <img
                  src="/metamask-fox.svg"
                  alt="MetaMask"
                  style={{ width: '20px', height: '20px' }}
                />
              }
            >
              Connect Wallet
            </Button>
          )}
        </HStack>
      </Flex>
    </Box>
  );
}

export default Navbar; 