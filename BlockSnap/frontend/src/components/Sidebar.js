import React from 'react';
import { Box, VStack, Icon, Text, Link } from '@chakra-ui/react';
import { NavLink as RouterLink, useLocation } from 'react-router-dom';
import {
  MdDashboard,
  MdCamera,
  MdVideocam,
  MdVerifiedUser,
  MdPhotoLibrary,
} from 'react-icons/md';

const MenuItem = ({ icon, children, to }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      as={RouterLink}
      to={to}
      style={{ textDecoration: 'none' }}
      _focus={{ boxShadow: 'none' }}
    >
      <Box
        display="flex"
        alignItems="center"
        p="4"
        mx="4"
        borderRadius="lg"
        role="group"
        cursor="pointer"
        bg={isActive ? 'blue.400' : 'transparent'}
        _hover={{
          bg: 'blue.400',
        }}
        transition="all 0.3s"
      >
        <Icon
          mr="4"
          fontSize="16"
          as={icon}
          color={isActive ? 'white' : 'gray.400'}
          _groupHover={{ color: 'white' }}
        />
        <Text color={isActive ? 'white' : 'gray.400'} _groupHover={{ color: 'white' }}>
          {children}
        </Text>
      </Box>
    </Link>
  );
};

function Sidebar() {
  return (
    <Box
      bg="gray.800"
      w="64"
      h="calc(100vh - 4rem)"
      pos="sticky"
      top="4rem"
      borderRight="1px"
      borderColor="gray.700"
    >
      <VStack spacing="1" align="stretch" py="4">
        <MenuItem icon={MdDashboard} to="/">
          Dashboard
        </MenuItem>
        <MenuItem icon={MdCamera} to="/camera">
          Camera
        </MenuItem>
        <MenuItem icon={MdVideocam} to="/dashcam">
          Dashcam
        </MenuItem>
        <MenuItem icon={MdVerifiedUser} to="/verify">
          Verify Media
        </MenuItem>
        <MenuItem icon={MdPhotoLibrary} to="/gallery">
          Gallery
        </MenuItem>
      </VStack>
    </Box>
  );
}

export default Sidebar; 