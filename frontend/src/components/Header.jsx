import React from "react";
import { AppBar, Toolbar, Typography } from "@mui/material";
import DescriptionIcon from "@mui/icons-material/Description";

export default function Header() {
  return (
    <AppBar position="static">
      <Toolbar>
        <DescriptionIcon sx={{ mr: 1 }} />
        <Typography variant="h6" fontWeight="bold">
          Resume Parser
        </Typography>
        <Typography variant="body2" sx={{ ml: 2, opacity: 0.8 }}>
          Extract structured data from PDF / DOCX resumes
        </Typography>
      </Toolbar>
    </AppBar>
  );
}
