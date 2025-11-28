# GEMINI.md - SmartInsight Global Context

## Project Overview
**SmartInsight Global (智察全球)** is an intelligent global intelligence analysis system.
It collects, analyzes, and interprets global information (News, Military, Finance, Politics) using domestic multi-modal Large Language Models (LLMs).

## Core Objectives
1.  **Global Vision**: Aggregate real-time global information.
2.  **AI Analysis**: Use API-based domestic LLMs (DeepSeek, Qwen, etc.) for deep interpretation, not just translation.
3.  **Data Safety**: Flexible storage (PostgreSQL/MongoDB) with **Dual Backup** (Local HDD + Cloud Object Storage).
4.  **Commercial Viability**: Cost-effective, premium user experience, suitable for personal and future SaaS use.

## Technical Context
-   **Backend**: Python (FastAPI) preferred for AI integration.
-   **Frontend**: Next.js / React with premium UI (TailwindCSS).
-   **AI Integration**: OpenAI-compatible API client pointing to domestic providers.
-   **Infrastructure**: Docker Compose based.

## Key Features to Implement
-   **Crawler Engine**: Safe, compliant scrapers for RSS/Web.
-   **Analysis Engine**: Prompt engineering for "Event Extraction", "Sentiment Analysis", "Trend Prediction".
-   **Dashboard**: Global Risk Map, Timeline, Report Center.
-   **Backup System**: Automated scripts for local snapshots and cloud upload.

## Development Rules
-   **Privacy**: No personal data collection.
-   **Compliance**: Strict adherence to data source terms of service.
-   **Performance**: Async processing for data collection and analysis.
