"use client";

import React, { useState } from "react";
import { Box, Menu, MenuItem, Stack } from "@mui/material";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import ChatComponent from "@/components/ui/chatComponent";  // Import the ChatComponent

export function AiPage() {
  const { theme } = useTheme();
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedModel, setSelectedModel] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [showChat, setShowChat] = useState(false);  // State to toggle ChatComponent visibility

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleModelSelect = (model) => {
    setSelectedModel(model);
    handleClose();
  };

  const handleChatToggle = () => {
    setShowChat(!showChat);  // Toggle ChatComponent visibility
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        bgcolor: theme,
        color: theme,
        p: 2,
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          color: theme,
          borderRadius: 2,
          maxWidth: "400px",
          width: "100%",
        }}
      >
        <Stack spacing={2} direction="row">
          <Button onClick={handleClick}>
            {selectedModel ? `Model: ${selectedModel}` : "Select Model"}
          </Button>

          {/* Button to toggle ChatComponent with gray styling when no model is selected */}
          <Button
            onClick={handleChatToggle}
            sx={{
              backgroundColor: selectedModel ? "primary.main" : "gray",  // Gray until a model is selected
              color: selectedModel ? "white" : "black",  // Ensure text color is readable
              "&:hover": {
                backgroundColor: selectedModel ? "primary.dark" : "gray",
              },
            }}
            disabled={!selectedModel}  // Disable button until a model is selected
          >
            {showChat ? "Hide Chat" : "Show Chat"}
          </Button>
        </Stack>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}  // Adjust to conditionally open the menu
          onClose={handleClose}
        >
          <MenuItem onClick={() => handleModelSelect("Chat GPT")}>Chat GPT</MenuItem>
          <MenuItem onClick={() => handleModelSelect("DeepSeek")}>DeepSeek</MenuItem>
        </Menu>
      </Box>

      {/* Conditional rendering of the form */}
      <Box
        sx={{
          position: "relative",
          width: "100%",
        }}
      >
        <Box
          sx={{
            position: "absolute",
            top: "15px",
            left: 0,
            width: "400px",
            padding: "0px",
            borderRadius: "5px",
            boxShadow: "0 2px 5px rgba(0, 0, 0, 0.1)",
          }}
        >
    
        </Box>
      </Box>

      {/* Conditional rendering of the ChatComponent */}
      {showChat && <ChatComponent />}
    </Box>
  );
}
