/**
 * Assistant Message
 * Message bubble for agent responses
 */

import { Bot } from 'lucide-react';
import type { Message } from '@/types/fleetOne';
import { StructuredDataRenderer } from './StructuredDataRenderer';

interface AssistantMessageProps {
  message: Message;
}

export function AssistantMessage({ message }: AssistantMessageProps) {
  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex items-start space-x-3">
      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
        <Bot size={16} className="text-green-600" />
      </div>
      <div className="bg-white rounded-lg p-3 max-w-[80%] shadow-sm border">
        <p className="text-sm text-gray-800 whitespace-pre-wrap">
          {message.content}
        </p>

        {/* Structured Data (tables, charts, etc.) */}
        {message.data && (
          <div className="mt-3">
            <StructuredDataRenderer data={message.data} />
          </div>
        )}

        {/* Mode Badge */}
        {message.mode && (
          <span className="inline-block mt-2 px-2 py-1 bg-gray-100 text-xs rounded text-gray-600">
            {message.mode}
          </span>
        )}

        <span className="text-xs text-gray-400 mt-1 block">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}
