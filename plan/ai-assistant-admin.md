# AI Assistant for Admin Dashboard

## Overview
Create an AI chatbot assistant that can perform admin actions via natural language commands.

## Features
1. **Category Creation**: Create categories from natural language (e.g., "create a category called Technology")
2. **Chat Interface**: Floating chatbot widget on admin dashboard
3. **Action Execution**: AI can execute admin panel actions on user's behalf
4. **Conversation History**: Maintain chat history during session

## Technical Implementation

### Backend
- **Endpoint**: `POST /api/admin/assistant/chat`
- **AI Agent**: ChatAgent with function calling capabilities
- **Tools**: Category creation function
- **Model**: gemini-2.5-flash (fast responses)

### Frontend
- **Component**: AdminAssistant.js
- **UI**: Floating chat widget with toggle button
- **Integration**: Connects to category management system
- **State**: Session-based conversation history

## User Flow
1. Admin opens chatbot from dashboard
2. Types natural language command (e.g., "create a tech category")
3. AI processes command and creates category
4. Confirmation message shown in chat
5. Category appears in admin panel immediately
