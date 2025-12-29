'use client';

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API_URL } from '@/lib/api';

export default function PublishStats() {
  const [stats, setStats] = useState({
    today: 0,
    week: 0,
    total: 0,
    drafts: 0
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchStats = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const res = await axios.get(`${API_URL}/api/publish/stats`);
      setStats({
        today: res.data.today_published || 0,
        week: res.data.this_week || 0,
        total: res.data.total_published || 0,
        drafts: res.data.drafts || 0
      });
    } catch (error) {
      console.error('Stats fetch failed:', error);
      // 에러 시 기존 값 유지
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    // 초기 로드
    fetchStats();

    // 발행 이벤트 리스너 등록
    const handlePublished = () => {
      console.log('Post published event received, refreshing stats...');
      fetchStats();
    };

    window.addEventListener('post-published', handlePublished);

    // 글로벌 refresh 함수 등록
    (window as any).refreshStats = fetchStats;

    // 30초마다 자동 새로고침
    const interval = setInterval(fetchStats, 30000);

    return () => {
      window.removeEventListener('post-published', handlePublished);
      delete (window as any).refreshStats;
      clearInterval(interval);
    };
  }, [fetchStats]);

  return (
    <div className="grid grid-cols-4 gap-4">
      <div className={`bg-white rounded-lg shadow p-4 text-center transition-opacity ${isRefreshing ? 'opacity-70' : ''}`}>
        <div className="text-3xl font-bold text-blue-600">{stats.today}</div>
        <div className="text-gray-500 text-sm">오늘</div>
      </div>
      <div className={`bg-white rounded-lg shadow p-4 text-center transition-opacity ${isRefreshing ? 'opacity-70' : ''}`}>
        <div className="text-3xl font-bold text-green-600">{stats.week}</div>
        <div className="text-gray-500 text-sm">이번 주</div>
      </div>
      <div className={`bg-white rounded-lg shadow p-4 text-center transition-opacity ${isRefreshing ? 'opacity-70' : ''}`}>
        <div className="text-3xl font-bold text-purple-600">{stats.total}</div>
        <div className="text-gray-500 text-sm">전체</div>
      </div>
      <div className={`bg-white rounded-lg shadow p-4 text-center transition-opacity ${isRefreshing ? 'opacity-70' : ''}`}>
        <div className="text-3xl font-bold text-orange-600">{stats.drafts}</div>
        <div className="text-gray-500 text-sm">대기 중</div>
      </div>
    </div>
  );
}
