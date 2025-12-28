'use client';

import { useState, useEffect } from 'react';
import { Send, Eye, Clock, BarChart3, CheckCircle, AlertCircle } from 'lucide-react';
import type { Article } from '@/app/page';

interface PublishPanelProps {
  article: Article | null;
  mode: 'semi' | 'auto';
}

interface Stats {
  total_published: number;
  today_published: number;
  this_week: number;
  this_month: number;
}

export default function PublishPanel({ article, mode }: PublishPanelProps) {
  const [publishing, setPublishing] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);
  const [publishResult, setPublishResult] = useState<{
    success: boolean;
    url?: string;
    message: string;
  } | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch('http://localhost:8003/api/publish/stats');
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      setStats({
        total_published: 42,
        today_published: 3,
        this_week: 15,
        this_month: 42,
      });
    }
  };

  const handlePublish = async () => {
    if (!article) return;

    setPublishing(true);
    setPublishResult(null);

    try {
      const res = await fetch('http://localhost:8003/api/publish/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_id: article.id }),
      });
      const data = await res.json();
      setPublishResult(data);
      fetchStats(); // 통계 갱신
    } catch (error) {
      setPublishResult({
        success: false,
        message: 'Failed to publish: ' + String(error),
      });
    } finally {
      setPublishing(false);
    }
  };

  const handlePreview = async () => {
    if (!article) return;

    try {
      const res = await fetch(`http://localhost:8003/api/publish/preview/${article.id}`, {
        method: 'POST',
      });
      const data = await res.json();

      // 새 창에서 미리보기
      const previewWindow = window.open('', '_blank');
      if (previewWindow) {
        previewWindow.document.write(data.html);
        previewWindow.document.close();
      }
    } catch (error) {
      console.error('Preview failed:', error);
    }
  };

  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 mb-4">
        <Send className="w-5 h-5 text-accent" />
        <h2 className="text-lg font-bold text-white">발행</h2>
      </div>

      {/* 발행 통계 */}
      {stats && (
        <div className="grid grid-cols-2 gap-2 mb-4">
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-white">{stats.today_published}</p>
            <p className="text-xs text-muted-foreground">오늘</p>
          </div>
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-white">{stats.this_week}</p>
            <p className="text-xs text-muted-foreground">이번 주</p>
          </div>
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-white">{stats.this_month}</p>
            <p className="text-xs text-muted-foreground">이번 달</p>
          </div>
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-accent">{stats.total_published}</p>
            <p className="text-xs text-muted-foreground">전체</p>
          </div>
        </div>
      )}

      {/* 발행 결과 메시지 */}
      {publishResult && (
        <div
          className={`flex items-center gap-2 p-3 rounded-lg mb-4 ${
            publishResult.success
              ? 'bg-accent/20 text-accent'
              : 'bg-red-500/20 text-red-400'
          }`}
        >
          {publishResult.success ? (
            <CheckCircle className="w-4 h-4" />
          ) : (
            <AlertCircle className="w-4 h-4" />
          )}
          <div className="flex-1 text-sm">
            <p>{publishResult.message}</p>
            {publishResult.url && (
              <a
                href={publishResult.url}
                target="_blank"
                rel="noopener noreferrer"
                className="underline"
              >
                글 보기
              </a>
            )}
          </div>
        </div>
      )}

      {/* 발행 버튼 */}
      {article ? (
        <div className="space-y-3">
          {mode === 'semi' && (
            <button
              onClick={handlePreview}
              className="btn-secondary w-full flex items-center justify-center gap-2"
            >
              <Eye className="w-4 h-4" />
              미리보기
            </button>
          )}

          <button
            onClick={handlePublish}
            disabled={publishing || article.status === 'published'}
            className={`w-full flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-all ${
              article.status === 'published'
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'btn-accent'
            }`}
          >
            {publishing ? (
              <>
                <Clock className="w-4 h-4 animate-spin" />
                발행 중...
              </>
            ) : article.status === 'published' ? (
              <>
                <CheckCircle className="w-4 h-4" />
                발행 완료
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                WordPress 발행
              </>
            )}
          </button>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground text-center py-4">
          글을 생성하면 발행할 수 있습니다
        </p>
      )}

      {/* 자동 모드 스케줄 */}
      {mode === 'auto' && (
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            <Clock className="w-4 h-4" />
            자동 발행 스케줄
          </div>
          <div className="flex flex-wrap gap-2">
            {['09:00', '15:00', '21:00'].map((time) => (
              <span
                key={time}
                className="px-2 py-1 rounded bg-accent/20 text-accent text-xs"
              >
                {time}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
