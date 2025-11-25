/**
 * Chat Input
 * Input field with send button and optional mode picker
 */

import { useState, useRef, KeyboardEvent } from 'react';
import { Send, ChevronDown } from 'lucide-react';
import { useFleetOneStore } from '@/stores/fleetOneStore';
import type { AgentMode } from '@/types/fleetOne';

export function ChatInput() {
  const [input, setInput] = useState('');
  const [showModePicker, setShowModePicker] = useState(false);
  const [forceMode, setForceMode] = useState<AgentMode | undefined>();
  const { sendQuery, loading } = useFleetOneStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    sendQuery(input, forceMode);
    setInput('');
    setForceMode(undefined);
    setShowModePicker(false);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);

    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px';
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t bg-white">
      {/* Mode Picker (optional) */}
      {showModePicker && (
        <div className="mb-2 flex items-center space-x-2">
          <span className="text-xs text-gray-600">Modus erzwingen:</span>
          <select
            value={forceMode || ''}
            onChange={(e) => setForceMode((e.target.value || undefined) as AgentMode)}
            className="text-xs border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-600"
          >
            <option value="">Automatisch</option>
            <option value="FLOTTE">FLOTTE</option>
            <option value="MAINTENANCE">MAINTENANCE</option>
            <option value="WORKSHOP">WORKSHOP</option>
            <option value="PROCUREMENT">PROCUREMENT</option>
            <option value="FINANCE">FINANCE</option>
            <option value="HR">HR</option>
            <option value="DOCS">DOCS</option>
          </select>
          {forceMode && (
            <button
              type="button"
              onClick={() => setForceMode(undefined)}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              Zurücksetzen
            </button>
          )}
        </div>
      )}

      <div className="flex items-end space-x-2">
        <button
          type="button"
          onClick={() => setShowModePicker(!showModePicker)}
          className={`p-2 rounded transition ${
            showModePicker
              ? 'text-blue-600 bg-blue-50'
              : 'text-gray-400 hover:text-gray-600'
          }`}
          title="Modus auswählen"
        >
          <ChevronDown size={20} />
        </button>

        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Stellen Sie eine Frage... (z.B. 'Zeige alle Loks mit Status maintenance_due')"
          className="flex-1 resize-none border rounded-lg px-3 py-2
                     focus:outline-none focus:ring-2 focus:ring-blue-600
                     text-sm max-h-32"
          rows={1}
          disabled={loading}
        />

        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="p-2 bg-blue-600 text-white rounded-lg
                     hover:bg-blue-700 disabled:opacity-50
                     disabled:cursor-not-allowed transition flex items-center justify-center"
          aria-label="Nachricht senden"
        >
          <Send size={20} />
        </button>
      </div>

      <p className="text-xs text-gray-400 mt-2">
        Drücken Sie <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs">Enter</kbd> zum Senden,{' '}
        <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs">Shift+Enter</kbd> für neue Zeile
      </p>
    </form>
  );
}
