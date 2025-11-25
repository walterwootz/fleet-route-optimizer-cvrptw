/**
 * User Message
 * Message bubble for user queries
 */

import { User } from 'lucide-react';
import type { Message } from '@/types/fleetOne';

interface UserMessageProps {
  message: Message;
}

export function UserMessage({ message }: UserMessageProps) {
  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex items-start space-x-3 justify-end">
      <div className="bg-blue-600 text-white rounded-lg p-3 max-w-[80%]">
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <span className="text-xs text-blue-200 mt-1 block">
          {formatTime(message.timestamp)}
        </span>
      </div>
      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
        <User size={16} className="text-blue-600" />
      </div>
    </div>
  );
}
