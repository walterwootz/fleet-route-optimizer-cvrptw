/**
 * System Message
 * Message bubble for system notifications and errors
 */

import { AlertCircle } from 'lucide-react';
import type { Message } from '@/types/fleetOne';

interface SystemMessageProps {
  message: Message;
}

export function SystemMessage({ message }: SystemMessageProps) {
  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex items-start space-x-3">
      <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
        <AlertCircle size={16} className="text-orange-600" />
      </div>
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 max-w-[80%]">
        <p className="text-sm text-orange-900 whitespace-pre-wrap">
          {message.content}
        </p>
        <span className="text-xs text-orange-600 mt-1 block">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}
