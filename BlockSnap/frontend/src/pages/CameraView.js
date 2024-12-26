import React, { useRef, useState, useCallback } from 'react';
import {
  Box,
  Button,
  VStack,
  HStack,
  Text,
  useToast,
  Image,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure,
} from '@chakra-ui/react';
import Webcam from 'react-webcam';
import { useWeb3React } from '@web3-react/core';
import { MdCamera, MdRefresh } from 'react-icons/md';
import axios from 'axios';

function CameraView() {
  const webcamRef = useRef(null);
  const [imgSrc, setImgSrc] = useState(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { account, active } = useWeb3React();
  const toast = useToast();

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImgSrc(imageSrc);
    onOpen();
  }, [webcamRef, onOpen]);

  const handleSave = async () => {
    if (!active) {
      toast({
        title: 'Wallet not connected',
        description: 'Please connect your MetaMask wallet first.',
        status: 'error',
        duration: 5000,
      });
      return;
    }

    try {
      toast({
        title: 'Processing',
        description: 'Uploading to IPFS and minting NFT...',
        status: 'info',
        duration: null,
        isClosable: false,
      });

      // Send to backend
      const result = await axios.post('http://localhost:5000/capture', {
        wallet_address: account,
        image_data: imgSrc
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const { token_id, image_url, transaction_hash } = result.data.data;

      toast({
        title: 'Success!',
        description: (
          <VStack align="start">
            <Text>NFT successfully minted!</Text>
            <Text>Token ID: {token_id}</Text>
            <Text>
              <a href={`https://testnet.buildbear.io/tx/${transaction_hash}`} target="_blank" rel="noopener noreferrer">
                View on BuildBear Explorer
              </a>
            </Text>
          </VStack>
        ),
        status: 'success',
        duration: 10000,
        isClosable: true,
      });

      onClose();
      setImgSrc(null);
      
      // Redirect to gallery
      window.location.href = '/gallery';
    } catch (error) {
      console.error('Error:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.error || error.message || 'Failed to mint NFT',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const videoConstraints = {
    width: 1280,
    height: 720,
    facingMode: "user"
  };

  return (
    <Box>
      <VStack spacing={8} align="center">
        <Box
          w="100%"
          maxW="1280px"
          h="720px"
          bg="gray.800"
          borderRadius="lg"
          overflow="hidden"
          position="relative"
        >
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            videoConstraints={videoConstraints}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
          <Box
            position="absolute"
            bottom="4"
            left="50%"
            transform="translateX(-50%)"
          >
            <HStack spacing={4}>
              <Button
                leftIcon={<MdCamera />}
                colorScheme="blue"
                size="lg"
                onClick={capture}
              >
                Capture Photo
              </Button>
              <Button
                leftIcon={<MdRefresh />}
                colorScheme="gray"
                size="lg"
                onClick={() => setImgSrc(null)}
              >
                Reset
              </Button>
            </HStack>
          </Box>
        </Box>

        <Text color="gray.400">
          {active
            ? 'Click capture to take a photo and mint it as an NFT'
            : 'Please connect your wallet to mint NFTs'}
        </Text>
      </VStack>

      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent bg="gray.800">
          <ModalHeader color="white">Preview Capture</ModalHeader>
          <ModalBody>
            <Image src={imgSrc} alt="Captured" borderRadius="md" />
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" mr={3} onClick={handleSave}>
              Save & Mint NFT
            </Button>
            <Button variant="ghost" onClick={onClose} color="white">
              Cancel
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
}

export default CameraView; 