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
  onSelect: (keyword: string, category?: string) => void;
  loading: boolean;
}

export default function KeywordSelector({ onSelect, loading }: KeywordSelectorProps) {
  const [activeTab, setActiveTab] = useState<'trending' | 'evergreen' | 'custom'>('trending');
  const [trendingKeywords, setTrendingKeywords] = useState<Keyword[]>([]);
  const [evergreenKeywords, setEvergreenKeywords] = useState<Keyword[]>([]);
  const [customKeyword, setCustomKeyword] = useState('');
  const [customCategory, setCustomCategory] = useState('생활');
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [generatingKeyword, setGeneratingKeyword] = useState<string | null>(null);

  const categories = ['재테크', '생활', 'IT', '건강', '교육', '부동산', '취업'];

  // 키워드 로드
  useEffect(() => {
    loadKeywords();
  }, []);

  // loading이 false가 되면 generatingKeyword 초기화
  useEffect(() => {
    if (!loading) {
      setGeneratingKeyword(null);
    }
  }, [loading]);

  const loadKeywords = async () => {
    setIsLoading(true);
    try {
      const [trendingRes, evergreenRes] = await Promise.all([
        axios.get(`${API_URL}/api/keywords/trending`),
        axios.get(`${API_URL}/api/keywords/evergreen`)
      ]);

      setTrendingKeywords(trendingRes.data.keywords || []);
      setEvergreenKeywords(evergreenRes.data.keywords || []);
    } catch (error) {
      console.error('키워드 로드 실패:', error);
      // 더미 데이터
      setTrendingKeywords([
        { keyword: '연말정산', trend_score: 5, category: '재테크', source: 'trends' },
        { keyword: '청년도약계좌', trend_score: 4, category: '재테크', source: 'trends' },
        { keyword: '실업급여', trend_score: 4, category: '생활', source: 'trends' },
      ]);
      setEvergreenKeywords([
        { keyword: '연말정산 하는 법', trend_score: 3, category: '에버그린', source: 'evergreen' },
        { keyword: '실업급여 신청방법', trend_score: 3, category: '에버그린', source: 'evergreen' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // 키워드 새로고침 (AI 새추천)
  const refreshKeywords = async () => {
    setIsRefreshing(true);
    try {
      const response = await axios.post(`${API_URL}/api/keywords/refresh`);
      if (response.data.keywords) {
        if (activeTab === 'trending') {
          setTrendingKeywords(response.data.keywords);
        } else if (activeTab === 'evergreen') {
          setEvergreenKeywords(response.data.keywords);
        }
      }
    } catch (error) {
      console.error('새로고침 실패:', error);
      // 새로고침 실패 시 기존 데이터 다시 로드
      await loadKeywords();
    } finally {
      setIsRefreshing(false);
    }
  };

  // 키워드 선택
  const handleSelect = (keyword: string, category?: string) => {
    setGeneratingKeyword(keyword);
    onSelect(keyword, category);
  };

  // 직접 입력으로 글 생성
  const handleCustomSubmit = () => {
    if (!customKeyword.trim()) {
      alert('키워드를 입력해주세요.');
      return;
    }
    setGeneratingKeyword(customKeyword.trim());
    onSelect(customKeyword.trim(), customCategory);
  };

  // 트렌드 스코어 렌더링
  const renderTrendScore = (score: number) => {
    return Array(Math.min(score, 5)).fill(null).map((_, i) => (
      <span key={i}>🔥</span>
    ));
  };

  // 특정 키워드가 생성 중인지 확인
  const isKeywordGenerating = (keyword: string) => {
    return loading && generatingKeyword === keyword;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-800">키워드 선택</h2>

        {/* AI 새추천 버튼 - 트렌드/에버그린 탭에서만 표시 */}
        {activeTab !== 'custom' && (
          <button
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 flex items-center gap-2 transition-all"
            onClick={refreshKeywords}
            disabled={isRefreshing || loading}
          >
            {isRefreshing ? (
              <>
                <span className="animate-spin">⟳</span>
                새로고침 중...
              </>
            ) : (
              <>
                ✨ AI 새추천
              </>
            )}
          </button>
        )}
      </div>

      {/* 탭 버튼 */}
      <div className="flex gap-2 mb-6">
        <button
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'trending'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
          onClick={() => setActiveTab('trending')}
        >
          🔥 트렌드
        </button>
        <button
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'evergreen'
              ? 'bg-green-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
          onClick={() => setActiveTab('evergreen')}
        >
          🌲 에버그린
        </button>
        <button
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'custom'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
          onClick={() => setActiveTab('custom')}
        >
          ✏️ 직접 입력
        </button>
      </div>

      {/* 트렌드 키워드 */}
      {activeTab === 'trending' && (
        <div>
          <p className="text-sm text-gray-500 mb-4">Google Trends 기반 인기 키워드</p>

          {isLoading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : (
            <div className="grid gap-3">
              {trendingKeywords.map((kw, idx) => {
                const isGenerating = isKeywordGenerating(kw.keyword);
                const isOtherGenerating = loading && generatingKeyword && generatingKeyword !== kw.keyword;

                return (
                  <div
                    key={idx}
                    className={`flex items-center justify-between p-4 border rounded-lg transition-colors ${
                      isGenerating
                        ? 'border-purple-400 bg-purple-50'
                        : isOtherGenerating
                          ? 'opacity-50 cursor-not-allowed'
                          : 'hover:border-purple-400 hover:bg-purple-50 cursor-pointer'
                    }`}
                    onClick={() => !loading && handleSelect(kw.keyword, kw.category)}
                  >
                    <div>
                      <span className="font-medium text-gray-800">{kw.keyword}</span>
                      <span className="ml-2 text-xs px-2 py-1 bg-gray-100 rounded text-gray-500">
                        {kw.category}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-orange-500">
                        {renderTrendScore(kw.trend_score)}
                      </span>
                      <button
                        className={`px-3 py-1 text-sm rounded transition-colors ${
                          isGenerating
                            ? 'bg-purple-500 text-white'
                            : 'bg-purple-600 text-white hover:bg-purple-700'
                        } disabled:opacity-50`}
                        disabled={loading}
                      >
                        {isGenerating ? (
                          <span className="flex items-center gap-1">
                            <span className="animate-spin text-xs">⟳</span>
                            생성중...
                          </span>
                        ) : '선택'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* 에버그린 키워드 */}
      {activeTab === 'evergreen' && (
        <div>
          <p className="text-sm text-gray-500 mb-4">시즌/상시 인기 키워드</p>

          {isLoading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : (
            <div className="grid gap-3">
              {evergreenKeywords.map((kw, idx) => {
                const isGenerating = isKeywordGenerating(kw.keyword);
                const isOtherGenerating = loading && generatingKeyword && generatingKeyword !== kw.keyword;

                return (
                  <div
                    key={idx}
                    className={`flex items-center justify-between p-4 border rounded-lg transition-colors ${
                      isGenerating
                        ? 'border-green-400 bg-green-50'
                        : isOtherGenerating
                          ? 'opacity-50 cursor-not-allowed'
                          : 'hover:border-green-400 hover:bg-green-50 cursor-pointer'
                    }`}
                    onClick={() => !loading && handleSelect(kw.keyword, kw.category)}
                  >
                    <div>
                      <span className="font-medium text-gray-800">{kw.keyword}</span>
                      <span className="ml-2 text-xs px-2 py-1 bg-gray-100 rounded text-gray-500">
                        {kw.category}
                      </span>
                    </div>
                    <button
                      className={`px-3 py-1 text-sm rounded transition-colors ${
                        isGenerating
                          ? 'bg-green-500 text-white'
                          : 'bg-green-600 text-white hover:bg-green-700'
                      } disabled:opacity-50`}
                      disabled={loading}
                    >
                      {isGenerating ? (
                        <span className="flex items-center gap-1">
                          <span className="animate-spin text-xs">⟳</span>
                          생성중...
                        </span>
                      ) : '선택'}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* 직접 입력 */}
      {activeTab === 'custom' && (
        <div>
          <p className="text-sm text-gray-500 mb-4">원하는 키워드로 직접 글 생성</p>

          <div className="space-y-4">
            {/* 키워드 입력 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                키워드
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="예: 2025 연말정산, 청년도약계좌 조건"
                value={customKeyword}
                onChange={(e) => setCustomKeyword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !loading && handleCustomSubmit()}
                disabled={loading}
              />
            </div>

            {/* 카테고리 선택 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                카테고리
              </label>
              <div className="flex flex-wrap gap-2">
                {categories.map((cat) => (
                  <button
                    key={cat}
                    className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                      customCategory === cat
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                    onClick={() => setCustomCategory(cat)}
                    disabled={loading}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* 글 생성 버튼 */}
            <button
              className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              onClick={handleCustomSubmit}
              disabled={loading || !customKeyword.trim()}
            >
              {isKeywordGenerating(customKeyword.trim()) ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⟳</span>
                  글 생성 중...
                </span>
              ) : '이 키워드로 글 생성하기'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
