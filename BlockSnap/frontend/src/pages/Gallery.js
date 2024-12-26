import React, { useState, useEffect } from 'react';
import {
  Box,
  SimpleGrid,
  Image,
  Text,
  VStack,
  Badge,
  useToast,
  Spinner,
  Center,
  Button,
} from '@chakra-ui/react';
import { useWeb3React } from '@web3-react/core';
import axios from 'axios';

function Gallery() {
  const [nfts, setNfts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { active, account } = useWeb3React();
  const toast = useToast();

  useEffect(() => {
    if (active && account) {
      fetchNFTs();
    }
  }, [active, account]);

  const fetchNFTs = async () => {
    try {
      const response = await axios.get(`http://localhost:5000/nfts/${account}`);
      setNfts(response.data.nfts);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch NFTs',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  if (!active) {
    return (
      <Center h="50vh">
        <VStack spacing={4}>
          <Text color="white" fontSize="xl">
            Please connect your wallet to view your NFTs
          </Text>
        </VStack>
      </Center>
    );
  }

  if (loading) {
    return (
      <Center h="50vh">
        <Spinner size="xl" color="blue.500" />
      </Center>
    );
  }

  return (
    <Box maxW="7xl" mx="auto" pt={5} px={{ base: 2, sm: 12, md: 17 }}>
      <VStack align="stretch" spacing={8}>
        <Text fontSize="2xl" fontWeight="bold" color="white">
          Your NFT Collection
        </Text>

        {nfts.length === 0 ? (
          <Center h="50vh">
            <VStack spacing={4}>
              <Text color="gray.400">No NFTs found in your collection</Text>
              <Button colorScheme="blue" onClick={() => window.location.href = '/camera'}>
                Capture New Photo
              </Button>
            </VStack>
          </Center>
        ) : (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
            {nfts.map((nft) => (
              <Box
                key={nft.tokenId}
                bg="gray.800"
                borderRadius="lg"
                overflow="hidden"
                transition="transform 0.2s"
                _hover={{ transform: 'scale(1.02)' }}
              >
                <Image
                  src={nft.imageUrl}
                  alt={`NFT ${nft.tokenId}`}
                  w="100%"
                  h="300px"
                  objectFit="cover"
                />
                <VStack p={4} align="stretch" spacing={2}>
                  <Text color="white" fontWeight="bold">
                    Token ID: {nft.tokenId}
                  </Text>
                  <Text color="gray.400" fontSize="sm" isTruncated>
                    IPFS CID: {nft.ipfsCid}
                  </Text>
                  <Badge colorScheme="blue" alignSelf="flex-start">
                    {nft.type || 'Photo'}
                  </Badge>
                </VStack>
              </Box>
            ))}
          </SimpleGrid>
        )}
      </VStack>
    </Box>
  );
}

export default Gallery; 