import React, { useState, useEffect, useCallback } from 'react';
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
  HStack,
  IconButton,
  Tooltip,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Divider,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
} from '@chakra-ui/react';
import { useWeb3React } from '@web3-react/core';
import { CopyIcon, ChevronUpIcon, ChevronDownIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import axios from 'axios';

function Gallery() {
  const [media, setMedia] = useState({ photos: [], videoSessions: [] });
  const [loading, setLoading] = useState(true);
  const [activeSession, setActiveSession] = useState(null);
  const [imageErrors, setImageErrors] = useState({});
  const [selectedImage, setSelectedImage] = useState(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { active, account } = useWeb3React();
  const toast = useToast();

  const handleCopy = (text, type) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied!',
      description: `${type} copied to clipboard`,
      status: 'success',
      duration: 2000,
    });
  };

  const fetchMedia = useCallback(async () => {
    if (!active || !account) return;
    
    try {
      const photosRes = await axios.get(`http://localhost:5000/nfts/${account}`);
      console.log('Photos response:', photosRes.data);
      
      let videoSessions = [];
      try {
        const sessionsRes = await axios.get(`http://localhost:5000/video-sessions/${account}`);
        videoSessions = sessionsRes.data.sessions || [];
      } catch (err) {
        console.warn('Video sessions not available:', err);
      }
      
      setMedia({
        photos: photosRes.data.nfts || [],
        videoSessions: videoSessions.map(session => ({
          ...session,
          chunks: session.chunks?.sort((a, b) => a.sequence_number - b.sequence_number) || []
        }))
      });
    } catch (error) {
      console.error('Error fetching media:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch media',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  }, [active, account, toast]);

  useEffect(() => {
    fetchMedia();
  }, [fetchMedia]);

  const handleImageError = (tokenId) => {
    console.log('Image error for token:', tokenId);
    setImageErrors(prev => ({
      ...prev,
      [tokenId]: true
    }));
  };

  const handleImageClick = (nft) => {
    setSelectedImage(nft);
    onOpen();
  };

  const renderInfoRow = (label, value) => (
    <Box w="100%" py={1}>
      <Text fontSize="xs" color="gray.500" mb={1}>
        {label}
      </Text>
      <HStack justify="space-between" align="center" 
        bg="gray.800" 
        p={2} 
        borderRadius="md"
        borderWidth="1px"
        borderColor="gray.700"
        _hover={{ bg: 'gray.700' }}
      >
        <Text fontSize="sm" color="gray.300" isTruncated maxW="70%" fontFamily="mono">
          {value}
        </Text>
        <IconButton
          icon={<CopyIcon />}
          size="sm"
          variant="ghost"
          colorScheme="blue"
          color="gray.300"
          _hover={{ bg: 'gray.600' }}
          onClick={() => handleCopy(value, label)}
          aria-label={`Copy ${label}`}
        />
      </HStack>
    </Box>
  );

  const renderVideoSession = (session) => {
    const isActive = activeSession === session.id;
    const firstChunk = session.chunks[0];
    
    return (
      <Box 
        key={session.id}
        borderWidth="1px"
        borderRadius="lg"
        overflow="hidden"
        cursor="pointer"
        onClick={() => setActiveSession(isActive ? null : session.id)}
      >
        <Box p={4}>
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <Text fontWeight="bold">
                Session #{session.id}
              </Text>
              <Text fontSize="sm" color="gray.500">
                {new Date(session.start_time).toLocaleString()}
              </Text>
              <Text fontSize="sm">
                {session.chunks.length} clips
              </Text>
            </VStack>
            <IconButton
              aria-label="Expand session"
              icon={isActive ? <ChevronUpIcon /> : <ChevronDownIcon />}
            />
          </HStack>
        </Box>
        
        {isActive && (
          <SimpleGrid columns={[1, 2, 3]} spacing={4} p={4}>
            {session.chunks.map((chunk, idx) => (
              <Box key={chunk.video_cid}>
                <video
                  controls
                  width="100%"
                  src={`https://ipfs.io/ipfs/${chunk.video_cid}`}
                />
                <Text fontSize="sm" mt={2}>
                  Clip {idx + 1}
                </Text>
              </Box>
            ))}
          </SimpleGrid>
        )}
      </Box>
    );
  };

  if (!active) {
    return (
      <Center h="200px">
        <Text>Please connect your wallet to view your media</Text>
      </Center>
    );
  }

  if (loading) {
    return (
      <Center h="200px">
        <Spinner />
      </Center>
    );
  }

  return (
    <Box p={8} bg="gray.900">
      <Tabs>
        <TabList>
          <Tab>Photos</Tab>
          <Tab>Video Sessions</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            {media.photos.length === 0 ? (
              <Center h="200px">
                <Text>No photos found</Text>
              </Center>
            ) : (
              <SimpleGrid columns={[1, 2, 3]} spacing={8}>
                {media.photos.map((nft) => (
                  <Box
                    key={nft.tokenId}
                    borderWidth="1px"
                    borderRadius="lg"
                    overflow="hidden"
                    shadow="md"
                  >
                    {imageErrors[nft.tokenId] ? (
                      <Center h="200px" bg="gray.100">
                        <Text color="gray.500">Image not available</Text>
                      </Center>
                    ) : (
                      <Box position="relative" cursor="pointer" onClick={() => handleImageClick(nft)}>
                        <Image 
                          src={`https://ipfs.io/ipfs/${nft.image_cid}`}
                          alt={`Photo ${nft.tokenId}`}
                          fallback={<Center h="200px"><Spinner /></Center>}
                          onError={() => handleImageError(nft.tokenId)}
                          objectFit="cover"
                          h="200px"
                          w="100%"
                        />
                        <Box
                          position="absolute"
                          top={2}
                          right={2}
                          bg="gray.800"
                          p={2}
                          borderRadius="md"
                          opacity={0.7}
                          _hover={{ opacity: 1 }}
                        >
                          <ExternalLinkIcon color="white" />
                        </Box>
                      </Box>
                    )}
                    <Box p={4} bg="gray.900">
                      <Divider mb={3} borderColor="gray.700" />
                      <VStack spacing={3} align="stretch">
                        {renderInfoRow('IPFS Content ID', nft.image_cid)}
                        {renderInfoRow('Transaction Hash', nft.transaction_hash)}
                      </VStack>
                    </Box>
                  </Box>
                ))}
              </SimpleGrid>
            )}
          </TabPanel>

          <TabPanel>
            {media.videoSessions.length === 0 ? (
              <Center h="200px">
                <Text>No video sessions found</Text>
              </Center>
            ) : (
              <VStack spacing={4} align="stretch">
                {media.videoSessions.map(renderVideoSession)}
              </VStack>
            )}
          </TabPanel>
        </TabPanels>
      </Tabs>

      {/* Full-screen Image Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="full">
        <ModalOverlay bg="rgba(0, 0, 0, 0.9)" />
        <ModalContent bg="transparent" boxShadow="none">
          <ModalCloseButton color="white" size="lg" />
          <ModalBody display="flex" alignItems="center" justifyContent="center" p={0}>
            {selectedImage && (
              <Image
                src={`https://ipfs.io/ipfs/${selectedImage.image_cid}`}
                alt={`Photo ${selectedImage.tokenId}`}
                maxH="90vh"
                objectFit="contain"
                borderRadius="md"
                onClick={(e) => e.stopPropagation()}
              />
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}

export default Gallery;