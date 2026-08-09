# Frontend - Autonomous Research Agent

Modern web interface for the Autonomous Research Agent, built with Next.js, React, and Tailwind CSS.

## Features

- **Chat Interface**: ChatGPT-like conversational interface
- **Research Interface**: Deep research with cited reports
- **History Page**: View past research and chat history
- **Settings Page**: Configure research modes, autonomy levels, and provider preferences
- **Dark Mode**: Automatic dark mode support
- **Markdown Rendering**: Rich text with LaTeX math support
- **Responsive Design**: Works on desktop and mobile

## Tech Stack

- **Next.js 14**: React framework with App Router
- **React 18**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first CSS
- **Lucide React**: Icon library
- **React Markdown**: Markdown rendering with math support

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API server running on port 8000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── globals.css          # Global styles
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Main chat/research interface
│   ├── history/
│   │   └── page.tsx         # History page
│   └── settings/
│       └── page.tsx         # Settings page
├── components/              # Reusable components (to be added)
├── public/                  # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── next.config.js
└── postcss.config.js
```

## API Integration

The frontend connects to the backend API:

- `POST /api/chat` - Chat endpoint
- `POST /api/research` - Research endpoint
- `GET /api/history` - History endpoint
- `GET /api/providers` - Providers endpoint

API requests are proxied through Next.js rewrites to avoid CORS issues.

## Future Enhancements

- [ ] Streaming responses
- [ ] Real-time research progress
- [ ] Export to PDF/DOCX
- [ ] Vault browser
- [ ] Provider management UI
- [ ] Workspace management
- [ ] Multi-user support
- [ ] Mobile app (React Native)
