'use client';

import { useState, useEffect, useRef } from 'react';
import { getApiUrl } from '@/lib/api';

interface LogEntry {
  timestamp: string;
  level: 'info' | 'success' | 'warning' | 'error' | 'progress';
  stage: string;
  message: string;
  details?: Record<string, any>;
}

const STAGE_LABELS: Record<string, string> = {
  keyword: '키워드',
  context: '맥락 검증',
  generate: 'AI 생성',
  image: '이미지',
  publish: '발행',
};

const LEVEL_STYLES: Record<string, { icon: string; color: string }> = {
  info: { icon: 'i', color: 'text-blue-400' },
  success: { icon: '✓', color: 'text-green-400' },
  warning: { icon: '!', color: 'text-yellow-400' },
  error: { icon: '✗', color: 'text-red-400' },
  progress: { icon: '◌', color: 'text-purple-400' },
};

export default function LogPanel() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // 기존 로그 로드
    fetch(`${getApiUrl()}/api/logs`)
      .then(res => res.json())
      .then(data => setLogs(data.logs || []))
      .catch(console.error);

    // SSE 연결
    const connectSSE = () => {
      const eventSource = new EventSource(`${getApiUrl()}/api/logs/stream`);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
      };

      eventSource.addEventListener('log', (event) => {
        try {
          const logEntry = JSON.parse(event.data);
          setLogs(prev => [...prev.slice(-99), logEntry]); // 최근 100개 유지
        } catch (e) {
          console.error('로그 파싱 실패:', e);
        }
      });

      eventSource.addEventListener('heartbeat', () => {
        // 연결 유지 확인
      });

      eventSource.onerror = () => {
        setIsConnected(false);
        eventSource.close();
        // 3초 후 재연결 시도
        setTimeout(() => {
          connectSSE();
        }, 3000);
      };
    };

    connectSSE();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // 자동 스크롤
  useEffect(() => {
    if (logContainerRef.current && !isMinimized) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, isMinimized]);

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const clearLogs = async () => {
    try {
      await fetch(`${getApiUrl()}/api/logs`, { method: 'DELETE' });
      setLogs([]);
    } catch (error) {
      console.error('로그 초기화 실패:', error);
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg shadow-lg overflow-hidden mt-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800">
        <div className="flex items-center gap-2">
          <span className="text-white font-medium text-sm">콘텐츠 생성 로그</span>
          <span
            className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
            title={isConnected ? '연결됨' : '연결 끊김'}
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearLogs}
            className="text-gray-400 hover:text-white text-xs px-2 py-1 rounded hover:bg-gray-700 transition-colors"
            title="로그 초기화"
          >
            초기화
          </button>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="text-gray-400 hover:text-white px-2 py-1 rounded hover:bg-gray-700 transition-colors"
          >
            {isMinimized ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {/* 로그 내용 */}
      {!isMinimized && (
        <div
          ref={logContainerRef}
          className="h-48 overflow-y-auto p-3 font-mono text-xs"
        >
          {logs.length === 0 ? (
            <div className="text-gray-500 text-center py-8">
              로그가 없습니다. 콘텐츠를 생성하면 여기에 표시됩니다.
            </div>
          ) : (
            logs.map((log, index) => {
              const style = LEVEL_STYLES[log.level] || LEVEL_STYLES.info;
              return (
                <div
                  key={index}
                  className="flex gap-2 py-1 border-b border-gray-800 last:border-0 items-start"
                >
                  <span className="text-gray-500 flex-shrink-0 w-16">
                    {formatTime(log.timestamp)}
                  </span>
                  <span className={`${style.color} flex-shrink-0 w-4 text-center`}>
                    {style.icon}
                  </span>
                  <span className="text-gray-400 flex-shrink-0 w-16 truncate">
                    [{STAGE_LABELS[log.stage] || log.stage}]
                  </span>
                  <span className={`${style.color} flex-1 break-all`}>
                    {log.message}
                  </span>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
