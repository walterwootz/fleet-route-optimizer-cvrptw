/**
 * Structured Data Renderer
 * Renders structured data (tables, lists, etc.) from agent responses
 */

interface StructuredDataRendererProps {
  data: any;
}

export function StructuredDataRenderer({ data }: StructuredDataRendererProps) {
  // Check if data contains locomotives array
  if (data.locomotives && Array.isArray(data.locomotives)) {
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full text-xs border border-gray-200 rounded">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-2 py-1 border text-left font-medium">ID</th>
              <th className="px-2 py-1 border text-left font-medium">Status</th>
              {data.locomotives[0]?.due_date && (
                <th className="px-2 py-1 border text-left font-medium">Fällig</th>
              )}
              {data.locomotives[0]?.location && (
                <th className="px-2 py-1 border text-left font-medium">Standort</th>
              )}
            </tr>
          </thead>
          <tbody>
            {data.locomotives.map((loco: any, idx: number) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-2 py-1 border">
                  <span className="font-mono">{loco.id}</span>
                </td>
                <td className="px-2 py-1 border">
                  <StatusBadge status={loco.status} />
                </td>
                {loco.due_date && (
                  <td className="px-2 py-1 border">{loco.due_date}</td>
                )}
                {loco.location && (
                  <td className="px-2 py-1 border">{loco.location}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Check if data contains tasks array
  if (data.tasks && Array.isArray(data.tasks)) {
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full text-xs border border-gray-200 rounded">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-2 py-1 border text-left font-medium">Lok</th>
              <th className="px-2 py-1 border text-left font-medium">Typ</th>
              <th className="px-2 py-1 border text-left font-medium">Fällig</th>
            </tr>
          </thead>
          <tbody>
            {data.tasks.map((task: any, idx: number) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-2 py-1 border">
                  <span className="font-mono">{task.locomotive_id}</span>
                </td>
                <td className="px-2 py-1 border">{task.type}</td>
                <td className="px-2 py-1 border">{task.due_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Check if data contains workshop_orders array
  if (data.workshop_orders && Array.isArray(data.workshop_orders)) {
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full text-xs border border-gray-200 rounded">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-2 py-1 border text-left font-medium">Auftrag</th>
              <th className="px-2 py-1 border text-left font-medium">Lok</th>
              <th className="px-2 py-1 border text-left font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.workshop_orders.map((order: any, idx: number) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-2 py-1 border">
                  <span className="font-mono">{order.id}</span>
                </td>
                <td className="px-2 py-1 border">
                  <span className="font-mono">{order.locomotive_id}</span>
                </td>
                <td className="px-2 py-1 border">
                  <StatusBadge status={order.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Check for stock data
  if (data.stock) {
    const stock = data.stock;
    return (
      <div className="bg-gray-50 rounded p-3 text-xs space-y-2">
        <div className="flex justify-between">
          <span className="text-gray-600">Teil:</span>
          <span className="font-mono font-medium">{stock.part_no}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Verfügbar:</span>
          <span className="font-medium">{stock.available} Stück</span>
        </div>
        {stock.reserved !== undefined && (
          <div className="flex justify-between">
            <span className="text-gray-600">Reserviert:</span>
            <span className="font-medium">{stock.reserved} Stück</span>
          </div>
        )}
        {stock.free !== undefined && (
          <div className="flex justify-between">
            <span className="text-gray-600">Frei:</span>
            <span className="font-medium text-green-600">{stock.free} Stück</span>
          </div>
        )}
      </div>
    );
  }

  // Check for availability metrics
  if (data.availability !== undefined) {
    return (
      <div className="bg-blue-50 rounded p-3 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-gray-700">Verfügbarkeit:</span>
          <span className="text-2xl font-bold text-blue-600">
            {(data.availability * 100).toFixed(1)}%
          </span>
        </div>
        {data.total_fleet && (
          <p className="text-xs text-gray-600 mt-2">
            Flottengröße: {data.total_fleet} Lokomotiven
          </p>
        )}
      </div>
    );
  }

  // Generic JSON display for other data
  return (
    <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto border">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

// Helper component for status badges
function StatusBadge({ status }: { status: string }) {
  const statusStyles: Record<string, string> = {
    operational: 'bg-green-100 text-green-700',
    maintenance_due: 'bg-red-100 text-red-700',
    in_workshop: 'bg-purple-100 text-purple-700',
    planned_for_workshop: 'bg-yellow-100 text-yellow-700',
    planned: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-orange-100 text-orange-700',
    completed: 'bg-green-100 text-green-700',
  };

  const style = statusStyles[status] || 'bg-gray-100 text-gray-700';

  return (
    <span className={`px-1 py-0.5 rounded text-xs ${style}`}>
      {status}
    </span>
  );
}
