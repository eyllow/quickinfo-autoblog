'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

interface Keyword {
  keyword: string;
  trend_score: number;
  category: string;
  source: string;
}

interface KeywordSelectorProps {
  onSelect: (keyword: string) => void;
  loading: boolean;
}

export default function KeywordSelector({ onSelect, loading }: KeywordSelectorProps) {
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [customKeyword, setCustomKeyword] = useState('');
  const [activeTab, setActiveTab] = useState<'trending' | 'evergreen'>('trending');

  useEffect(() => {
    fetchKeywords();
  }, [activeTab]);

  const fetchKeywords = async () => {
    try {
      const endpoint = activeTab === 'trending' ? '/api/keywords/trending' : '/api/keywords/evergreen';
      const res = await axios.get(`${API_URL}${endpoint}`);
      setKeywords(res.data.keywords || []);
    } catch (error) {
      console.error('키워드 조회 실패:', error);
      // 더미 데이터
      setKeywords([
        { keyword: '연말정산', trend_score: 5, category: '재테크', source: activeTab },
        { keyword: '청년도약계좌', trend_score: 4, category: '재테크', source: activeTab },
        { keyword: '실업급여', trend_score: 4, category: '생활', source: activeTab },
      ]);
    }
  };

  const renderTrendScore = (score: number) => {
    return Array(score).fill('*').join('');
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">키워드 선택</h2>

      {/* 탭 */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveTab('trending')}
          className={`px-4 py-2 rounded ${
            activeTab === 'trending' ? 'bg-blue-600 text-white' : 'bg-gray-100'
          }`}
        >
          트렌드
        </button>
        <button
          onClick={() => setActiveTab('evergreen')}
          className={`px-4 py-2 rounded ${
            activeTab === 'evergreen' ? 'bg-green-600 text-white' : 'bg-gray-100'
          }`}
        >
          에버그린
        </button>
      </div>

      {/* 키워드 목록 */}
      <div className="space-y-2 mb-6">
        {keywords.map((kw, index) => (
          <button
            key={index}
            onClick={() => onSelect(kw.keyword)}
            disabled={loading}
            className="w-full text-left p-4 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition flex justify-between items-center disabled:opacity-50"
          >
            <span className="font-medium">{kw.keyword}</span>
            <span className="text-sm text-orange-500">{renderTrendScore(kw.trend_score)}</span>
          </button>
        ))}
      </div>

      {/* 직접 입력 */}
      <div className="border-t pt-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          직접 입력
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={customKeyword}
            onChange={(e) => setCustomKeyword(e.target.value)}
            placeholder="원하는 키워드 입력..."
            className="flex-1 border rounded-lg px-4 py-2"
          />
          <button
            onClick={() => customKeyword && onSelect(customKeyword)}
            disabled={!customKeyword || loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
          >
            {loading ? '생성 중...' : '글 생성'}
          </button>
        </div>
      </div>
    </div>
  );
}
