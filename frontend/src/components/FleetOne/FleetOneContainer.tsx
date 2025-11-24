/**
 * FLEET-ONE Container
 * Root component for FLEET-ONE chat integration
 */

import { useFleetOneStore } from '@/stores/fleetOneStore';
import { FleetOneTrigger } from './FleetOneTrigger';

export function FleetOneContainer() {
  const { isOpen, setIsOpen } = useFleetOneStore();

  return (
    <>
      {/* Floating trigger button */}
      <FleetOneTrigger onClick={() => setIsOpen(true)} />

      {/* Chat drawer - TODO: Implement in next step */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-center justify-center"
          onClick={() => setIsOpen(false)}
        >
          <div
            className="bg-white rounded-lg p-8 max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-2xl font-bold mb-4">FLEET-ONE Agent</h2>
            <p className="text-gray-600 mb-4">
              Chat-Interface wird implementiert...
            </p>
            <button
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Schließen
            </button>
          </div>
        </div>
      )}
    </>
  );
}
