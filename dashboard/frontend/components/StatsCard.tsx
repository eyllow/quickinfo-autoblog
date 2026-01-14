'use client';

interface StatsCardProps {
  title: string;
  value: number;
  icon: string;
  color: 'blue' | 'green' | 'purple' | 'orange';
  subtitle?: string;
  trend?: {
    value: number;
    isUp: boolean;
  };
}

const colorStyles = {
  blue: {
    bg: 'bg-gradient-to-br from-blue-500 to-blue-600',
    light: 'bg-blue-100',
    text: 'text-blue-600',
  },
  green: {
    bg: 'bg-gradient-to-br from-green-500 to-green-600',
    light: 'bg-green-100',
    text: 'text-green-600',
  },
  purple: {
    bg: 'bg-gradient-to-br from-purple-500 to-purple-600',
    light: 'bg-purple-100',
    text: 'text-purple-600',
  },
  orange: {
    bg: 'bg-gradient-to-br from-orange-500 to-orange-600',
    light: 'bg-orange-100',
    text: 'text-orange-600',
  },
};

export default function StatsCard({ title, value, icon, color, subtitle, trend }: StatsCardProps) {
  const styles = colorStyles[color];

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300">
      <div className={`${styles.bg} px-4 py-3`}>
        <div className="flex items-center justify-between">
          <span className="text-white text-opacity-90 text-sm font-medium">{title}</span>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
      <div className="px-4 py-4">
        <div className="flex items-end justify-between">
          <div>
            <div className="text-3xl font-bold text-gray-800">{value.toLocaleString()}</div>
            {subtitle && (
              <div className="text-xs text-gray-500 mt-1">{subtitle}</div>
            )}
          </div>
          {trend && (
            <div className={`flex items-center text-sm ${trend.isUp ? 'text-green-500' : 'text-red-500'}`}>
              <span>{trend.isUp ? '↑' : '↓'}</span>
              <span className="ml-1">{Math.abs(trend.value)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
