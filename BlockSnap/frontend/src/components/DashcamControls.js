import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Stack,
  IconButton,
  Tooltip,
  Grid
} from '@mui/material';
import {
  Videocam,
  Stop,
  Refresh,
  CheckCircle,
  Error as ErrorIcon
} from '@mui/icons-material';
import VideoPreview from './VideoPreview';

const DashcamControls = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch status periodically
  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(fetchStatus, 2000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const fetchStatus = async () => {
    try {
      const response = await axios.get('/api/dashcam/status');
      if (response.data.status === 'success') {
        setStatus(response.data.data);
      }
    } catch (err) {
      console.error('Error fetching status:', err);
    }
  };

  const startRecording = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.post('/api/dashcam/start');
      
      if (response.data.status === 'success') {
        setIsRecording(true);
        setSessionId(response.data.session_id);
      } else {
        setError('Failed to start recording');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to start recording');
    } finally {
      setLoading(false);
    }
  };

  const stopRecording = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.post('/api/dashcam/stop');
      
      if (response.data.status === 'success') {
        setIsRecording(false);
        setSessionId(null);
      } else {
        setError('Failed to stop recording');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to stop recording');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, margin: 'auto', mt: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <VideoPreview isRecording={isRecording} />
        </Grid>
        
        <Grid item xs={12} md={5}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Dashcam Controls
              </Typography>

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
                <Button
                  variant="contained"
                  color={isRecording ? "error" : "primary"}
                  startIcon={isRecording ? <Stop /> : <Videocam />}
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={loading}
                >
                  {isRecording ? "Stop Recording" : "Start Recording"}
                </Button>

                <Tooltip title="Refresh Status">
                  <IconButton onClick={fetchStatus} disabled={loading}>
                    <Refresh />
                  </IconButton>
                </Tooltip>
              </Stack>

              {loading && (
                <Box display="flex" justifyContent="center" my={2}>
                  <CircularProgress size={24} />
                </Box>
              )}

              {status && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Recording Status
                  </Typography>
                  
                  <Stack spacing={1}>
                    <StatusItem
                      label="Recording Active"
                      value={status.is_recording}
                      icon={status.is_recording ? <CheckCircle color="success" /> : <ErrorIcon color="error" />}
                    />
                    
                    {sessionId && (
                      <StatusItem
                        label="Session ID"
                        value={sessionId}
                      />
                    )}
                    
                    {status.processor_stats && (
                      <>
                        <StatusItem
                          label="Processed Chunks"
                          value={status.processor_stats.total_processed}
                        />
                        <StatusItem
                          label="Successful Uploads"
                          value={status.processor_stats.successful_uploads}
                        />
                        <StatusItem
                          label="Failed Uploads"
                          value={status.processor_stats.failed_uploads}
                        />
                      </>
                    )}
                    
                    {status.recorder_status && (
                      <StatusItem
                        label="Current Chunk"
                        value={status.recorder_status.current_chunk}
                      />
                    )}
                  </Stack>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

const StatusItem = ({ label, value, icon }) => (
  <Box display="flex" alignItems="center">
    <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
      {label}:
    </Typography>
    <Box display="flex" alignItems="center">
      <Typography variant="body2" sx={{ mr: 1 }}>
        {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
      </Typography>
      {icon}
    </Box>
  </Box>
);

export default DashcamControls;
