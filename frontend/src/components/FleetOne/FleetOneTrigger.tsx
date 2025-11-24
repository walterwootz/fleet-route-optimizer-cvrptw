/**
 * FLEET-ONE Trigger Button
 * Floating button to open the chat interface
 */

import { MessageSquare } from 'lucide-react';

interface FleetOneTriggerProps {
  onClick: () => void;
}

export function FleetOneTrigger({ onClick }: FleetOneTriggerProps) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700
                 text-white rounded-full p-4 shadow-lg transition-all
                 hover:scale-110 z-50 flex items-center justify-center"
      aria-label="FLEET-ONE Agent öffnen"
    >
      <MessageSquare size={24} />
      {/* Online indicator */}
      <span
        className="absolute -top-1 -right-1 bg-green-500 w-3 h-3
                   rounded-full border-2 border-white"
      />
    </button>
  );
}
