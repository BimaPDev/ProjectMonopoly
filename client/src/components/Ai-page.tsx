"use client";

import React, { useState } from "react";
import { Box, Menu, MenuItem, Stack } from "@mui/material";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { RecommendationForm } from "@/components/ui/recommendationForm"; // Import the form component

export function AiPage() {
  const { theme } = useTheme(); // Access the theme
  const [anchorEl, setAnchorEl] = useState(null); // Tracks the menu anchor
  const [selectedModel, setSelectedModel] = useState(""); // Tracks the selected model
  const [showForm, setShowForm] = useState(false); // Tracks form visibility
  const open = Boolean(anchorEl);

  // Handlers for menu and model selection
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

  const handleGetRecommendation = () => {
    if (selectedModel) {
      setShowForm(true); // Show the form if a model is selected
    } else {
      alert("Please select a model before getting recommendations.");
    }
  };

  const handleFormSubmit = (data) => {
    console.log("Form submitted with data:", data);
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
          <Button onClick={handleGetRecommendation}>Get Recommendation</Button>
        </Stack>

        <Menu
          anchorEl={anchorEl}
          open={open}
          onClose={handleClose}
        >
          <MenuItem onClick={() => handleModelSelect("Chat GPT")}>Chat GPT</MenuItem>
          <MenuItem onClick={() => handleModelSelect("DeepSeek")}>DeepSeek</MenuItem>
        </Menu>
      </Box>

      
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
            boxShadow: "0 2px 5px rgba(0, 0, 0, 0.1)" 
          }}
        >
          {showForm && (
            <RecommendationForm onSubmit={handleFormSubmit} />
          )}
        </Box>
      </Box>
    </Box>
  );
}