"use client";

import React, { useState } from "react";
import { Box, TextField, Button, Stack } from "@mui/material";

export function RecommendationForm({ onSubmit }) {
  const [param1, setParam1] = useState("");
  const [param2, setParam2] = useState("");
  const [param3, setParam3] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    // Send form data back to the parent component
    onSubmit({ param1, param2, param3 });
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
        bgcolor: "#3b3a38",
        color: "#ffffff",
        p: 4,
        borderRadius: 2,
        maxWidth: "400px",
        width: "100%",
        mx: "auto",
      }}
    >
      <h2>Recommendation Form</h2>

      <TextField
        label="Website One"
        value={param1}
        onChange={(e) => setParam1(e.target.value)}
        variant="outlined"
        fullWidth
        required
        InputLabelProps={{
          style: { color: "#ffffff" },
        }}
        InputProps={{
          style: { color: "#ffffff", borderColor: "#ffffff" },
        }}
      />

      <TextField
        label="Parameter 2"
        value={param2}
        onChange={(e) => setParam2(e.target.value)}
        variant="outlined"
        fullWidth
        required
        InputLabelProps={{
          style: { color: "#ffffff" },
        }}
        InputProps={{
          style: { color: "#ffffff", borderColor: "#ffffff" },
        }}
      />

      <TextField
        label="Parameter 3"
        value={param3}
        onChange={(e) => setParam3(e.target.value)}
        variant="outlined"
        fullWidth
        required
        
        InputLabelProps={{
          style: { color: "#ffffff" },
        }}
        InputProps={{
          style: { color: "#ffffff", borderColor: "#ffffff" },
        }}
      />

      <Stack spacing={2} direction="row" justifyContent="flex-end">
        <Button variant="contained" color="primary" type="submit">
          Submit
        </Button>
      </Stack>
    </Box>
  );
}
