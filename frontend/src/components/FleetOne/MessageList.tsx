/**
 * Message List
 * Scrollable list of chat messages with auto-scroll
 */

import { useRef, useEffect } from 'react';
import { useFleetOneStore } from '@/stores/fleetOneStore';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { SystemMessage } from './SystemMessage';

export function MessageList() {
  const { messages, loading } = useFleetOneStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
      {messages.length === 0 && !loading && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500 max-w-md">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">🤖</span>
            </div>
            <p className="text-lg font-medium mb-2">
              Willkommen bei FLEET-ONE
            </p>
            <p className="text-sm mb-4">
              Ich bin Ihr KI-Assistent für Flottenmanagement. Stellen Sie mir Fragen zu:
            </p>
            <div className="text-sm text-left space-y-1">
              <p>• 🚂 Flottenstatus und Verfügbarkeit</p>
              <p>• 🔧 Wartungsplanung und HU-Fristen</p>
              <p>• 🏭 Werkstattaufträge und Reparaturen</p>
              <p>• 📦 Teile und Beschaffung</p>
              <p>• 💰 Rechnungen und Finanzen</p>
              <p>• 👥 Personal und Zuweisungen</p>
              <p>• 📄 Dokumente und Zertifizierungen</p>
            </div>
          </div>
        </div>
      )}

      {messages.map((msg, idx) => {
        if (msg.role === 'user') {
          return <UserMessage key={idx} message={msg} />;
        } else if (msg.role === 'assistant') {
          return <AssistantMessage key={idx} message={msg} />;
        } else {
          return <SystemMessage key={idx} message={msg} />;
        }
      })}

      {loading && (
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
          </div>
          <span className="text-sm">Agent denkt nach...</span>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}
