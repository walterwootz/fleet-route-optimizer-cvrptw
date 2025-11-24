/**
 * Mode Indicator
 * Visual indicator showing the current agent mode
 */

import { Ship, Wrench, Factory, ShoppingCart, DollarSign, Users, FileText } from 'lucide-react';
import { useFleetOneStore } from '@/stores/fleetOneStore';
import type { AgentMode } from '@/types/fleetOne';

interface ModeConfig {
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  colorClass: string;
  bgClass: string;
  borderClass: string;
}

const MODE_CONFIG: Record<AgentMode, ModeConfig> = {
  FLOTTE: {
    label: 'Flotte',
    icon: Ship,
    colorClass: 'text-blue-600',
    bgClass: 'bg-blue-50',
    borderClass: 'border-blue-200',
  },
  MAINTENANCE: {
    label: 'Wartung',
    icon: Wrench,
    colorClass: 'text-orange-600',
    bgClass: 'bg-orange-50',
    borderClass: 'border-orange-200',
  },
  WORKSHOP: {
    label: 'Werkstatt',
    icon: Factory,
    colorClass: 'text-purple-600',
    bgClass: 'bg-purple-50',
    borderClass: 'border-purple-200',
  },
  PROCUREMENT: {
    label: 'Beschaffung',
    icon: ShoppingCart,
    colorClass: 'text-green-600',
    bgClass: 'bg-green-50',
    borderClass: 'border-green-200',
  },
  FINANCE: {
    label: 'Finanzen',
    icon: DollarSign,
    colorClass: 'text-yellow-600',
    bgClass: 'bg-yellow-50',
    borderClass: 'border-yellow-200',
  },
  HR: {
    label: 'Personal',
    icon: Users,
    colorClass: 'text-pink-600',
    bgClass: 'bg-pink-50',
    borderClass: 'border-pink-200',
  },
  DOCS: {
    label: 'Dokumente',
    icon: FileText,
    colorClass: 'text-gray-600',
    bgClass: 'bg-gray-50',
    borderClass: 'border-gray-200',
  },
};

export function ModeIndicator() {
  const { currentMode, modeConfidence } = useFleetOneStore();

  if (!currentMode) return null;

  const config = MODE_CONFIG[currentMode];
  if (!config) return null;

  const Icon = config.icon;

  return (
    <div className={`px-4 py-2 ${config.bgClass} border-b ${config.borderClass}`}>
      <div className="flex items-center space-x-2">
        <Icon size={16} className={config.colorClass} />
        <span className="text-sm font-medium text-gray-700">
          Modus: {config.label}
        </span>
        {modeConfidence !== null && modeConfidence !== undefined && (
          <span className="text-xs text-gray-500">
            ({Math.round(modeConfidence * 100)}% sicher)
          </span>
        )}
      </div>
    </div>
  );
}
