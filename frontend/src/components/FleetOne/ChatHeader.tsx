/**
 * Chat Header
 * Header for FLEET-ONE drawer with title and controls
 */

import { X, Info } from 'lucide-react';
import { useFleetOneStore } from '@/stores/fleetOneStore';

interface ChatHeaderProps {
  onClose: () => void;
}

export function ChatHeader({ onClose }: ChatHeaderProps) {
  const { sessionId, userRole } = useFleetOneStore();

  const roleLabels: Record<string, string> = {
    dispatcher: 'Disponent',
    workshop: 'Werkstatt',
    procurement: 'Beschaffung',
    finance: 'Finanzen',
    ecm: 'ECM',
    viewer: 'Betrachter',
  };

  return (
    <div className="flex items-center justify-between p-4 border-b bg-blue-600 text-white">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
          <span className="text-blue-600 font-bold text-lg">F1</span>
        </div>
        <div>
          <h2 className="font-semibold text-lg">FLEET-ONE</h2>
          <p className="text-xs text-blue-100">
            {userRole ? roleLabels[userRole] || userRole : 'Agent'}
            {sessionId && (
              <span className="ml-2 opacity-75">• Session aktiv</span>
            )}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <button
          className="p-2 hover:bg-blue-700 rounded transition"
          title="Informationen"
          onClick={() => {
            window.open('/docs/FLEET_ONE_BENUTZERHANDBUCH.md', '_blank');
          }}
        >
          <Info size={20} />
        </button>
        <button
          onClick={onClose}
          className="p-2 hover:bg-blue-700 rounded transition"
          aria-label="Schließen"
        >
          <X size={20} />
        </button>
      </div>
    </div>
  );
}
