'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import KeywordPanel from '@/components/KeywordPanel';
import ArticleEditor from '@/components/ArticleEditor';
import ImagePanel from '@/components/ImagePanel';
import PublishPanel from '@/components/PublishPanel';

export interface Article {
  id: string;
  keyword: string;
  title: string;
  sections: {
    id: string;
    title: string;
    content: string;
  }[];
  image_types: string[];
  status: string;
}

export default function Dashboard() {
  const [mode, setMode] = useState<'semi' | 'auto'>('semi');
  const [selectedKeyword, setSelectedKeyword] = useState<string>('');
  const [article, setArticle] = useState<Article | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleKeywordSelect = (keyword: string) => {
    setSelectedKeyword(keyword);
  };

  const handleGenerate = async () => {
    if (!selectedKeyword) return;

    setIsGenerating(true);
    try {
      const res = await fetch('http://localhost:8003/api/articles/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword: selectedKeyword, mode }),
      });
      const data = await res.json();
      setArticle(data);
    } catch (error) {
      console.error('Generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header mode={mode} onModeChange={setMode} />

      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* 좌측: 키워드 패널 */}
          <div className="col-span-3">
            <KeywordPanel
              selectedKeyword={selectedKeyword}
              onSelect={handleKeywordSelect}
              onGenerate={handleGenerate}
              isGenerating={isGenerating}
            />
          </div>

          {/* 중앙: 글 편집기 */}
          <div className="col-span-6">
            <ArticleEditor
              article={article}
              onUpdate={setArticle}
              mode={mode}
            />
          </div>

          {/* 우측: 이미지 & 발행 */}
          <div className="col-span-3 space-y-6">
            <ImagePanel article={article} />
            <PublishPanel article={article} mode={mode} />
          </div>
        </div>
      </main>
    </div>
  );
}
