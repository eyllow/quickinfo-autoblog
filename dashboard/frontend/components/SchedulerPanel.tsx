'use client';

import { useState, useEffect } from 'react';

interface ScheduleItem {
  time: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'missed';
}

interface TodayPost {
  time: string;
  url: string;
  keyword: string;
  status: string;
}

interface SchedulerStatus {
  is_running: boolean;
  pid: string | null;
  today_completed: number;
  today_total: number;
  today_posts: TodayPost[];
  schedule: ScheduleItem[];
  next_publish: ScheduleItem | null;
  last_updated: string;
}

export default function SchedulerPanel() {
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchStatus = async () => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${API_BASE}/api/scheduler/status`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch scheduler status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // 30초마다 갱신
    return () => clearInterval(interval);
  }, []);

  const handleRestart = async () => {
    if (!confirm('스케줄러를 재시작하시겠습니까?')) return;
    setActionLoading(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${API_BASE}/api/scheduler/restart`, { method: 'POST' });
      const data = await res.json();
      alert(data.message);
      setTimeout(fetchStatus, 2000);
    } catch (error) {
      alert('재시작 실패');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    if (!confirm('스케줄러를 중지하시겠습니까?')) return;
    setActionLoading(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${API_BASE}/api/scheduler/stop`, { method: 'POST' });
      const data = await res.json();
      alert(data.message);
      setTimeout(fetchStatus, 2000);
    } catch (error) {
      alert('중지 실패');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusIcon = (s: string) => {
    switch (s) {
      case 'completed': return '✅';
      case 'running': return '🔄';
      case 'missed': return '❌';
      default: return '⏳';
    }
  };

  const getStatusText = (s: string) => {
    switch (s) {
      case 'completed': return '완료';
      case 'running': return '진행 중';
      case 'missed': return '실패';
      default: return '대기';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse flex items-center gap-2">
          <div className="h-4 w-4 bg-gray-200 rounded-full"></div>
          <div className="h-4 w-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold flex items-center gap-2">
          스케줄러 상태
          {status?.is_running ? (
            <span className="text-sm bg-green-100 text-green-700 px-2 py-1 rounded-full">
              실행 중
            </span>
          ) : (
            <span className="text-sm bg-red-100 text-red-700 px-2 py-1 rounded-full">
              중지됨
            </span>
          )}
        </h2>
        <div className="flex gap-2">
          <button
            onClick={handleRestart}
            disabled={actionLoading}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            재시작
          </button>
          <button
            onClick={handleStop}
            disabled={actionLoading || !status?.is_running}
            className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
          >
            중지
          </button>
        </div>
      </div>

      {/* 오늘 발행 현황 */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-2">
          오늘 발행: <span className="font-bold text-blue-600">{status?.today_completed}</span> / {status?.today_total}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: `${((status?.today_completed || 0) / (status?.today_total || 3)) * 100}%` }}
          />
        </div>
      </div>

      {/* 스케줄 목록 */}
      <div className="space-y-2 mb-4">
        {status?.schedule.map((item, idx) => (
          <div
            key={idx}
            className={`flex items-center justify-between p-2 rounded ${
              item.status === 'completed' ? 'bg-green-50' :
              item.status === 'running' ? 'bg-yellow-50' :
              item.status === 'missed' ? 'bg-red-50' : 'bg-gray-50'
            }`}
          >
            <div className="flex items-center gap-2">
              <span>{getStatusIcon(item.status)}</span>
              <span className="font-mono text-sm">{item.time}</span>
              <span className="text-xs bg-gray-200 px-2 py-0.5 rounded">{item.type}</span>
            </div>
            <span className="text-xs text-gray-500">
              {getStatusText(item.status)}
            </span>
          </div>
        ))}
      </div>

      {/* 다음 발행 */}
      {status?.next_publish && (
        <div className="text-sm text-gray-600 border-t pt-3">
          다음 발행: <span className="font-bold">{status.next_publish.time}</span> ({status.next_publish.type})
        </div>
      )}

      {/* 최근 발행 */}
      {status?.today_posts && status.today_posts.length > 0 && (
        <div className="mt-4 border-t pt-3">
          <div className="text-sm text-gray-600 mb-2">최근 발행:</div>
          <div className="space-y-1">
            {status.today_posts.map((post, idx) => (
              <div key={idx} className="text-xs text-gray-500 truncate">
                {post.time && <span className="text-gray-400 mr-1">{post.time}</span>}
                {post.url ? (
                  <a href={post.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                    {post.keyword || post.url}
                  </a>
                ) : (
                  <span>{post.keyword || '발행 완료'}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 마지막 업데이트 */}
      <div className="text-xs text-gray-400 mt-4 flex items-center justify-between">
        <span>
          마지막 업데이트: {status?.last_updated ? new Date(status.last_updated).toLocaleTimeString('ko-KR') : '-'}
        </span>
        <button
          onClick={fetchStatus}
          className="text-blue-500 hover:text-blue-700"
          title="새로고침"
        >
          ↻
        </button>
      </div>
    </div>
  );
}
