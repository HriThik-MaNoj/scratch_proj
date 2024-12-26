import { extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
  config: {
    initialColorMode: 'dark',
    useSystemColorMode: false,
  },
  styles: {
    global: {
      body: {
        bg: 'gray.900',
        color: 'white',
      },
    },
  },
  components: {
    Button: {
      defaultProps: {
        colorScheme: 'blue',
      },
    },
    Modal: {
      baseStyle: {
        dialog: {
          bg: 'gray.800',
        },
      },
    },
  },
  colors: {
    gray: {
      700: '#2D3748',
      800: '#1A202C',
      900: '#171923',
    },
  },
});

export default theme; 