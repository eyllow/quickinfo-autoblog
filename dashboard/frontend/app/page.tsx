'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import ModeToggle from '@/components/ModeToggle';
import KeywordSelector from '@/components/KeywordSelector';
import ArticleEditor from '@/components/ArticleEditor';
import PublishStats from '@/components/PublishStats';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

export default function Dashboard() {
  const [mode, setMode] = useState<'semi-auto' | 'full-auto'>('semi-auto');
  const [step, setStep] = useState<'keywords' | 'editing' | 'preview'>('keywords');
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);
  const [article, setArticle] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // 설정 로드
    axios.get(`${API_URL}/api/settings`).then(res => {
      setMode(res.data.publish_mode === 'auto' ? 'full-auto' : 'semi-auto');
    }).catch(() => {
      // 기본값 사용
    });
  }, []);

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

      const res = await axios.post(`${API_URL}/api/articles/generate`, requestBody);
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
      await axios.post(`${API_URL}/api/settings/mode`, {
        mode: newMode === 'full-auto' ? 'auto' : 'semi'
      });
      setMode(newMode);
    } catch (error) {
      console.error('모드 변경 실패:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            QuickInfo 발행 대시보드
          </h1>
          <ModeToggle mode={mode} onModeChange={handleModeChange} />
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* 통계 */}
        <PublishStats />

        {/* 반자동 모드 */}
        {mode === 'semi-auto' && (
          <div className="mt-8">
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
          <div className="mt-8 bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">자동 발행 스케줄</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
                <span>07:00 트렌드 발행</span>
                <span className="text-green-600">활성화</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
                <span>15:00 트렌드 발행</span>
                <span className="text-green-600">활성화</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
                <span>18:00 에버그린 발행</span>
                <span className="text-green-600">활성화</span>
              </div>
            </div>
            <p className="mt-4 text-gray-500 text-sm">
              완전자동 모드에서는 설정된 시간에 자동으로 글이 발행됩니다.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
