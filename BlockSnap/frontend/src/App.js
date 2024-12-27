import React from 'react';
import { ChakraProvider, Box } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Web3ReactProvider } from '@web3-react/core';
import { ethers } from 'ethers';

// Components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import DashcamControls from './components/DashcamControls';

// Pages
import Dashboard from './pages/Dashboard';
import CameraView from './pages/CameraView';
import DashcamView from './pages/DashcamView';
import VerifyMedia from './pages/VerifyMedia';
import Gallery from './pages/Gallery';

// Theme
import theme from './theme';

function getLibrary(provider) {
  return new ethers.providers.Web3Provider(provider);
}

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Web3ReactProvider getLibrary={getLibrary}>
        <Router>
          <Box minH="100vh" bg="gray.900">
            <Navbar />
            <Box display="flex">
              <Sidebar />
              <Box flex="1" p="4">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/camera" element={<CameraView />} />
                  <Route path="/dashcam" element={<DashcamView />} />
                  <Route path="/verify" element={<VerifyMedia />} />
                  <Route path="/gallery" element={<Gallery />} />
                  <Route path="/dashcam-controls" element={<DashcamControls />} />
                </Routes>
              </Box>
            </Box>
          </Box>
        </Router>
      </Web3ReactProvider>
    </ChakraProvider>
  );
}

export default App; 