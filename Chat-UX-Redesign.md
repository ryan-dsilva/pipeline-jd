# Chat UX Redesign: Modal-Based Interface

## Overview
Transform the fixed chat bar into a sophisticated modal-based interface centered on the main content. The modal will expand on focus to reveal model settings and suggested questions, and minimize on blur while maintaining accessibility to suggested questions during active conversations.

## Design Direction

**Aesthetic Concept:** Refined Editorial Minimalism

This design prioritizes clarity and intentionality. The interface feels like a well-designed editorial tool - precise typography, considered spacing, subtle but purposeful interactions. The warm earth-tone palette (brand orange #C2552D, cream #F7F4F1) is balanced with clean geometric forms and restrained motion.

**Key Design Principles:**
- **Floating Modal:** Bottom-anchored modal centered on main content (not edge-to-edge)
- **Two States:** Minimized (input bar) and expanded (with settings & suggestions)
- **State Transitions:** Smooth, considered animations using CSS transforms and opacity
- **Typographic Hierarchy:** Clear distinction between UI chrome and content
- **Spatial Breathing:** Generous padding, clean borders, purposeful negative space

## Critical Files to Modify

1. **frontend/src/components/ChatBar.tsx** (169 lines)
   - Complete restructure from fixed bar to floating modal
   - Add focus/blur state management
   - Implement model settings UI (reasoning, verbosity)
   - Add suggested questions component
   - Remove headings from response rendering

2. **frontend/src/pages/RoleDetailPage.tsx** (line 248)
   - Update ChatBar positioning to support centered modal layout

3. **frontend/src/lib/types.ts** (lines 92-95)
   - Add ChatSettings interface for reasoning/verbosity
   - Keep existing ChatMessage interface

4. **backend/app/routers/chat.py** (lines 70-76)
   - Add support for reasoning/verbosity parameters
   - Update API to accept model settings

5. **backend/app/models.py**
   - Add ChatRequest fields for reasoning and verbosity settings

## Implementation Plan

### Phase 1: Frontend Type Definitions

**File:** `frontend/src/lib/types.ts`

Add new interfaces:
```typescript
export interface ChatSettings {
  reasoning: 'low' | 'medium' | 'high';
  verbosity: 'brief' | 'balanced' | 'detailed';
}

// ChatMessage already exists - no changes needed
```

### Phase 2: Backend API Updates

**File:** `backend/app/models.py`

Update `ChatRequest` to include settings:
```python
class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    reasoning: str = "low"  # low, medium, high
    verbosity: str = "brief"  # brief, balanced, detailed
```

**File:** `backend/app/routers/chat.py`

Update chat endpoint (lines 70-76):
- Read `body.reasoning` and `body.verbosity`
- Map reasoning to extended_thinking parameter:
  - "low" → no extended_thinking
  - "medium" → extended_thinking with budget of 2000 tokens
  - "high" → extended_thinking with budget of 5000 tokens
- Map verbosity to system prompt guidance:
  - "brief" → "Keep responses concise and to the point."
  - "balanced" → "Provide clear, well-structured responses."
  - "detailed" → "Provide comprehensive, detailed responses with examples."
- Keep streaming response intact

### Phase 3: Suggested Questions Component

**New File:** `frontend/src/components/SuggestedQuestions.tsx`

Create component that displays 4 hardcoded suggested questions as clickable pills:
- Questions hardcoded in frontend (can be made dynamic later if needed)
- Questions relevant to general job analysis context
- Warm, inviting design with hover states
- Clicking a question populates the input and sends

Hardcoded questions:
- "What are three questions I should ask the interviewer?"
- "What are the biggest challenges in this role?"
- "How does this role compare to similar positions?"
- "What skills should I emphasize in my cover letter?"

### Phase 4: ChatBar Modal Redesign

**File:** `frontend/src/components/ChatBar.tsx`

Complete restructure with these key changes:

**A. State Management**
```typescript
const [messages, setMessages] = useState<ChatMessage[]>([]);
const [input, setInput] = useState("");
const [streaming, setStreaming] = useState(false);
const [expanded, setExpanded] = useState(false);
const [settings, setSettings] = useState<ChatSettings>({
  reasoning: 'low',
  verbosity: 'brief'
});
```

**B. Layout Structure**
```
{expanded && <div className="backdrop" />} (full-screen backdrop with blur)

<div> (floating modal container - positioned absolute/fixed)
  {expanded && (
    <div> (expanded panel - settings and suggestions)
      <ModelSettings />
      <SuggestedQuestions onSelect={handleQuestionSelect} />
    </div>
  )}

  {messages.length > 0 && (
    <div> (conversation history - always visible when messages exist)
      <ChatMessageBubble /> (for each message)
    </div>
  )}

  <div> (input bar - always visible)
    <Input onFocus={handleFocus} onBlur={handleBlur} />
    <Button>Send</Button>
  </div>
</div>
```

**C. Positioning & Styling**
- Container: absolute positioning, bottom offset, centered horizontally
- Modal width: 85% of main content area (slightly narrower than content)
- Backdrop: semi-transparent overlay with blur effect when expanded (`backdrop-blur-sm bg-black/10`)
- Shadow for depth: `shadow-2xl`
- Border radius: `rounded-xl`
- Background: white
- Smooth transitions: `transition-all duration-300 ease-in-out`

**D. Focus/Blur Behavior**
```typescript
const handleFocus = () => setExpanded(true);
const handleBlur = (e: FocusEvent) => {
  // Only blur if clicking outside the entire modal
  if (!modalRef.current?.contains(e.relatedTarget as Node)) {
    setExpanded(false);
  }
};
```

**E. Model Settings UI**

Create inline component:
```typescript
function ModelSettings({ settings, onChange }) {
  return (
    <div className="flex gap-6 items-center justify-center border-b pb-4">
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-text-secondary">
          Reasoning
        </label>
        <select
          value={settings.reasoning}
          onChange={(e) => onChange({ ...settings, reasoning: e.target.value })}
          className="..."
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-text-secondary">
          Verbosity
        </label>
        <select
          value={settings.verbosity}
          onChange={(e) => onChange({ ...settings, verbosity: e.target.value })}
          className="..."
        >
          <option value="brief">Brief</option>
          <option value="balanced">Balanced</option>
          <option value="detailed">Detailed</option>
        </select>
      </div>
    </div>
  );
}
```

**F. Remove Headings from Responses**

Update `ChatMessageBubble` component:
```typescript
// Configure marked to customize heading rendering
marked.use({
  renderer: {
    heading(text) {
      // Render headings as bold paragraphs instead
      return `<p class="font-semibold mt-3 mb-1">${text}</p>`;
    }
  }
});
```

**G. Update Send Handler**

Include settings in API call:
```typescript
const handleSend = async () => {
  // ... existing code ...

  controllerRef.current = await sendChatMessage(
    jobId,
    text,
    history,
    settings, // NEW: pass settings
    onChunk,
    onComplete,
    onError
  );
};
```

### Phase 5: Update API Client

**File:** `frontend/src/lib/api.ts`

Update `sendChatMessage` function (lines 148-197):
```typescript
export async function sendChatMessage(
  jobId: string,
  message: string,
  history: ChatMessage[],
  settings: ChatSettings, // NEW parameter
  onChunk: (chunk: string) => void,
  onComplete: () => void,
  onError: () => void
): Promise<AbortController> {
  // ... existing setup ...

  const response = await fetch(`${API_BASE}/chat/${jobId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      history,
      reasoning: settings.reasoning,    // NEW
      verbosity: settings.verbosity,    // NEW
    }),
    signal: controller.signal,
  });

  // ... rest of streaming logic unchanged ...
}
```

### Phase 6: Update Page Layout

**File:** `frontend/src/pages/RoleDetailPage.tsx`

Update ChatBar container (around line 248):
```typescript
{/* Chat Modal - positioned relative to content */}
<div className="relative">
  <ChatBar jobId={id!} />
</div>
```

The parent container should have relative positioning to anchor the modal properly.

## Verification Steps

After implementation:

1. **Visual Verification:**
   - [ ] Modal appears centered on main content (not edge-to-edge)
   - [ ] Modal has proper shadow and border radius
   - [ ] Focus expands modal smoothly
   - [ ] Blur (clicking outside) minimizes modal smoothly
   - [ ] Settings visible when expanded
   - [ ] Suggested questions visible when expanded
   - [ ] Suggested questions remain visible during active chat

2. **Functional Verification:**
   - [ ] Clicking suggested question populates input and sends
   - [ ] Model settings (reasoning/verbosity) are saved in state
   - [ ] Settings are sent to backend with each message
   - [ ] Chat streaming still works correctly
   - [ ] Chat history displays properly
   - [ ] No headings appear in chat responses
   - [ ] Focus/blur behavior works correctly (doesn't collapse when clicking settings)

3. **Backend Verification:**
   - [ ] Backend receives reasoning and verbosity parameters
   - [ ] Extended thinking parameter is set based on reasoning level
   - [ ] System prompt includes verbosity guidance
   - [ ] Streaming response is unchanged

4. **Interaction Testing:**
   - [ ] Type in input → modal stays expanded
   - [ ] Click model settings → modal stays expanded
   - [ ] Click suggested question → sends message
   - [ ] Click outside modal → modal minimizes
   - [ ] During active chat, can still see and click suggested questions
   - [ ] Pressing Enter sends message

## Design Notes

**Typography:**
- Settings labels: `text-sm font-medium text-text-secondary`
- Suggested questions: `text-sm text-text-body`
- Keep existing message bubble typography

**Colors:**
- Modal background: `bg-white`
- Settings area: `border-border-light`
- Suggested question pills: `bg-bg-off-white` hover `bg-bg-cream`
- Focus states: use `ring-brand-primary`

**Motion:**
- Expansion/collapse: `transition-all duration-300 ease-in-out`
- Transform: `scale-y-0 origin-bottom` to `scale-y-100`
- Opacity: `opacity-0` to `opacity-100`
- Suggested question hover: subtle scale `hover:scale-105 transition-transform`

**Spacing:**
- Modal padding: `p-4`
- Settings padding: `pb-4`
- Between sections: `space-y-4`
- Modal bottom offset: `bottom-6`
- Modal width: 85% of parent container width
- Modal horizontal centering: `left-1/2 -translate-x-1/2`

## Technical Considerations

1. **Focus Management:** Use `useRef` for modal container to properly detect outside clicks
2. **Suggested Questions During Chat:** Always render suggested questions in expanded state, even when messages exist
3. **Markdown Configuration:** Use marked.use() to customize renderer globally for the component
4. **Z-index:** Ensure modal appears above page content but below any global modals
5. **Responsive:** Consider mobile behavior - may need to be full-width on small screens
