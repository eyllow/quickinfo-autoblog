'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import ModeToggle from '@/components/ModeToggle';
import KeywordSelector from '@/components/KeywordSelector';
import ArticleEditor from '@/components/ArticleEditor';
import LiveClock from '@/components/LiveClock';
import StatsCard from '@/components/StatsCard';
import RecentPosts from '@/components/RecentPosts';
import SchedulerPanel from '@/components/SchedulerPanel';
import LogPanel from '@/components/LogPanel';
import { getApiUrl } from '@/lib/api';

interface Stats {
  today: number;
  thisWeek: number;
  total: number;
  pending: number;
  yesterdayTotal: number;
}

export default function Dashboard() {
  const [mode, setMode] = useState<'semi-auto' | 'full-auto'>('semi-auto');
  const [step, setStep] = useState<'keywords' | 'editing' | 'preview'>('keywords');
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);
  const [article, setArticle] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<Stats>({
    today: 0,
    thisWeek: 0,
    total: 0,
    pending: 0,
    yesterdayTotal: 0,
  });

  useEffect(() => {
    // 설정 로드
    axios.get(`${getApiUrl()}/api/settings`).then(res => {
      setMode(res.data.publish_mode === 'auto' ? 'full-auto' : 'semi-auto');
    }).catch(() => {
      // 기본값 사용
    });

    // 통계 로드
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${getApiUrl()}/api/articles/stats`);
      setStats(res.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  // 키워드 선택 핸들러 - 직접 작성 모드 지원
  interface CustomGenerateOptions {
    keyword: string;
    category?: string;
    custom_context?: string;
  }

  const handleKeywordSelect = async (keyword: string, category?: string, options?: CustomGenerateOptions) => {
    setSelectedKeyword(keyword);
    setLoading(true);

    try {
      // 요청 본문 구성
      const requestBody: any = {
        keyword,
        is_evergreen: false
      };

      // 직접 작성 모드: 카테고리 및 작성 방향 추가
      if (options?.custom_context) {
        requestBody.category = options.category || category;
        requestBody.custom_context = options.custom_context;
        console.log('직접 작성 모드:', requestBody);
      } else if (category) {
        requestBody.category = category;
      }

      const res = await axios.post(`${getApiUrl()}/api/articles/generate`, requestBody);
      setArticle(res.data);
      setStep('editing');
    } catch (error) {
      console.error('글 생성 실패:', error);
      alert('글 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleModeChange = async (newMode: 'semi-auto' | 'full-auto') => {
    try {
      await axios.post(`${getApiUrl()}/api/settings/mode`, {
        mode: newMode === 'full-auto' ? 'auto' : 'semi'
      });
      setMode(newMode);
    } catch (error) {
      console.error('모드 변경 실패:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 헤더 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-800">
              QuickInfo 발행 대시보드
            </h1>
            <div className="flex items-center gap-6">
              <LiveClock />
              <ModeToggle mode={mode} onModeChange={handleModeChange} />
            </div>
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* 통계 카드 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatsCard
            title="오늘 발행"
            value={stats.today}
            icon="📝"
            color="blue"
            subtitle="발행된 글"
            trend={stats.yesterdayTotal > 0 ? {
              value: stats.today - stats.yesterdayTotal,
              isUp: stats.today >= stats.yesterdayTotal
            } : undefined}
          />
          <StatsCard
            title="이번 주"
            value={stats.thisWeek}
            icon="📅"
            color="green"
            subtitle="목표: 21개"
          />
          <StatsCard
            title="전체 발행"
            value={stats.total}
            icon="📊"
            color="purple"
            subtitle="누적 발행"
          />
          <StatsCard
            title="대기 중"
            value={stats.pending}
            icon="⏳"
            color="orange"
            subtitle="발행 예정"
          />
        </div>

        {/* 스케줄러 + 최근 발행 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <SchedulerPanel />
          <RecentPosts />
        </div>

        {/* 실시간 로그 패널 */}
        <div className="mb-6">
          <LogPanel />
        </div>

        {/* 반자동 모드 */}
        {mode === 'semi-auto' && (
          <div className="mt-6">
            {step === 'keywords' && (
              <KeywordSelector
                onSelect={handleKeywordSelect}
                loading={loading}
              />
            )}

            {step === 'editing' && article && (
              <ArticleEditor
                article={article}
                onUpdate={setArticle}
                onBack={() => setStep('keywords')}
                onPublish={() => setStep('preview')}
              />
            )}
          </div>
        )}

        {/* 완전자동 모드 */}
        {mode === 'full-auto' && (
          <div className="mt-6 bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">자동 발행 스케줄</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🌅</span>
                  <div>
                    <div className="font-medium">07:00 트렌드 발행</div>
                    <div className="text-sm text-gray-500">실시간 인기 키워드</div>
                  </div>
                </div>
                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">활성화</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">☀️</span>
                  <div>
                    <div className="font-medium">15:00 트렌드 발행</div>
                    <div className="text-sm text-gray-500">오후 인기 키워드</div>
                  </div>
                </div>
                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">활성화</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🌙</span>
                  <div>
                    <div className="font-medium">18:00 에버그린 발행</div>
                    <div className="text-sm text-gray-500">장기 유용 콘텐츠</div>
                  </div>
                </div>
                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">활성화</span>
              </div>
            </div>
            <p className="mt-4 text-gray-500 text-sm text-center">
              완전자동 모드에서는 설정된 시간에 자동으로 글이 발행됩니다.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
