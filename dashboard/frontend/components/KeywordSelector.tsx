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

interface CustomGenerateOptions {
  keyword: string;
  category?: string;
  custom_context?: string;  // 직접 작성 시 작성 방향
}

interface KeywordSelectorProps {
  onSelect: (keyword: string, category?: string, options?: CustomGenerateOptions) => void;
  loading: boolean;
}

export default function KeywordSelector({ onSelect, loading }: KeywordSelectorProps) {
  const [activeTab, setActiveTab] = useState<'trending' | 'evergreen' | 'custom'>('trending');
  const [trendingKeywords, setTrendingKeywords] = useState<Keyword[]>([]);
  const [evergreenKeywords, setEvergreenKeywords] = useState<Keyword[]>([]);
  const [customKeyword, setCustomKeyword] = useState('');
  const [customCategory, setCustomCategory] = useState('생활');
  const [customDirection, setCustomDirection] = useState('');  // 작성 방향
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
      // 현재 탭에 따라 type 파라미터 설정
      const type = activeTab === 'evergreen' ? 'evergreen' : 'trend';
      const response = await axios.post(`${API_URL}/api/keywords/refresh`, { type });

      if (response.data.success && response.data.keywords) {
        if (activeTab === 'trending') {
          setTrendingKeywords(response.data.keywords);
        } else if (activeTab === 'evergreen') {
          setEvergreenKeywords(response.data.keywords);
        }
      } else if (response.data.keywords) {
        // 호환성: success 필드가 없는 경우에도 처리
        if (activeTab === 'trending') {
          setTrendingKeywords(response.data.keywords);
        } else if (activeTab === 'evergreen') {
          setEvergreenKeywords(response.data.keywords);
        }
      }
    } catch (error: any) {
      console.error('새로고침 실패:', error);
      alert(error.response?.data?.detail || '키워드 새로고침에 실패했습니다.');
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
      alert('주제를 입력해주세요.');
      return;
    }
    const keyword = customKeyword.trim();
    setGeneratingKeyword(keyword);

    // custom_context가 있으면 옵션으로 전달
    if (customDirection.trim()) {
      onSelect(keyword, customCategory, {
        keyword,
        category: customCategory,
        custom_context: customDirection.trim()
      });
    } else {
      onSelect(keyword, customCategory);
    }
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
          <p className="text-sm text-gray-500 mb-4">
            원하는 주제와 작성 방향을 입력하면 AI가 맞춤형 블로그 글을 생성합니다.
          </p>

          <div className="space-y-4">
            {/* 주제 입력 (필수) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                📝 주제 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="예: 2025년 1인 가구 절세 전략"
                value={customKeyword}
                onChange={(e) => setCustomKeyword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !loading && handleCustomSubmit()}
                disabled={loading}
              />
            </div>

            {/* 작성 방향 (선택) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                💡 작성 방향 / 포함할 내용 <span className="text-gray-400 text-xs">(선택)</span>
              </label>
              <textarea
                className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
                placeholder={`예:\n- 연말정산과 연계해서 설명\n- 월세 세액공제 강조\n- 청년 타겟으로 친근하게\n- 국세청 홈택스 링크 포함`}
                rows={5}
                value={customDirection}
                onChange={(e) => setCustomDirection(e.target.value)}
                disabled={loading}
              />
              <p className="text-xs text-gray-400 mt-1">
                작성 방향을 입력하면 AI가 해당 내용을 반영하여 글을 작성합니다.
              </p>
            </div>

            {/* 카테고리 선택 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                🏷️ 카테고리
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
              className={`w-full py-3 rounded-lg font-medium transition-all ${
                !customKeyword.trim() || loading
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700'
              }`}
              onClick={handleCustomSubmit}
              disabled={loading || !customKeyword.trim()}
            >
              {isKeywordGenerating(customKeyword.trim()) ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  글 생성 중...
                </span>
              ) : '✨ 글 생성하기'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
