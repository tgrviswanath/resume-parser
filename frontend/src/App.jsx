import React from "react";
import { Box, Container } from "@mui/material";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import Header from "./components/Header";
import ParseResumePage from "./pages/ParseResumePage";

const theme = createTheme({
  palette: {
    primary: { main: "#1565c0" },
    background: { default: "#f5f5f5" },
  },
});

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ bgcolor: "background.default", minHeight: "100vh" }}>
        <Header />
        <Container maxWidth="md" sx={{ mt: 4, pb: 6 }}>
          <Box sx={{ bgcolor: "white", p: 3, borderRadius: 2, boxShadow: 1 }}>
            <ParseResumePage />
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}
