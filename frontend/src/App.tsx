import React, { useState, useRef, useEffect } from 'react';
import { 
  ChakraProvider, 
  Box, 
  Input, 
  Text, 
  Button, 
  useToast, 
  Flex, 
  Divider,
  Spinner,
  Icon
} from '@chakra-ui/react';
import { ArrowForwardIcon, AttachmentIcon } from '@chakra-ui/icons';
import theme from './theme/theme';

interface Message {
  type: 'user' | 'bot';
  content: string;
}

export default function App() {
  // console.log(`${process.env.REACT_APP_API_URL}`)
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isBotAnswering, setIsBotAnswering] = useState(false);
  const toast = useToast();
  const [isFileSelected, setIsFileSelected] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState();
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const sendMessage = () => {
    setIsBotAnswering(true);
    if (!selectedFile || !input.trim()) {
      toast({
        title: "File upload error.",
        description: "Please provide both a file and some input.",
        status: "error",
        duration: 9000,
        isClosable: true,
      });
      setIsBotAnswering(false);
      return;
      
    }

    // Add the user's message to the chat
    setMessages([...messages, { type: 'user', content: input.trim() }]);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('question', input.trim());
    setInput('');

    fetch(`${process.env.REACT_APP_API_URL}/predict`, {
      method: "POST",
      body: formData,
    })
    .then(async response => {
      console.log(response)
      if (!response.ok) { 
        // If the server response was not 2xx, it's an error 
        const errorData = await response.json(); 
        console.log(errorData)
        throw new Error("An unknown error occurred on server side."); 
      }
      return response.json();
    } )
    .then((data) => {
      console.log('this data',data);
      setMessages((msgs) => [...msgs, { type: 'bot', content: data.result }]);
      setIsBotAnswering(false);
    })
    .catch(error => {
      console.error("Error:", error);
      toast({
        title: "Fetch response error.",
        description: error.message,
        status: "error",
        duration: 9000,
        isClosable: true,
      });
      setIsBotAnswering(false);
    });
  };

  const handleKeyDown = (event: any) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (isFileSelected) sendMessage();
    }
  };

  const handleFileUpload = async (event: any) => {
    event.preventDefault();
    const file = event.target.files ? event.target.files[0] : null;
    const supportedTypes = ['text/csv', 'application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const maxFileSize = 100 * 1024 * 1024; // 100 MB in bytes
    
    if (file) {
      if (!supportedTypes.includes(file.type)) {
        toast({
          title: "File selection error.",
          description: "Unsupported file type. Supported types are .csv, .pdf, .txt, and .docx.",
          status: "error",
          duration: 9000,
          isClosable: true,
        });
        return;
      }

      if (file.size > maxFileSize) {
        toast({
          title: "File selection error.",
          description: 'File size exceeds 100 MB limit.',
          status: "error",
          duration: 9000,
          isClosable: true,
        });
        return;
      }

      console.log(`Selected File: ${file.name}`);
      toast({
        title: "File Selected.",
        description: file.name + " has been selected for upload.",
        status: "success",
        duration: 9000,
        isClosable: true,
      });
      setIsFileSelected(true);
      setSelectedFile(file); 
      setSelectedFileName(file.name);
    }
  };

  return (
    <ChakraProvider theme={theme}>
      <Box
        maxW={{ base: "90vw", md: "85vw", lg: "80vw", xl: "75vw" }} // Responsive width
        height={{ base: "90vh", md: "85vh", lg: "80vh", xl: "75vh" }} // Responsive height
        bg="chatBg"
        p={4}
        margin="40px auto 20px"
        borderRadius="lg"
        boxShadow="md"
        display="flex"
        flexDirection="column"
      >
        <Text fontSize="2xl" color="whiteAlpha.900" mb={4} textAlign="center">DocGenie</Text>
        <Flex 
          direction="column" 
          flex="1" 
          overflowY="auto"
        >
          {messages.map((message, index) => (
            <Flex
              key={index}
              justify={message.type === 'user' ? 'flex-end' : 'flex-start'}
              width="100%"
              px="2"
            >
              <Box
                bg={message.type === 'user' ? 'userMessageBg' : 'botMessageBg'}
                p={3}
                borderRadius="lg"
                maxWidth="80%"
                my={1}
                mx={2}
              >
                <Text fontWeight="bold" fontSize="xs" mb={1}>
                  {message.type.toUpperCase()}
                </Text>
                <Text fontSize="md">{message.content}</Text>
                <div ref={chatEndRef} />
              </Box>
          </Flex>
          ))}
        </Flex>

        {selectedFileName && (
          <Flex justifyContent="flex-end">
            <Text fontSize="sm" mr={2} mt={2} color="gray.500">Referring File: {selectedFileName}</Text>
          </Flex>
        )}

        <Divider my={4} borderColor="gray.600"/>

        <Flex alignItems="center" mt={2}>
          <Button as="label" marginRight="2" isDisabled={isBotAnswering}>
            <Icon as={AttachmentIcon}/>
            <input type="file" hidden onChange={handleFileUpload} accept=".csv,.txt,.docx,.pdf" />
          </Button>
          <Input
            flex="1"
            placeholder="Type your message here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            isDisabled={!isFileSelected || isBotAnswering}
          />
          <Button
            aria-label="Send message"
            onClick={sendMessage}
            isDisabled={!isFileSelected || isBotAnswering}
            marginLeft="2"
            bg="green.600"
            >
            {isBotAnswering ? (
              <Spinner size="xs" position="absolute"/>
            ) : (
              <>
                <Icon as={ArrowForwardIcon}/>
              </>
            )}
          </Button>
          
        </Flex>
      </Box>
    </ChakraProvider>
  );
}