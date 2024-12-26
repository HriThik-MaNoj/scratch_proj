import React, { useState } from 'react';
import {
  Box,
  VStack,
  Button,
  Text,
  Input,
  useToast,
  Heading,
  Divider,
  HStack,
  Icon,
  Badge,
  Image,
  FormControl,
  FormLabel,
} from '@chakra-ui/react';
import { useDropzone } from 'react-dropzone';
import { MdCloudUpload, MdVerified, MdError } from 'react-icons/md';
import axios from 'axios';

function VerifyMedia() {
  const [verificationResult, setVerificationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cidInput, setCidInput] = useState('');
  const toast = useToast();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png'],
      'video/*': ['.mp4', '.webm']
    },
    maxFiles: 1,
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        await verifyFile(acceptedFiles[0]);
      }
    },
  });

  const verifyFile = async (file) => {
    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('http://localhost:5000/verify/file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setVerificationResult(response.data);
    } catch (error) {
      toast({
        title: 'Error',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const verifyCID = async () => {
    if (!cidInput) {
      toast({
        title: 'Error',
        description: 'Please enter a CID',
        status: 'error',
        duration: 5000,
      });
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:5000/verify/${cidInput}`);
      setVerificationResult(response.data);
    } catch (error) {
      toast({
        title: 'Error',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box maxW="container.lg" mx="auto">
      <VStack spacing={8} align="stretch">
        <Heading color="white">Verify Media Authenticity</Heading>
        
        <Box
          {...getRootProps()}
          p={10}
          bg="gray.800"
          borderRadius="lg"
          borderWidth={2}
          borderStyle="dashed"
          borderColor={isDragActive ? "blue.500" : "gray.600"}
          cursor="pointer"
          _hover={{
            borderColor: "blue.500",
          }}
        >
          <input {...getInputProps()} />
          <VStack spacing={4}>
            <Icon as={MdCloudUpload} w={12} h={12} color="gray.400" />
            <Text color="gray.400" textAlign="center">
              {isDragActive
                ? "Drop the file here"
                : "Drag and drop a file here, or click to select"}
            </Text>
          </VStack>
        </Box>

        <Divider />

        <VStack spacing={4}>
          <FormControl>
            <FormLabel color="white">Or verify by IPFS CID</FormLabel>
            <HStack>
              <Input
                placeholder="Enter IPFS CID"
                value={cidInput}
                onChange={(e) => setCidInput(e.target.value)}
                bg="gray.800"
                color="white"
                borderColor="gray.600"
              />
              <Button
                colorScheme="blue"
                onClick={verifyCID}
                isLoading={loading}
              >
                Verify
              </Button>
            </HStack>
          </FormControl>
        </VStack>

        {verificationResult && (
          <Box bg="gray.800" p={6} borderRadius="lg">
            <VStack spacing={4} align="stretch">
              <HStack>
                <Icon
                  as={verificationResult.exists_on_blockchain ? MdVerified : MdError}
                  w={6}
                  h={6}
                  color={verificationResult.exists_on_blockchain ? "green.500" : "red.500"}
                />
                <Text color="white" fontSize="lg" fontWeight="bold">
                  Verification Result
                </Text>
              </HStack>

              <HStack>
                <Badge
                  colorScheme={verificationResult.exists_on_ipfs ? "green" : "red"}
                >
                  IPFS Status
                </Badge>
                <Text color="gray.300">
                  {verificationResult.exists_on_ipfs ? "Content Found" : "Content Not Found"}
                </Text>
              </HStack>

              <HStack>
                <Badge
                  colorScheme={verificationResult.exists_on_blockchain ? "green" : "red"}
                >
                  Blockchain Status
                </Badge>
                <Text color="gray.300">
                  {verificationResult.exists_on_blockchain
                    ? `Verified - Owned by ${verificationResult.owner}`
                    : "Not Found"}
                </Text>
              </HStack>

              {verificationResult.ipfs_url && (
                <Box mt={4}>
                  <Text color="white" mb={2}>Preview:</Text>
                  <Image
                    src={verificationResult.ipfs_url}
                    alt="Verified content"
                    maxH="300px"
                    borderRadius="md"
                  />
                </Box>
              )}
            </VStack>
          </Box>
        )}
      </VStack>
    </Box>
  );
}

export default VerifyMedia; 