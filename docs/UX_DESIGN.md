# UI/UX Design Specification

**Version:** 1.0  
**Date:** 2026-08-08  
**Status:** Design specification for Phase K implementation

---

## Overview

Providence uses a **web-first UI/UX approach** with the dashboard as the primary user interface. The CLI remains a secondary interface for power users and automation.

**Design Philosophy:**
- **Simplicity first** — Clean, intuitive interface; no overwhelming complexity
- **Progressive disclosure** — Show complexity only when needed
- **Streaming-first** — Real-time feedback for long-running research
- **Ultra-smooth performance** — 60fps scrolling, instant interactions
- **Citation-visible** — Evidence always accessible
- **Cost-transparent** — Spend always visible
- **Configurable** — Advanced features available but not overwhelming

---

## 1. Information Architecture

### 1.1 Primary Navigation

```
┌─────────────────────────────────────────────────────────────┐
│  Logo  │  Chat  │  Research  │  Vault  │  History  │  Settings  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Page Hierarchy

| Page | Purpose | Audience |
|------|---------|----------|
| **Chat** | Multi-turn conversations with optional tools | General users |
| **Research** | Deep research with progressive output | Researchers |
| **Vault** | Browse saved sources and notes | Knowledge workers |
| **History** | View past runs and results | All users |
| **Settings** | Configure providers, modes, budgets | Admins/Power users |
| **Ops Dashboard** | Gateway metrics and system health | Operators (existing) |

---

## 2. Chat Interface

### 2.1 Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Chat                                      Mode: Balanced ▼  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ User: What are the latest developments in AI?         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Assistant: [Streaming response...]                   │  │
│  │                                                      │  │
│  │ 📚 Used 3 sources · 💰 $0.02                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ User: Escalate to research mode                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Type a message...                          [Send] [🔍 Tools] │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Features

**Message Display:**
- User messages on right, assistant on left
- Streaming responses with typing indicator
- Tool usage indicators (🔍 search, 📚 vault, etc.)
- Source citations inline with hover preview
- Cost per message displayed

**Input Area:**
- Text input with multi-line support
- Tool toggle button (🔍) to enable/disable tools
- Mode selector (ultra-fast, balanced, accurate, comprehensive)
- Attachment support (PDF, documents)
- Escalate to research button

**Sidebar (Collapsible):**
- Current session metadata
- Cost breakdown
- Source list
- Related vault notes

### 2.3 Interactions

**Real-time Feedback:**
- Streaming responses appear character-by-character
- Tool calls show status (pending → running → complete)
- Source citations expand on hover
- Cost updates in real-time

**Escalation Flow:**
- User clicks "Escalate to research"
- Confirmation modal: "Start deep research on this topic?"
- Research interface opens with pre-filled query
- Chat context preserved

---

## 3. Research Interface

### 3.1 Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Research                    Mode: Comprehensive ▲         │
│  Query: Latest developments in quantum computing            │
│  Autonomy: L1 Report ▲  Budget: $5.00                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Progress ───────────────────────────────────────────┐  │
│  │ ✅ Plan      ⏱️ 2s                                    │  │
│  │ ✅ Gather    ⏱️ 15s                                   │  │
│  │ ✅ Ingest    ⏱️ 8s                                    │  │
│  │ 🔄 Analyze   ⏱️ Running...                            │  │
│  │ ⏳ Retrieve  ⏳ Pending                                │  │
│  │ ⏳ Synthesize ⏳ Pending                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Outline ─────────────────────────────────────────────┐  │
│  │ 1. Introduction                                        │  │
│  │ 2. Recent Breakthroughs                               │  │
│  │ 3. Industry Applications                              │  │
│  │ 4. Future Directions                                  │  │
│  │ 5. Conclusion                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Report ───────────────────────────────────────────────┐  │
│  │ # Recent Breakthroughs in Quantum Computing           │  │
│  │                                                      │  │
│  │ ## 1. Introduction                                    │  │
│  │ [Streamed content...]                                 │  │
│  │                                                      │  │
│  │ According to Smith et al. [1], quantum...            │  │
│  │                                                      │  │
│  │ ## 2. Recent Breakthroughs                           │  │
│  │ [Streaming...]                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Sources ─────────────────────────────────────────────┐  │
│  │ [1] arxiv.org/abs/2024.12345 ⭐ 95%                  │  │
│  │ [2] nature.com/articles/... ⭐ 92%                    │  │
│  │ [3] ieee.org/... ⭐ 88%                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  💰 $0.45 / $5.00  🔄 Iteration 2/5  ⏱️ 2:30 elapsed    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Features

**Progress Tracking:**
- Step-by-step progress with status indicators
- Time per step
- Current iteration count
- Estimated time remaining

**Outline Panel:**
- Generated outline displayed early
- Click to jump to section
- Section completion status
- Word count per section

**Report Panel:**
- Progressive section streaming
- Inline citations with source preview
- LaTeX math rendering
- Export buttons (Markdown, PDF, HTML)

**Sources Panel:**
- All sources with credibility scores
- Click to view source
- Filter by type (academic, news, docs)
- Sort by relevance or credibility

**Status Bar:**
- Real-time cost tracking
- Budget progress bar
- Iteration counter
- Elapsed time
- Pause/Resume/Stop controls

### 3.3 Interactions

**Human-in-the-Loop (L2):**
- Pause after plan with approval modal
- Pause before expensive operations
- Resume on approval
- Modify plan before approval

**Dynamic Task Injection:**
- "Add subtask" button during research
- Inject new questions mid-run
- DAG auto-replans without restart
- Progress updates with new tasks

**Quality Gates:**
- Citation ship-gate warning if sources weak
- Quality score display
- Option to retry with different settings

---

## 4. Vault Browser

### 4.1 Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Vault                                    [+ New Note]       │
├─────────────────────────────────────────────────────────────┤
│  🔍 Search vault...                                          │
│                                                              │
│  ┌─ Filters ─────────────────────────────────────────────┐  │
│  │ Topics: [AI] [Quantum] [Research] [+ Add]            │  │
│  │ Date: [Last 30 days ▼]                                │  │
│  │ Source: [All ▼]                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Notes ────────────────────────────────────────────────┐  │
│  │ ┌──────────────────────────────────────────────────┐  │
│  │ │ 📄 Quantum Computing Advances                    │  │
│  │ │ Sources: 12  •  Updated: 2 days ago              │  │
│  │ │ Topics: AI, Quantum, Research                     │  │
│  │ │ Preview: Recent breakthroughs in quantum...       │  │
│  │ └──────────────────────────────────────────────────┘  │
│  │                                                          │
│  │ ┌──────────────────────────────────────────────────┐  │
│  │ │ 📄 AI Research Methods                           │  │
│  │ │ Sources: 8  •  Updated: 1 week ago               │  │
│  │ │ Topics: AI, Research, Methods                    │  │
│  │ │ Preview: Overview of modern AI research...        │  │
│  │ └──────────────────────────────────────────────────┘  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Features

**Search:**
- Full-text search across notes
- Semantic search with embeddings
- Filter by topics, date, source
- Sort by relevance or date

**Note Cards:**
- Title, source count, update date
- Topic tags
- Text preview
- Quality score indicator

**Note Detail View:**
- Full note content
- Source list with links
- Related notes
- Edit/delete options
- Export options

---

## 5. History

### 5.1 Layout

```
┌─────────────────────────────────────────────────────────────┐
│  History                                      [Filter ▼]     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Runs ─────────────────────────────────────────────────┐  │
│  │ ┌──────────────────────────────────────────────────┐  │  │
│  │ │ 📊 Quantum Computing Research                   │  │  │
│  │ │ Mode: Comprehensive  •  Cost: $0.45             │  │  │
│  │ │ Duration: 2:30  •  Iterations: 5  •  Status: ✅ │  │  │
│  │ │ [View Result] [Download] [Delete]               │  │  │
│  │ └──────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │ ┌──────────────────────────────────────────────────┐  │  │
│  │ │ 💬 Chat: AI Developments                         │  │  │
│  │ │ Mode: Balanced  •  Cost: $0.02                  │  │  │
│  │ │ Duration: 45s  •  Messages: 8  •  Status: ✅   │  │  │
│  │ │ [View Result] [Delete]                           │  │  │
│  │ └──────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Features

**Run List:**
- All chat and research runs
- Filter by type, date, status
- Sort by date, cost, duration
- Search by query

**Run Detail:**
- Full result display
- Cost breakdown
- Performance metrics
- Trace viewer (for research)
- Source list
- Export options

**Trace Viewer:**
- Step-by-step execution trace
- Agent decisions
- Tool calls
- Timing per step
- Error logs

---

## 6. Settings

### 6.1 Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Settings                                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Providers ───────────────────────────────────────────┐  │
│  │                                                          │  │
│  │ [+ Add Provider]                                       │  │
│  │                                                          │  │
│  │ ┌──────────────────────────────────────────────────┐  │  │
│  │ │ OpenCode (Free)                                   │  │  │
│  │ │ URL: https://opencode.ai/zen/v1                  │  │  │
│  │ │ Key: ••••••••  [Edit] [Test] [Remove]            │  │  │
│  │ │ Models: deepseek-v4-flash-free, big-pickle...     │  │  │
│  │ └──────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │ ┌──────────────────────────────────────────────────┐  │  │
│  │ │ OpenAI                                             │  │  │
│  │ │ URL: https://api.openai.com/v1                    │  │  │
│  │ │ Key: •••••••••••••••••••••••  [Edit] [Test] [Remove]│  │  │
│  │ │ Models: gpt-4o, gpt-4o-mini...                    │  │  │
│  │ └──────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Modes ───────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │ Ultra-Fast:  Token budget: 10K, Cost: $0.10          │  │
│  │ Balanced:     Token budget: 50K, Cost: $0.50          │  │
│  │ Accurate:     Token budget: 100K, Cost: $1.00        │  │
│  │ Comprehensive: Token budget: 500K, Cost: $5.00       │  │
│  │                                                          │  │
│  │ [+ Add Custom Mode]                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Autonomy ────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │ Default: ⦿ L1 Report  ○ L2 Human Gate  ○ L3 Unattended│  │
│  │                                                          │  │
│  │ L2 Human Gate:                                         │  │
│  │ ☑ Pause after plan                                     │  │
│  │ ☑ Pause before expensive operations                   │  │
│  │ ☑ Pause before export                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Advanced ────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │ Temporal Server: localhost:7233  [Test Connection]    │  │
│  │ Vector Backend: ⦿ LanceDB  ○ Qdrant  ○ FTS          │  │
│  │ Factoid Model: llama3:8b  [Test]                      │  │
│  │                                                          │  │
│  │ ☑ Enable bias mitigation (Triangulator)               │  │
│  │ ☑ Enable factoid extraction (90% token reduction)     │  │
│  │ ☑ Enable source verification (Retriever Guard)         │  │
│  │ ☑ Enable mathematical rendering                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Features

**Provider Management:**
- Add custom providers
- Edit provider configuration
- Test provider connectivity
- View available models
- Remove providers

**Mode Configuration:**
- View default modes
- Create custom modes
- Set token/cost/time budgets
- Configure quality dials

**Autonomy Settings:**
- Select default autonomy level
- Configure L2 human gate triggers
- Set budget hard limits

**Advanced Settings:**
- Temporal server configuration
- Vector backend selection
- Factoid model configuration
- Feature toggles (bias mitigation, factoid extraction, etc.)

---

## 7. Ops Dashboard (Existing)

The existing `src/dashboard/` provides:

- Gateway metrics (calls, errors, latency, tokens, cost)
- Prometheus endpoint for scraping
- Event stream for monitoring
- Status overview

**Integration Plan:**
- Merge ops metrics into main Settings page
- Add "System Health" tab
- Keep standalone dashboard available for operators

---

## 8. Responsive Design

### 8.1 Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 768px | Single column, stacked panels |
| Tablet | 768px - 1024px | Two columns, collapsible sidebar |
| Desktop | > 1024px | Three columns, full sidebar |

### 8.2 Mobile Adaptations

**Chat:**
- Full-width messages
- Collapsible tool panel
- Bottom input fixed

**Research:**
- Tab-based navigation (Progress, Outline, Report, Sources)
- Swipe between tabs
- Compact progress indicators

**Vault:**
- Single-column note cards
- Filter in drawer
- Search always visible

---

## 9. Design System

### 9.1 Color Palette

| Purpose | Color | Hex |
|---------|-------|-----|
| Primary | Blue | #3B82F6 |
| Secondary | Slate | #64748B |
| Success | Green | #10B981 |
| Warning | Amber | #F59E0B |
| Error | Red | #EF4444 |
| Background | White | #FFFFFF |
| Surface | Gray | #F8FAFC |
| Border | Gray | #E2E8F0 |

### 9.2 Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Headings | Inter | 24px | 600 |
| Body | Inter | 16px | 400 |
| Code | JetBrains Mono | 14px | 400 |
| Captions | Inter | 12px | 400 |

### 9.3 Components

**Buttons:**
- Primary: Blue background, white text
- Secondary: Gray background, dark text
- Ghost: Transparent, colored text
- Icon-only: Square, 32px

**Cards:**
- White background
- Subtle border
- 8px border radius
- 16px padding

**Inputs:**
- Gray background
- Dark border on focus
- 8px border radius
- 32px height

**Progress Bars:**
- Blue fill
- Gray track
- Rounded corners
- Animated during operation

---

## 10. Accessibility

### 10.1 Standards

- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader support
- High contrast mode
- Focus indicators

### 10.2 Features

- ARIA labels for all interactive elements
- Skip to main content link
- Alt text for images
- Semantic HTML
- Focus management in modals
- Error announcements

---

## 10. Export Functionality

### 10.1 Report Export

**Export Options Panel:**
```
┌─────────────────────────────────────────────────────────────┐
│  Export Report                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Format:                                                     │
│  ⦿ Markdown (.md)  ○ PDF (.pdf)  ○ HTML (.html)            │
│                                                              │
│  Options:                                                    │
│  ☑ Include citations                                        │
│  ☑ Include source list                                      │
│  ☑ Include metadata (date, cost, iterations)                │
│  ☑ Render mathematical formulas (LaTeX)                     │
│                                                              │
│  [Cancel]  [Export & Download]                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Markdown Export

**Features:**
- Clean, well-formatted markdown
- Inline citations: `[1]`, `[2]`
- Source list at end with URLs
- LaTeX math preserved: `$E=mc^2$`, `$$\int_0^1 x dx$$`
- Metadata header (YAML frontmatter)
- Table of contents (optional)

**Example Output:**
```markdown
---
title: "Recent Breakthroughs in Quantum Computing"
date: "2026-08-08"
cost: "$0.45"
iterations: 5
sources: 12
---

# Recent Breakthroughs in Quantum Computing

## 1. Introduction

According to Smith et al. [1], quantum computing has seen significant advances...

The key equation for quantum entanglement is:

$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$$

## 2. Recent Breakthroughs

...

## Sources

[1] arxiv.org/abs/2024.12345 - "Quantum Advances"
[2] nature.com/articles/... - "New Qubit Designs"
```

### 10.3 PDF Export

**Features:**
- Professional typesetting
- Proper page breaks
- Mathematical formulas rendered correctly
- Citations as footnotes or inline
- Cover page with metadata
- Table of contents
- High-quality layout

**Technology Options:**
- **Option 1:** Puppeteer + HTML → PDF (recommended)
  - Render HTML with MathJax
  - Print to PDF via Puppeteer
  - Good control over layout
  - Client-side generation

- **Option 2:** LaTeX → PDF
  - Convert MD to LaTeX
  - Compile with pdflatex
  - Best math rendering
  - Server-side generation

- **Option 3:** React-PDF
  - React components for PDF
  - Client-side generation
  - Limited math support

**Recommended:** Puppeteer + HTML for simplicity and client-side generation.

### 10.4 HTML Export

**Features:**
- Single HTML file
- Embedded CSS
- MathJax for math rendering
- Responsive design
- Print-friendly
- Interactive citations (click to jump to source)

### 10.5 Download Experience

**Progress Indicator:**
```
┌─────────────────────────────────────────────────────────────┐
│  Exporting Report...                                        │
│                                                              │
│  ████████████████████████████████░░░░ 75%                  │
│                                                              │
│  Generating PDF...                                          │
│                                                              │
│  [Cancel]                                                   │
└─────────────────────────────────────────────────────────────┘
```

**Success State:**
```
┌─────────────────────────────────────────────────────────────┐
│  ✓ Export Complete                                          │
│                                                              │
│  Your report has been downloaded:                           │
│                                                              │
│  📄 quantum-computing-report.pdf                            │
│                                                              │
│  [Download Again]  [Close]                                  │
└─────────────────────────────────────────────────────────────┘
```

### 10.6 Batch Export

**For Power Users:**
- Export multiple reports at once
- Zip file with all formats
- Export entire history
- Scheduled exports

---

## 11. Ultra-Smooth Performance

### 11.1 Performance Principles

**Target Experience:**
- **60fps scrolling** — No jank, smooth as native
- **Instant interactions** — < 16ms response time
- **Perceived speed** — Optimistic UI updates
- **Smooth streaming** — Character-by-character without lag

### 11.2 Technical Implementation

**Virtual Scrolling:**
- Implement virtual scrolling for long lists (history, vault, sources)
- Only render visible items
- Recycle DOM nodes
- Smooth infinite scroll

**Streaming Optimization:**
- Use Server-Sent Events (SSE) for real-time updates
- Buffer small chunks for smooth rendering
- Use `requestAnimationFrame` for UI updates
- Debounce rapid updates

**Code Splitting:**
- Lazy load routes
- Split components by feature
- Dynamic imports for heavy libraries
- Preload critical routes

**Rendering Optimization:**
- Use React.memo for expensive components
- Implement shouldComponentUpdate logic
- Avoid unnecessary re-renders
- Use CSS transforms for animations (GPU-accelerated)

**Image Optimization:**
- Lazy load images
- Use WebP format
- Implement progressive loading
- Add blur-up placeholders

### 11.3 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Initial load | < 2s | Lighthouse |
| Time to interactive | < 3s | Lighthouse |
| First contentful paint | < 1s | Lighthouse |
| Streaming latency | < 100ms | Network |
| Scroll FPS | 60fps | Chrome DevTools |
| Interaction delay | < 16ms | Chrome DevTools |
| Page transition | < 200ms | Manual |

### 11.4 Smooth Scrolling Implementation

**CSS:**
```css
html {
  scroll-behavior: smooth;
}

/* Smooth scrolling for containers */
.smooth-scroll {
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}

/* Hardware acceleration */
.gpu-accelerated {
  transform: translateZ(0);
  will-change: transform;
}
```

**JavaScript:**
```javascript
// Virtual scrolling for long lists
import { useVirtualizer } from '@tanstack/react-virtual';

const virtualizer = useVirtualizer({
  count: items.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 50,
  overscan: 5,
});
```

**Progressive Loading:**
```javascript
// Load items in chunks
const loadMore = useCallback(async () => {
  const nextChunk = await fetchItems(offset, chunkSize);
  setItems(prev => [...prev, ...nextChunk]);
  setOffset(prev => prev + chunkSize);
}, [offset]);
```

### 11.5 Streaming Best Practices

**Chunk Size:**
- Small chunks (100-500 characters) for smooth display
- Avoid large chunks that cause layout shifts
- Buffer for consistent frame rate

**Update Strategy:**
```javascript
// Use requestAnimationFrame for smooth updates
const updateContent = useCallback((newContent) => {
  requestAnimationFrame(() => {
    setContent(prev => prev + newContent);
  });
}, []);
```

**Backpressure Handling:**
- Implement flow control if client can't keep up
- Pause streaming if buffer full
- Resume when ready

### 11.6 Performance Monitoring

**Metrics to Track:**
- Core Web Vitals (LCP, FID, CLS)
- Custom metrics (streaming latency, scroll FPS)
- Error rates
- User perceived performance

**Tools:**
- Lighthouse CI
- Web Vitals library
- Custom performance logging
- Real User Monitoring (RUM)

---

## 12. Implementation Priority

### Phase K.1 - Core UI (High Priority)
- [ ] Chat interface with streaming
- [ ] Research interface with progressive output
- [ ] Basic navigation
- [ ] Responsive layout
- [ ] Export functionality (MD, PDF, HTML)
- [ ] Ultra-smooth scrolling (60fps)

### Phase K.2 - Features (Medium Priority)
- [ ] Provider management UI
- [ ] Vault browser
- [ ] History view
- [ ] Settings page

### Phase K.3 - Advanced (Low Priority)
- [ ] Trace viewer
- [ ] Advanced filtering
- [ ] Custom modes UI
- [ ] Theme customization

---

## 13. Tech Stack Recommendations

### Frontend Framework
- **Option 1:** Next.js + React (recommended)
  - Server-side rendering
  - Built-in routing
  - API routes
  - Great performance

- **Option 2:** Vue.js + Nuxt
  - Simpler learning curve
  - Great documentation
  - Good performance

- **Option 3:** SvelteKit
  - Lightweight
  - Great performance
  - Smaller bundle size

### UI Library
- **Option 1:** shadcn/ui (recommended)
  - Based on Radix UI
  - Tailwind CSS
  - Highly customizable
  - No runtime overhead

- **Option 2:** Chakra UI
  - Simple API
  - Good accessibility
  - Built-in components

- **Option 3:** Mantine
  - React-based
  - Many components
  - Good documentation

### State Management
- **Option 1:** Zustand (recommended)
  - Simple API
  - No boilerplate
  - TypeScript support

- **Option 2:** Redux Toolkit
  - Mature ecosystem
  - Great dev tools
  - More complex

### Real-time
- **Option 1:** Server-Sent Events (SSE) (recommended)
  - Simple to implement
  - Built-in browser support
  - Good for streaming

- **Option 2:** WebSocket
  - Bidirectional
  - More complex
  - Better for real-time collaboration

---

## 14. API Integration

### 14.1 Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Send chat message |
| `/api/chat/stream` | GET | Stream chat response (SSE) |
| `/api/research` | POST | Start research |
| `/api/research/stream` | GET | Stream research progress (SSE) |
| `/api/research/{id}` | GET | Get research result |
| `/api/providers` | GET | List providers |
| `/api/providers` | POST | Add provider |
| `/api/providers/{id}` | PUT | Update provider |
| `/api/providers/{id}` | DELETE | Remove provider |
| `/api/vault/search` | GET | Search vault |
| `/api/vault/notes` | GET | List notes |
| `/api/vault/notes` | POST | Create note |
| `/api/history` | GET | List history |
| `/api/history/{id}` | GET | Get history item |
| `/api/settings` | GET | Get settings |
| `/api/settings` | PUT | Update settings |

### 14.2 Streaming Format

**Chat Stream:**
```
data: {"type": "content", "content": "Hello"}
data: {"type": "source", "id": "1", "title": "..."}
data: {"type": "cost", "cost": 0.01}
data: {"type": "done"}
```

**Research Stream:**
```
data: {"type": "step", "step": "plan", "status": "running"}
data: {"type": "outline", "sections": [...]}
data: {"type": "section", "id": "1", "content": "..."}
data: {"type": "source", "id": "1", "credibility": 0.95}
data: {"type": "cost", "cost": 0.45}
data: {"type": "done"}
```

---

## 15. Security Considerations

### 15.1 Authentication

- Optional API key authentication
- Session-based auth for web UI
- OAuth integration (future)

### 15.2 Authorization

- Role-based access control
- Admin vs user permissions
- Resource isolation

### 15.3 Data Protection

- HTTPS only
- Input sanitization
- Output encoding
- XSS prevention
- CSRF protection

---

## 16. Analytics & Telemetry

### 16.1 User Analytics

- Page views
- Feature usage
- Session duration
- Error rates

### 16.2 Product Analytics

- Research success rate
- Average research cost
- Mode usage distribution
- Provider usage distribution

### 16.3 Privacy

- Anonymous by default
- Opt-in for detailed analytics
- Data retention policies
- GDPR compliance

---

## 17. Internationalization

### 17.1 Plan

- Phase 1: English only
- Phase 2: Support for major languages (Spanish, Chinese, French)
- Phase 3: Full i18n with RTL support

### 17.2 Implementation

- Use i18n library (next-i18next, vue-i18n)
- Externalize all strings
- Support for date/time localization
- Currency localization

---

## 18. Testing Strategy

### 18.1 Unit Tests

- Component tests
- Hook tests
- Utility tests

### 18.2 Integration Tests

- API integration tests
- Streaming tests
- E2E user flows

### 18.3 E2E Tests

- Playwright or Cypress
- Critical user journeys
- Cross-browser testing

---

## 19. Deployment

### 19.1 Environments

- Development: Local + staging
- Production: Cloud deployment

### 19.2 Hosting Options

- **Option 1:** Vercel (recommended for Next.js)
- **Option 2:** Netlify
- **Option 3:** Self-hosted (Docker)

### 19.3 CI/CD

- Automated testing
- Automated deployment
- Rollback capability

---

## 20. Success Metrics

### 20.1 User Engagement

- Daily active users
- Session duration
- Research completion rate
- Feature adoption

### 20.2 Performance

- Page load time
- Streaming latency
- Error rate
- Uptime

### 20.3 Quality

- User satisfaction (NPS)
- Bug reports
- Feature requests
- Support tickets

---

## Appendix A: Wireframes

[To be created with design tool]

## Appendix B: Component Library

[To be documented during implementation]

## Appendix C: Design Tokens

[To be defined in CSS variables / design system]
