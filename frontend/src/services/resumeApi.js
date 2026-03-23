import axios from "axios";

const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
});

export const parseResume = (file) => {
  const form = new FormData();
  form.append("file", file);
  return API.post("/api/v1/parse", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
