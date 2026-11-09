import "dotenv/config";
import express from "express";
import cors from "cors";
import { generateAnswer } from "./services/gemini_service.js";

const app = express();

app.use(cors());
app.use(express.json());

// Health check
app.get("/api/health", (req, res) => {
  res.json({
    message: "RAG backend is running!",
  });
});

// Test Gemini
app.get("/api/test-gemini", async (req, res) => {
  console.log("1. Received request");

  try {
    console.log("2. Sending request to Gemini...");

    const answer = await generateAnswer(
      "Explain RAG in simple terms in 3 sentences."
    );

    console.log("3. Gemini responded!");

    res.json({ answer });
  } catch (error) {
    console.error("Gemini error:", error);

    res.status(500).json({
      message: "Failed to generate answer",
    });
  }
});

const PORT = 4000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});