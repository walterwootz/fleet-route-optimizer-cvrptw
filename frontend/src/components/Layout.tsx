/**
 * Layout Component
 * Main layout with sidebar navigation
 */

import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Ship, Wrench, Factory, Users, FileText, DollarSign, ShoppingCart } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Flotte', href: '/fleet', icon: Ship },
    { name: 'Wartung', href: '/maintenance', icon: Wrench },
    { name: 'Werkstatt', href: '/workshop', icon: Factory },
    // Future pages:
    // { name: 'Beschaffung', href: '/procurement', icon: ShoppingCart },
    // { name: 'Finanzen', href: '/finance', icon: DollarSign },
    // { name: 'Personal', href: '/hr', icon: Users },
    // { name: 'Dokumente', href: '/documents', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">RF</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">
                RailFleet
              </h1>
              <p className="text-xs text-gray-500">
                Manager
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2 rounded-lg transition ${
                  isActive
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`
              }
            >
              <item.icon size={20} />
              <span className="font-medium">{item.name}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t">
          <div className="text-xs text-gray-500">
            <p className="font-medium">FLEET-ONE Agent</p>
            <p>Version 1.0.0</p>
            <p className="mt-1">Phase 3 (WP15-WP25)</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="px-6 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                Powered by FLEET-ONE AI
              </span>
            </div>

            {/* User info */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  Demo Dispatcher
                </p>
                <p className="text-xs text-gray-500">Disponent</p>
              </div>
              <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                <span className="text-gray-600 font-medium">DD</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t">
          <div className="px-6 py-3">
            <p className="text-center text-xs text-gray-500">
              RailFleet Manager © 2025 | Entwickelt mit React, TypeScript & Tremor
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}
