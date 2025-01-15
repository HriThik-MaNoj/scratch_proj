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
  const [retryCount, setRetryCount] = useState({});
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { active, account } = useWeb3React();
  const toast = useToast();
  const MAX_RETRIES = 3;

  const getIPFSUrl = useCallback((cid) => {
    // Use local IPFS gateway
    return `http://127.0.0.1:8080/ipfs/${cid}`;
  }, []);

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
        // Deduplicate chunks in each session
        videoSessions = sessionsRes.data.sessions.map(session => {
          // Create a map of unique chunks using sequence_number as key
          const uniqueChunks = new Map();
          session.chunks.forEach(chunk => {
            const key = chunk.sequence_number;
            if (!uniqueChunks.has(key) || chunk.timestamp > uniqueChunks.get(key).timestamp) {
              uniqueChunks.set(key, chunk);
            }
          });
          
          return {
            ...session,
            chunks: Array.from(uniqueChunks.values()).sort((a, b) => a.sequence_number - b.sequence_number)
          };
        });
      } catch (err) {
        console.warn('Video sessions not available:', err);
      }
      
      setMedia({
        photos: photosRes.data.nfts || [],
        videoSessions
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

  const handleImageError = useCallback((tokenId) => {
    setRetryCount(prev => {
      const currentRetry = (prev[tokenId] || 0) + 1;
      if (currentRetry <= MAX_RETRIES) {
        // Force image reload by updating the key
        const img = document.querySelector(`img[data-token-id="${tokenId}"]`);
        if (img) {
          img.src = getIPFSUrl(media.photos.find(p => p.tokenId === tokenId)?.image_cid) + `?retry=${currentRetry}`;
        }
        return { ...prev, [tokenId]: currentRetry };
      } else {
        setImageErrors(prev => ({ ...prev, [tokenId]: true }));
        return prev;
      }
    });
  }, [media.photos, getIPFSUrl]);

  const handleImageClick = (nft) => {
    setSelectedImage(nft);
    onOpen();
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return 'Unknown date';
    // Ensure timestamp is in milliseconds
    const date = new Date(Number(timestamp) * 1000);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const getSessionTitle = (session) => {
    const date = formatDate(session.chunks[0]?.timestamp || session.start_block);
    const status = session.is_active ? 'Recording' : 'Completed';
    return `Dashcam Session - ${date} (${status})`;
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
    const isActive = activeSession === session.session_id;
    
    return (
      <Box 
        key={session.session_id}
        borderWidth="1px"
        borderRadius="lg"
        overflow="hidden"
        bg="gray.800"
        _hover={{ bg: 'gray.750' }}
      >
        <Box p={4} onClick={() => setActiveSession(isActive ? null : session.session_id)} cursor="pointer">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <Text fontWeight="bold" color="blue.300">
                {getSessionTitle(session)}
              </Text>
              <HStack spacing={2}>
                <Badge colorScheme={session.is_active ? 'green' : 'gray'}>
                  {session.is_active ? 'Active' : 'Completed'}
                </Badge>
                <Badge colorScheme="blue">
                  {session.chunks.length} clips
                </Badge>
              </HStack>
            </VStack>
            <IconButton
              aria-label="Expand session"
              icon={isActive ? <ChevronUpIcon /> : <ChevronDownIcon />}
              variant="ghost"
              colorScheme="blue"
            />
          </HStack>
        </Box>
        
        {isActive && (
          <Box>
            <Divider />
            <Box p={4}>
              {renderInfoRow('Session ID', session.session_id)}
              {renderInfoRow('Transaction', session.transaction_hash)}
              <Text fontSize="sm" color="gray.400" mt={4} mb={2}>
                Video Clips
              </Text>
              <SimpleGrid columns={[1, 2, 3]} spacing={4}>
                {session.chunks.map((chunk, idx) => (
                  <Box 
                    key={chunk.video_cid}
                    borderWidth="1px"
                    borderRadius="md"
                    overflow="hidden"
                    bg="gray.900"
                  >
                    <Box position="relative" className="video-container">
                      {chunk.status === 'ready' ? (
                        <video
                          controls
                          width="100%"
                          src={getIPFSUrl(chunk.video_cid)}
                          poster={getIPFSUrl(chunk.video_cid)}
                          onError={(e) => {
                            console.error('Video playback error:', e);
                            e.target.onerror = null; // Prevent infinite error loop
                            const errorBox = e.target.parentElement.querySelector('.video-error');
                            if (errorBox) {
                              errorBox.style.display = 'block';
                            }
                            toast({
                              title: 'Video Error',
                              description: `Unable to play video clip ${chunk.sequence_number + 1}. The content may still be loading or unavailable.`,
                              status: 'warning',
                              duration: 5000,
                            });
                          }}
                        />
                      ) : (
                        <Box
                          width="100%"
                          height="200px"
                          bg="gray.700"
                          display="flex"
                          alignItems="center"
                          justifyContent="center"
                          flexDirection="column"
                        >
                          <Text color="gray.400" mb={2}>
                            {chunk.status === 'unavailable' 
                              ? 'Video content not available in IPFS'
                              : chunk.status === 'error'
                              ? 'Error loading video'
                              : 'Loading video...'}
                          </Text>
                          {chunk.error && (
                            <Text fontSize="xs" color="red.300">
                              Error: {chunk.error}
                            </Text>
                          )}
                          <Button
                            size="sm"
                            mt={2}
                            onClick={async () => {
                              try {
                                // Try to fetch the video session again
                                const response = await axios.get(`http://localhost:5000/video-sessions/${account}`);
                                const updatedSession = response.data.sessions.find(
                                  s => s.session_id === session.session_id
                                );
                                if (updatedSession) {
                                  const updatedChunk = updatedSession.chunks.find(
                                    c => c.sequence_number === chunk.sequence_number
                                  );
                                  if (updatedChunk && updatedChunk.status === 'ready') {
                                    // Update the media state with new data
                                    setMedia(prev => ({
                                      ...prev,
                                      videoSessions: prev.videoSessions.map(s => 
                                        s.session_id === session.session_id ? updatedSession : s
                                      )
                                    }));
                                    toast({
                                      title: 'Success',
                                      description: 'Video content is now available',
                                      status: 'success',
                                      duration: 3000,
                                    });
                                  } else {
                                    throw new Error('Content still unavailable');
                                  }
                                }
                              } catch (error) {
                                console.error('Error checking video availability:', error);
                                toast({
                                  title: 'Error',
                                  description: 'Failed to check video availability',
                                  status: 'error',
                                  duration: 5000,
                                });
                              }
                            }}
                          >
                            Check Availability
                          </Button>
                        </Box>
                      )}
                      <Badge
                        position="absolute"
                        top={2}
                        right={2}
                        colorScheme={chunk.status === 'ready' ? 'blue' : 'gray'}
                      >
                        Clip {chunk.sequence_number + 1}
                      </Badge>
                      {chunk.status === 'ready' && (
                        <Box
                          position="absolute"
                          top="50%"
                          left="50%"
                          transform="translate(-50%, -50%)"
                          textAlign="center"
                          display="none"
                          className="video-error"
                        >
                          <Text color="red.300" fontSize="sm">
                            Unable to play video
                          </Text>
                          <Button
                            size="sm"
                            mt={2}
                            onClick={(event) => {
                              const videoElement = event.target.closest('.video-container').querySelector('video');
                              if (videoElement) {
                                videoElement.load();
                                videoElement.play().catch(console.error);
                              }
                            }}
                          >
                            Retry
                          </Button>
                        </Box>
                      )}
                    </Box>
                    <VStack spacing={2} p={3}>
                      <Text fontSize="sm" color="gray.300">
                        {formatDate(chunk.timestamp)}
                      </Text>
                      <Box w="100%">
                        <Text fontSize="xs" color="gray.500" mb={1}>
                          IPFS CID
                        </Text>
                        <HStack>
                          <Text fontSize="xs" color="gray.300" isTruncated fontFamily="mono">
                            {chunk.video_cid}
                          </Text>
                          <IconButton
                            icon={<CopyIcon />}
                            size="xs"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCopy(chunk.video_cid, 'CID');
                            }}
                            aria-label="Copy CID"
                          />
                        </HStack>
                      </Box>
                      {chunk.transaction_hash && (
                        <Box w="100%">
                          <Text fontSize="xs" color="gray.500" mb={1}>
                            Transaction
                          </Text>
                          <HStack>
                            <Text fontSize="xs" color="gray.300" isTruncated fontFamily="mono">
                              {chunk.transaction_hash}
                            </Text>
                            <IconButton
                              icon={<CopyIcon />}
                              size="xs"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCopy(chunk.transaction_hash, 'Transaction Hash');
                              }}
                              aria-label="Copy Transaction Hash"
                            />
                            <Tooltip label="View on Explorer">
                              <IconButton
                                icon={<ExternalLinkIcon />}
                                size="xs"
                                variant="ghost"
                                as="a"
                                href={`https://buildbear.io/tx/${chunk.transaction_hash}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                aria-label="View on Explorer"
                              />
                            </Tooltip>
                          </HStack>
                        </Box>
                      )}
                    </VStack>
                  </Box>
                ))}
              </SimpleGrid>
            </Box>
          </Box>
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
                          data-token-id={nft.tokenId}
                          src={getIPFSUrl(nft.image_cid)}
                          alt={`Photo ${nft.tokenId}`}
                          fallback={<Center h="200px"><Spinner /></Center>}
                          onError={() => handleImageError(nft.tokenId)}
                          objectFit="cover"
                          h="200px"
                          w="100%"
                          key={`${nft.tokenId}-${retryCount[nft.tokenId] || 0}`}
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
                src={getIPFSUrl(selectedImage.image_cid)}
                alt={`Photo ${selectedImage.tokenId}`}
                maxH="90vh"
                objectFit="contain"
                borderRadius="md"
                onClick={(e) => e.stopPropagation()}
                key={`modal-${selectedImage.tokenId}-${retryCount[selectedImage.tokenId] || 0}`}
              />
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}

export default Gallery;