import React from 'react';
import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Heading,
  Text,
  useColorModeValue,
  Icon,
  Flex,
  Button,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { useWeb3React } from '@web3-react/core';
import {
  MdCamera,
  MdVideocam,
  MdVerifiedUser,
  MdPhotoLibrary,
} from 'react-icons/md';

function StatsCard({ title, stat, icon, description, onClick }) {
  return (
    <Stat
      px={{ base: 2, md: 4 }}
      py="5"
      bg="gray.800"
      borderRadius="lg"
      borderWidth="1px"
      borderColor="gray.700"
      cursor="pointer"
      transition="all 0.3s"
      _hover={{
        transform: 'translateY(-2px)',
        shadow: 'lg',
        borderColor: 'blue.400',
      }}
      onClick={onClick}
    >
      <Flex justifyContent="space-between">
        <Box pl={{ base: 2, md: 4 }}>
          <StatLabel fontWeight="medium" isTruncated>
            {title}
          </StatLabel>
          <StatNumber fontSize="2xl" fontWeight="medium">
            {stat}
          </StatNumber>
          <StatHelpText>{description}</StatHelpText>
        </Box>
        <Box
          my="auto"
          color={useColorModeValue('gray.800', 'gray.200')}
          alignContent="center"
        >
          <Icon as={icon} w={8} h={8} />
        </Box>
      </Flex>
    </Stat>
  );
}

function Dashboard() {
  const navigate = useNavigate();
  const { active, account } = useWeb3React();

  return (
    <Box maxW="7xl" mx="auto" pt={5} px={{ base: 2, sm: 12, md: 17 }}>
      <Box mb={10}>
        <Heading color="white" mb={4}>
          Welcome to BlockSnap
        </Heading>
        <Text color="gray.400">
          Capture, secure, and verify your media on the blockchain
        </Text>
      </Box>

      {!active ? (
        <Box
          p={8}
          bg="gray.800"
          borderRadius="lg"
          textAlign="center"
          borderWidth="1px"
          borderColor="gray.700"
        >
          <Text fontSize="xl" mb={4} color="white">
            Connect your wallet to get started
          </Text>
          <Text color="gray.400" mb={6}>
            Use MetaMask to interact with the blockchain and mint NFTs
          </Text>
        </Box>
      ) : (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={{ base: 5, lg: 8 }}>
          <StatsCard
            title="Camera"
            stat="Capture"
            icon={MdCamera}
            description="Take photos and mint as NFTs"
            onClick={() => navigate('/camera')}
          />
          <StatsCard
            title="Dashcam"
            stat="Record"
            icon={MdVideocam}
            description="Record and secure video footage"
            onClick={() => navigate('/dashcam')}
          />
          <StatsCard
            title="Verify"
            stat="Authenticate"
            icon={MdVerifiedUser}
            description="Verify media authenticity"
            onClick={() => navigate('/verify')}
          />
          <StatsCard
            title="Gallery"
            stat="View All"
            icon={MdPhotoLibrary}
            description="Browse your NFT collection"
            onClick={() => navigate('/gallery')}
          />
        </SimpleGrid>
      )}

      {active && (
        <Box mt={10}>
          <Heading size="md" mb={4} color="white">
            Your Stats
          </Heading>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={{ base: 5, lg: 8 }}>
            <Stat
              bg="gray.800"
              p={4}
              borderRadius="lg"
              borderWidth="1px"
              borderColor="gray.700"
            >
              <StatLabel>Connected Account</StatLabel>
              <StatNumber fontSize="md">
                {`${account.slice(0, 6)}...${account.slice(-4)}`}
              </StatNumber>
            </Stat>
            {/* Add more stats here as needed */}
          </SimpleGrid>
        </Box>
      )}
    </Box>
  );
}

export default Dashboard; 