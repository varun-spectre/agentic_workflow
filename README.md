# Work in progress


Vision:

an Agent which does analysis on your portfolio and suggests changes to your portfolio.

- Analyses your interests
- Analyses stock market trends
- Suggests investment opportunities
- Suggests changes to your portfolio
- Gives you updates on your portfolio 

Current tech stack in mind

- LLM: OpenAI 4o
- Database: ChromaDB, SQLite
- Tools: DB access, Web search, Scraping, Twitter API
- MCP: Whatsapp for agent to user communication

Agentic framework:

- Custom Agent framework
1. Agent Config
2. Memory (Context Tracker)
3. System Prompt Builder
4. Execution Backend
5. Step Engine
6. Tool Registry



# TODO: Future improvements

Memory:
- Implement token-limited memory
- Add step filtering (e.g., only last plan+execution)
- Add long-term memory storage options:
  - File persistence
  - Redis integration
  - Vector DB support




