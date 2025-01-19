
"use client";

import { Box, Button, Stack, TextField, CircularProgress } from "@mui/material";
import { useState, useRef, useEffect } from "react";

const ChatComponent = () => {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello, Welcome to DogWood Gaming's AI virtual agent, how may I help you?",
    },
  ]);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingChat, setLoadingChat] = useState(true); // State for showing loading screen

  const sendMessage = async () => {
    if (!message.trim() || isLoading) return;
    setIsLoading(true);

    if (!message.trim()) return; // Don't send empty messages

    setMessage("");
    setMessages((messages) => [
      ...messages,
      { role: "user", content: message }, // Add the user's message to the chat
      { role: "assistant", content: "" }, // Add a placeholder for the assistant's response
    ]);

    try {
      // Send the message to the server
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify([...messages, { role: "user", content: message }]),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const reader = response.body.getReader(); // Get a reader to read the response body
      const decoder = new TextDecoder(); // Create a decoder to decode the response text

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        setMessages((messages) => {
          let lastMessage = messages[messages.length - 1]; // Get the last message (assistant's placeholder)
          let otherMessages = messages.slice(0, messages.length - 1); // Get all other messages
          return [
            ...otherMessages,
            { ...lastMessage, content: lastMessage.content + text }, // Append the decoded text to the assistant's message
          ];
        });
      }
    } catch (error) {
      // error handling
      console.error("Error:", error);
      setMessages((messages) => [
        ...messages,
        {
          role: "assistant",
          content:
            "I'm sorry, but I encountered an error. Please try again later.",
        },
      ]);
    }
    setIsLoading(false);
  };

  const handleKeyPress = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (!loadingChat) {
      scrollToBottom();
    }
  }, [messages, loadingChat]);

  // Simulate loading for the chat box
  useEffect(() => {
    const timeout = setTimeout(() => {
      setLoadingChat(false); // After 2 seconds, show the chat
    }, 2000); // Adjust the duration as needed

    return () => clearTimeout(timeout);
  }, []);


  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
    >
      <Stack
        direction={"column"}
        width="500px"
        height="700px"
        border="2px solid white"
        p={2}
        spacing={3}
      >
         {/* Loading screen */}
         {loadingChat ? (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            flexGrow={1}
          >
            <CircularProgress size={60} color="primary" />
          </Box>
        ) : (
          <>
            <Stack
              direction={"column"}
              spacing={2}
              flexGrow={1}
              overflow="auto"
              maxHeight="100%"
            >
              {messages.map((message, index) => (
                <Box
                  key={index}
                  display="flex"
                  justifyContent={
                    message.role === "assistant" ? "flex-start" : "flex-end"
                  }
                >
                  <Box
                    bgcolor={
                      message.role === "assistant"
                        ? "#1A73E8" // Blue for assistant
                        : "#34B7F1" // Light blue for user
                    }
                    color="white"
                    borderRadius="16px"
                    p={2}
                    maxWidth="70%"
                    wordWrap="break-word"
                    sx={{
                      boxShadow: 1,
                    }}
                  >
                    {message.content}
                  </Box>
                </Box>
              ))}
              <div ref={messagesEndRef} />
            </Stack>
            <Stack direction={"row"} spacing={2}>
              <TextField
                label="Type your message..."
                fullWidth
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                InputProps={{
                  style: { color: "white", backgroundColor: "#333" }, // Dark input background
                }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    "&.Mui-focused fieldset": {
                      borderColor: "white", // Change border color when focused to white
                    },
                  },
                }}
              />
              <Button
                variant="contained"
                onClick={sendMessage}
                disabled={isLoading}
                sx={{
                  backgroundColor: "#1A73E8",
                  "&:hover": {
                    backgroundColor: "#0c5ed3", // Darker on hover
                  },
                }}
              >
                {isLoading ? (
                  "Sending..."
                ) : (
                  <>
                    Send <span className="fas fa-arrow-circle-right"></span>
                  </>
                )}
              </Button>
            </Stack>
          </>
        )}
      </Stack>
    </Box>
  );
};

export default ChatComponent;