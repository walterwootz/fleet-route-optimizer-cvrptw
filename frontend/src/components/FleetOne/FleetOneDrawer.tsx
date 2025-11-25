/**
 * FLEET-ONE Drawer
 * Main chat interface as a slide-in drawer
 */

import { useEffect } from 'react';
import { useFleetOneStore } from '@/stores/fleetOneStore';
import { ChatHeader } from './ChatHeader';
import { ModeIndicator } from './ModeIndicator';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';

interface FleetOneDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function FleetOneDrawer({ isOpen, onClose }: FleetOneDrawerProps) {
  const { initSession, sessionId, userId, userRole } = useFleetOneStore();

  useEffect(() => {
    // Initialize session when drawer opens if no session exists
    if (isOpen && !sessionId && userId && userRole) {
      initSession(userId, userRole);
    }
  }, [isOpen, sessionId, userId, userRole, initSession]);

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="fixed right-0 top-0 h-full w-full md:w-[480px]
                   bg-white shadow-2xl z-50 flex flex-col
                   animate-slide-in-right"
      >
        {/* Header */}
        <ChatHeader onClose={onClose} />

        {/* Mode Indicator */}
        <ModeIndicator />

        {/* Messages */}
        <MessageList />

        {/* Input */}
        <ChatInput />
      </div>
    </>
  );
}
