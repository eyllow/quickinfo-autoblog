'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

export default function PublishStats() {
  const [stats, setStats] = useState({
    today: 0,
    week: 0,
    total: 0,
    drafts: 0
  });

  useEffect(() => {
    axios.get(`${API_URL}/api/publish/stats`).then(res => {
      setStats({
        today: res.data.today_published || 0,
        week: res.data.this_week || 0,
        total: res.data.total_published || 0,
        drafts: res.data.drafts || 0
      });
    }).catch(() => {
      // 더미 데이터
      setStats({
        today: 3,
        week: 15,
        total: 42,
        drafts: 2
      });
    });
  }, []);

  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="bg-white rounded-lg shadow p-4 text-center">
        <div className="text-3xl font-bold text-blue-600">{stats.today}</div>
        <div className="text-gray-500 text-sm">오늘</div>
      </div>
      <div className="bg-white rounded-lg shadow p-4 text-center">
        <div className="text-3xl font-bold text-green-600">{stats.week}</div>
        <div className="text-gray-500 text-sm">이번 주</div>
      </div>
      <div className="bg-white rounded-lg shadow p-4 text-center">
        <div className="text-3xl font-bold text-purple-600">{stats.total}</div>
        <div className="text-gray-500 text-sm">전체</div>
      </div>
      <div className="bg-white rounded-lg shadow p-4 text-center">
        <div className="text-3xl font-bold text-orange-600">{stats.drafts}</div>
        <div className="text-gray-500 text-sm">대기 중</div>
      </div>
    </div>
  );
}
