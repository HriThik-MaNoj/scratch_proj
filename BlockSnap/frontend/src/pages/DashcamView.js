import React, { useRef, useState, useEffect } from 'react';
import {
  Box,
  Button,
  VStack,
  HStack,
  Text,
  useToast,
  Progress,
  Badge,
} from '@chakra-ui/react';
import Webcam from 'react-webcam';
import { useWeb3React } from '@web3-react/core';
import { MdFiberManualRecord, MdStop, MdSave } from 'react-icons/md';
import axios from 'axios';

function DashcamView() {
  const webcamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const [recording, setRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [recordingTime, setRecordingTime] = useState(0);
  const { account, active } = useWeb3React();
  const toast = useToast();

  useEffect(() => {
    let interval;
    if (recording) {
      interval = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [recording]);

  const startRecording = async () => {
    if (!active) {
      toast({
        title: 'Wallet not connected',
        description: 'Please connect your MetaMask wallet first.',
        status: 'error',
        duration: 5000,
      });
      return;
    }

    chunksRef.current = [];
    const stream = webcamRef.current.video.srcObject;
    mediaRecorderRef.current = new MediaRecorder(stream, {
      mimeType: 'video/webm',
    });

    mediaRecorderRef.current.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunksRef.current.push(e.data);
      }
    };

    mediaRecorderRef.current.start(1000); // Collect data every second
    setRecording(true);
    setRecordingTime(0);
  };

  const stopRecording = () => {
    mediaRecorderRef.current.stop();
    setRecording(false);
  };

  const saveRecording = async () => {
    try {
      const blob = new Blob(chunksRef.current, { type: 'video/webm' });
      const file = new File([blob], 'dashcam.webm', { type: 'video/webm' });

      const formData = new FormData();
      formData.append('video', file);
      formData.append('wallet_address', account);
      formData.append('duration', recordingTime);

      const result = await axios.post('http://localhost:5000/capture/video', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast({
        title: 'Success!',
        description: `Video saved and minted as NFT. Token ID: ${result.data.data.token_id}`,
        status: 'success',
        duration: 5000,
      });

      chunksRef.current = [];
      setRecordingTime(0);
    } catch (error) {
      toast({
        title: 'Error',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const videoConstraints = {
    width: 1280,
    height: 720,
    facingMode: "environment"
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
            audio={true}
            ref={webcamRef}
            videoConstraints={videoConstraints}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
          
          {recording && (
            <Badge
              position="absolute"
              top="4"
              right="4"
              colorScheme="red"
              variant="solid"
              display="flex"
              alignItems="center"
            >
              <Box
                as="span"
                w="2"
                h="2"
                borderRadius="full"
                bg="red.500"
                mr="2"
                animation="blink 1s infinite"
              />
              Recording {formatTime(recordingTime)}
            </Badge>
          )}

          <Box
            position="absolute"
            bottom="4"
            left="50%"
            transform="translateX(-50%)"
            w="90%"
          >
            <VStack spacing={4}>
              <Progress
                value={(recordingTime / (5 * 60)) * 100}
                w="100%"
                colorScheme="blue"
                bg="gray.700"
                borderRadius="full"
                display={recording ? 'block' : 'none'}
              />
              
              <HStack spacing={4}>
                {!recording ? (
                  <Button
                    leftIcon={<MdFiberManualRecord />}
                    colorScheme="red"
                    size="lg"
                    onClick={startRecording}
                  >
                    Start Recording
                  </Button>
                ) : (
                  <>
                    <Button
                      leftIcon={<MdStop />}
                      colorScheme="red"
                      size="lg"
                      onClick={stopRecording}
                    >
                      Stop
                    </Button>
                    <Button
                      leftIcon={<MdSave />}
                      colorScheme="blue"
                      size="lg"
                      onClick={saveRecording}
                    >
                      Save & Mint
                    </Button>
                  </>
                )}
              </HStack>
            </VStack>
          </Box>
        </Box>

        <Text color="gray.400">
          {active
            ? 'Record dashcam footage and mint it as an NFT'
            : 'Please connect your wallet to mint NFTs'}
        </Text>
      </VStack>
    </Box>
  );
}

export default DashcamView; 