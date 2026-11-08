import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({
  apiKey: process.env.GEMINI_API_KEY,
});

export async function generateAnswer(question: string) {
  const response = await ai.models.generateContent({
    model: "gemini-3.8-flash",
    contents: question,
  });

  return response.text;
}