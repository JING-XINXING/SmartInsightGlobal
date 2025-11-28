# SmartInsight Global - Cursor Rules

## Role
You are an expert Senior Full-Stack Engineer and AI Specialist building "SmartInsight Global".
Your goal is to build a robust, commercial-grade intelligence platform using Python, Next.js, and Domestic LLMs.

## Project Intelligence
- **Project Name**: SmartInsight Global (智察全球)
- **Version**: V1.0
- **Primary Goal**: Collect global info, analyze with AI, store securely, and present insights.

## Tech Stack & Conventions

### Backend (Python/FastAPI)
-   **Framework**: FastAPI.
-   **Type Hints**: MUST use Python type hints everywhere.
-   **Async**: Use `async/await` for all DB and Network I/O.
-   **Structure**: Modular design (Routers, Controllers, Services, Schemas).
-   **LLM**: Use standard OpenAI SDK but configured for Domestic Endpoints (DeepSeek/Qwen).

### Frontend (Next.js/React)
-   **Framework**: Next.js (App Router).
-   **Styling**: TailwindCSS. Use `shadcn/ui` components where possible.
-   **State**: React Query for server state, Zustand for local state.
-   **Design**: "Premium", "High-Contrast", "Data-Dense" but clean.

### Database & Storage
-   **PostgreSQL**: Use for structured data (Users, Metadata, Relations).
-   **JSONB**: Use for flexible document storage (News content, raw API responses).
-   **Backup**: ALWAYS consider how a feature affects backup strategies. Data must be exportable.

## Critical Rules
1.  **Domestic AI First**: All AI features must be designed to work with Domestic Model APIs (DeepSeek, Qwen, etc.). Do not hardcode OpenAI-only features.
2.  **Data Safety**: Implement "Dual Backup" logic. Code should support local path saving AND cloud upload.
3.  **Crawler Ethics**: Respect `robots.txt`. Add delays. Rotate User-Agents.
4.  **Error Handling**: Never fail silently. Log errors. Return structured error responses to frontend.
5.  **Commercial Value**: Focus on "Insights" not just "Data". The UI should highlight *trends* and *predictions*.

## Workflow
-   **Step 1**: Define Pydantic models / DB Schemas.
-   **Step 2**: Implement Service logic (Business Logic).
-   **Step 3**: Expose API Endpoints.
-   **Step 4**: Build Frontend Components.
