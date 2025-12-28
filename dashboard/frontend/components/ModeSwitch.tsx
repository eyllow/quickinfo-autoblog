'use client';

import { Hand, Bot } from 'lucide-react';

interface ModeSwitchProps {
  mode: 'semi' | 'auto';
  onChange: (mode: 'semi' | 'auto') => void;
}

export default function ModeSwitch({ mode, onChange }: ModeSwitchProps) {
  return (
    <div className="flex items-center gap-2 bg-secondary rounded-lg p-1">
      <button
        onClick={() => onChange('semi')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all ${
          mode === 'semi'
            ? 'bg-primary text-white'
            : 'text-muted-foreground hover:text-white'
        }`}
      >
        <Hand className="w-4 h-4" />
        <span className="text-sm font-medium">반자동</span>
      </button>
      <button
        onClick={() => onChange('auto')}
        className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all ${
          mode === 'auto'
            ? 'bg-accent text-white'
            : 'text-muted-foreground hover:text-white'
        }`}
      >
        <Bot className="w-4 h-4" />
        <span className="text-sm font-medium">자동</span>
      </button>
    </div>
  );
}
