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
  const [error, setError] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [latestChunk, setLatestChunk] = useState(null);

  // Handle preview stream
  useEffect(() => {
    if (!isRecording) {
      return;
    }

    const videoElement = videoRef.current;
    if (!videoElement) return;

    // Create MediaSource
    const mediaSource = new MediaSource();
    videoElement.src = URL.createObjectURL(mediaSource);

    mediaSource.addEventListener('sourceopen', () => {
      const sourceBuffer = mediaSource.addSourceBuffer('video/mp4; codecs="avc1.42E01E"');
      
      // Function to fetch and append chunks
      const fetchChunk = async () => {
        try {
          const response = await fetch('/api/dashcam/latest-chunk');
          if (!response.ok) throw new Error('Failed to fetch chunk');
          
          const data = await response.json();
          if (data.status === 'success') {
            setLatestChunk(data.data);
            
            // Fetch video data
            const videoResponse = await fetch(data.data.video_url);
            const videoBuffer = await videoResponse.arrayBuffer();
            
            // Append to source buffer
            if (!sourceBuffer.updating) {
              sourceBuffer.appendBuffer(videoBuffer);
            }
          }
        } catch (err) {
          console.error('Error fetching chunk:', err);
        }
      };

      // Fetch chunks periodically
      const interval = setInterval(fetchChunk, 1000);
      return () => clearInterval(interval);
    });

    return () => {
      URL.revokeObjectURL(videoElement.src);
    };
  }, [isRecording]);

  // Handle preview stream for live view
  useEffect(() => {
    if (!isRecording) {
      return;
    }

    const videoElement = videoRef.current;
    if (!videoElement) return;

    // Set up preview stream
    const previewUrl = '/api/dashcam/preview';
    
    // Create image element for preview
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      
      // Draw frame
      ctx.drawImage(img, 0, 0);
      
      // Update video texture
      if (videoElement) {
        videoElement.srcObject = canvas.captureStream(30);
      }
    };

    // Fetch frames
    const fetchFrame = () => {
      img.src = `${previewUrl}?t=${Date.now()}`;
    };

    const interval = setInterval(fetchFrame, 1000 / 30);
    return () => clearInterval(interval);
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
          
          {!isRecording && (
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
                Start recording to see preview
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
