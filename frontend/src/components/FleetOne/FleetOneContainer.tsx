/**
 * FLEET-ONE Container
 * Root component for FLEET-ONE chat integration
 */

import { useFleetOneStore } from '@/stores/fleetOneStore';
import { FleetOneTrigger } from './FleetOneTrigger';
import { FleetOneDrawer } from './FleetOneDrawer';

export function FleetOneContainer() {
  const { isOpen, setIsOpen } = useFleetOneStore();

  return (
    <>
      {/* Floating trigger button */}
      <FleetOneTrigger onClick={() => setIsOpen(true)} />

      {/* Chat drawer */}
      <FleetOneDrawer
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </>
  );
}
