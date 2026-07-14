/**
 * HTTP client for communicating with the Python FastAPI backend.
 */
import axios from "axios";
import { config } from "../config";

export const backendClient = axios.create({
  baseURL: config.backendUrl,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});
