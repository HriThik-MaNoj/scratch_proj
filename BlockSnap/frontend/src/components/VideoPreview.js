import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  Stack,
  IconButton,
  Tooltip
} from '@mui/material';
import { Fullscreen, FullscreenExit } from '@mui/icons-material';

const VideoPreview = ({ isRecording }) => {
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const [error, setError] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [latestChunk, setLatestChunk] = useState(null);

  // Initialize camera stream
  useEffect(() => {
    async function initializeCamera() {
      try {
        // Get camera access
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1920 },
            height: { ideal: 1080 },
            frameRate: { ideal: 30 }
          },
          audio: true
        });

        // Store stream reference
        streamRef.current = stream;

        // Set stream to video element
        const videoElement = videoRef.current;
        if (videoElement) {
          videoElement.srcObject = stream;
        }

        // Initialize MediaRecorder
        mediaRecorderRef.current = new MediaRecorder(stream, {
          mimeType: 'video/webm;codecs=vp9',
          videoBitsPerSecond: 2500000 // 2.5 Mbps
        });

      } catch (err) {
        console.error('Error accessing camera:', err);
        setError('Failed to access camera. Please make sure you have granted camera permissions.');
      }
    }

    initializeCamera();

    // Cleanup
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Handle recording state
  useEffect(() => {
    if (!mediaRecorderRef.current || !streamRef.current) return;

    if (isRecording) {
      try {
        mediaRecorderRef.current.start();
      } catch (err) {
        console.error('Error starting recording:', err);
        setError('Failed to start recording');
      }
    } else {
      try {
        if (mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop();
        }
      } catch (err) {
        console.error('Error stopping recording:', err);
      }
    }
  }, [isRecording]);

  const toggleFullscreen = () => {
    const element = videoRef.current;
    
    if (!document.fullscreenElement) {
      element.requestFullscreen().catch(err => {
        setError(`Error attempting to enable fullscreen: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <Card elevation={3} sx={{ width: '100%', mt: 2 }}>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 1 }}>
          <Typography variant="h6">
            Live Preview
          </Typography>
          <Tooltip title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}>
            <IconButton onClick={toggleFullscreen}>
              {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
            </IconButton>
          </Tooltip>
        </Stack>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box
          sx={{
            position: 'relative',
            width: '100%',
            paddingTop: '56.25%', // 16:9 aspect ratio
            bgcolor: 'black'
          }}
        >
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'contain'
            }}
          />
          
          {!isRecording && !streamRef.current && (
            <Box
              sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center'
              }}
            >
              <Typography variant="body1" color="white">
                Initializing camera...
              </Typography>
            </Box>
          )}
        </Box>

        {latestChunk && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Latest Chunk: #{latestChunk.sequence_number}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default VideoPreview;
