import React, { useState, useCallback } from "react";
import {
  Box, Button, Typography, CircularProgress, Alert,
  Paper, Chip, Divider, Grid, Link,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import EmailIcon from "@mui/icons-material/Email";
import PhoneIcon from "@mui/icons-material/Phone";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import GitHubIcon from "@mui/icons-material/GitHub";
import { parseResume } from "../services/resumeApi";
import SkillsChart from "../components/SkillsChart";

export default function ParseResumePage() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  const handleFile = (f) => {
    setFile(f);
    setResult(null);
    setError("");
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  const onDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = () => setDragging(false);

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const res = await parseResume(file);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to parse resume.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {/* Drop Zone */}
      <Paper
        variant="outlined"
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        sx={{
          p: 4, textAlign: "center", cursor: "pointer",
          borderStyle: "dashed", borderWidth: 2,
          borderColor: dragging ? "primary.main" : "grey.400",
          bgcolor: dragging ? "primary.50" : "grey.50",
          mb: 2,
        }}
        onClick={() => document.getElementById("file-input").click()}
      >
        <UploadFileIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
        <Typography variant="h6">
          {file ? file.name : "Drop your resume here or click to upload"}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Supports PDF, DOCX, TXT
        </Typography>
        <input
          id="file-input"
          type="file"
          accept=".pdf,.docx,.txt"
          hidden
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </Paper>

      <Button
        variant="contained"
        fullWidth
        size="large"
        disabled={!file || loading}
        onClick={handleSubmit}
        startIcon={loading ? <CircularProgress size={18} color="inherit" /> : null}
      >
        {loading ? "Parsing..." : "Parse Resume"}
      </Button>

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

      {/* Results */}
      {result && (
        <Box sx={{ mt: 3 }}>
          <Divider sx={{ mb: 2 }} />

          {/* Contact Info */}
          <Typography variant="h5" fontWeight="bold" gutterBottom>
            {result.name || "Name not detected"}
          </Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, mb: 2 }}>
            {result.email && (
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                <EmailIcon fontSize="small" color="action" />
                <Typography variant="body2">{result.email}</Typography>
              </Box>
            )}
            {result.phone && (
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                <PhoneIcon fontSize="small" color="action" />
                <Typography variant="body2">{result.phone}</Typography>
              </Box>
            )}
            {result.linkedin && (
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                <LinkedInIcon fontSize="small" color="primary" />
                <Link href={`https://${result.linkedin}`} target="_blank" variant="body2">
                  {result.linkedin}
                </Link>
              </Box>
            )}
            {result.github && (
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                <GitHubIcon fontSize="small" />
                <Link href={`https://${result.github}`} target="_blank" variant="body2">
                  {result.github}
                </Link>
              </Box>
            )}
          </Box>

          <Grid container spacing={3}>
            {/* Skills */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Skills ({result.skills?.length || 0})
              </Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}>
                {result.skills?.map((s) => (
                  <Chip key={s} label={s} size="small" color="primary" variant="outlined" />
                ))}
              </Box>
              <SkillsChart skills={result.skills} />
            </Grid>

            {/* Education & Experience */}
            <Grid item xs={12} md={6}>
              {result.education?.length > 0 && (
                <>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Education
                  </Typography>
                  {result.education.map((e, i) => (
                    <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>• {e}</Typography>
                  ))}
                  <Divider sx={{ my: 2 }} />
                </>
              )}
              {result.experience?.length > 0 && (
                <>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    Experience Timeline
                  </Typography>
                  {result.experience.map((e, i) => (
                    <Chip
                      key={i}
                      label={`${e.start} → ${e.end}`}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                      variant="outlined"
                    />
                  ))}
                </>
              )}
              <Divider sx={{ my: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Word count: {result.word_count}
              </Typography>
            </Grid>
          </Grid>
        </Box>
      )}
    </Box>
  );
}
