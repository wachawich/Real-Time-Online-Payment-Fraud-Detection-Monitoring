import Image from "next/image";
import { Geist, Geist_Mono } from "next/font/google";
import React from "react";
import TransactionStreamer from "../components/TransactionStreamer";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1976d2",
    },
    secondary: {
      main: "#dc004e",
    },
  },
});

// pages/index.tsx
export default function HomePage() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <main>
        <TransactionStreamer />
      </main>
    </ThemeProvider>
  );
}