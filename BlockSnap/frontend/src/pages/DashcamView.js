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
  Center,
  Spinner,
} from '@chakra-ui/react';
import Webcam from 'react-webcam';
import { useWeb3React } from '@web3-react/core';
import { MdFiberManualRecord, MdStop } from 'react-icons/md';
import axios from 'axios';

const videoConstraints = {
  width: 1280,
  height: 720,
  facingMode: "environment"
};

function DashcamView() {
  const webcamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [recording, setRecording] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const { account, active } = useWeb3React();
  const toast = useToast();

  // Initialize camera stream
  useEffect(() => {
    async function initializeStream() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: videoConstraints,
          audio: false 
        });
        streamRef.current = stream;
        setIsInitialized(true);
      } catch (err) {
        toast({
          title: 'Camera Error',
          description: 'Failed to access camera: ' + err.message,
          status: 'error',
          duration: 5000,
        });
      }
    }

    if (active && !isInitialized) {
      initializeStream();
    }

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [active, toast]);

  // Recording timer
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
    try {
      if (!active) {
        toast({
          title: 'Wallet not connected',
          description: 'Please connect your wallet first.',
          status: 'error',
          duration: 5000,
        });
        return;
      }

      if (!streamRef.current) {
        toast({
          title: 'Camera not ready',
          description: 'Please wait for camera initialization.',
          status: 'error',
          duration: 5000,
        });
        return;
      }

      // Start backend recording session
      const response = await axios.post('http://localhost:5000/dashcam/start');
      if (!response.data.session_id) {
        throw new Error('Failed to start recording session');
      }
      setSessionId(response.data.session_id);

      // Start local recording
      mediaRecorderRef.current = new MediaRecorder(streamRef.current, {
        mimeType: 'video/webm;codecs=h264',
        videoBitsPerSecond: 2500000 // 2.5 Mbps
      });

      mediaRecorderRef.current.ondataavailable = async (e) => {
        if (e.data && e.data.size > 0) {
          const chunk = new Blob([e.data], { type: 'video/webm' });
          const formData = new FormData();
          formData.append('video', chunk);
          formData.append('session_id', sessionId);
          formData.append('timestamp', Date.now());
          
          try {
            await axios.post('http://localhost:5000/dashcam/chunk', formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
            });
          } catch (err) {
            console.error('Failed to upload chunk:', err);
          }
        }
      };

      mediaRecorderRef.current.start(15000); // Create a chunk every 15 seconds
      setRecording(true);
      setRecordingTime(0);

      toast({
        title: 'Recording Started',
        description: 'Video recording has begun.',
        status: 'success',
        duration: 3000,
      });

    } catch (error) {
      toast({
        title: 'Error',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const stopRecording = async () => {
    try {
      if (mediaRecorderRef.current && recording) {
        mediaRecorderRef.current.stop();
        await axios.post('http://localhost:5000/dashcam/stop');
        setRecording(false);
        setSessionId(null);
        
        toast({
          title: 'Recording Stopped',
          description: 'Video session has been saved.',
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  if (!isInitialized) {
    return (
      <Center h="500px">
        <VStack spacing={4}>
          <Spinner size="xl" />
          <Text>Initializing camera...</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box p={4}>
      <VStack spacing={4} align="stretch">
        <Box borderWidth={1} borderRadius="lg" overflow="hidden">
          <Webcam
            ref={webcamRef}
            audio={false}
            videoConstraints={videoConstraints}
            width="100%"
          />
        </Box>

        <HStack justify="center" spacing={4}>
          {!recording ? (
            <Button
              leftIcon={<MdFiberManualRecord />}
              colorScheme="red"
              onClick={startRecording}
              isDisabled={!active}
            >
              Start Recording
            </Button>
          ) : (
            <Button
              leftIcon={<MdStop />}
              colorScheme="gray"
              onClick={stopRecording}
            >
              Stop Recording
            </Button>
          )}
        </HStack>

        {recording && (
          <VStack spacing={2}>
            <Badge colorScheme="red">Recording</Badge>
            <Text>Duration: {new Date(recordingTime * 1000).toISOString().substr(11, 8)}</Text>
            <Progress size="sm" isIndeterminate colorScheme="red" w="100%" />
          </VStack>
        )}
      </VStack>
    </Box>
  );
}

export default DashcamView;