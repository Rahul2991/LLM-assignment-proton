// theme.js or theme.ts
import { extendTheme } from '@chakra-ui/react';

const config = {
  initialColorMode: 'dark',
  useSystemColorMode: false,
};

const theme = extendTheme({
  config,
  styles: {
    global: {
      body: {
        bg: 'gray.800',
        color: 'white',
      },
      '::-webkit-scrollbar': {
        width: '12px',
        borderRadius: '8px',
        backgroundColor: `rgba(0, 0, 0, 0.05)`, // Scrollbar background
      },
      '::-webkit-scrollbar-thumb': {
        borderRadius: '8px',
        backgroundColor: `rgba(0, 0, 0, 0.5)`, // Scrollbar thumb
      },
    },
  },
  // Your color definitions
  colors: {
    chatBg: '#2D3748',
    userMessageBg: '#3182CE', // Assuming this is working
    botMessageBg: '#4A5568', // Assuming this is working
    fontColor: '#ffffff'
  },
});

export default theme;