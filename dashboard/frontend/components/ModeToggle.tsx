'use client';

interface ModeToggleProps {
  mode: 'semi-auto' | 'full-auto';
  onModeChange: (mode: 'semi-auto' | 'full-auto') => void;
}

export default function ModeToggle({ mode, onModeChange }: ModeToggleProps) {
  return (
    <div className="flex items-center gap-4 bg-gray-100 p-1 rounded-lg">
      <button
        onClick={() => onModeChange('semi-auto')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition ${
          mode === 'semi-auto'
            ? 'bg-white shadow text-blue-600'
            : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        반자동
      </button>
      <button
        onClick={() => onModeChange('full-auto')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition ${
          mode === 'full-auto'
            ? 'bg-white shadow text-green-600'
            : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        완전자동
      </button>
    </div>
  );
}
