'use client';

import { Zap, Settings, BarChart3 } from 'lucide-react';
import ModeSwitch from './ModeSwitch';

interface HeaderProps {
  mode: 'semi' | 'auto';
  onModeChange: (mode: 'semi' | 'auto') => void;
}

export default function Header({ mode, onModeChange }: HeaderProps) {
  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* 로고 */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">QuickInfo</h1>
              <p className="text-xs text-muted-foreground">Dashboard</p>
            </div>
          </div>

          {/* 모드 스위치 */}
          <ModeSwitch mode={mode} onChange={onModeChange} />

          {/* 우측 메뉴 */}
          <div className="flex items-center gap-4">
            <button className="p-2 rounded-lg hover:bg-secondary transition-colors">
              <BarChart3 className="w-5 h-5 text-muted-foreground" />
            </button>
            <button className="p-2 rounded-lg hover:bg-secondary transition-colors">
              <Settings className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
