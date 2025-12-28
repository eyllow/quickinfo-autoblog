'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, Leaf, Search, Sparkles, RefreshCw } from 'lucide-react';

interface Keyword {
  keyword: string;
  trend_score: number;
  category: string;
  source: string;
}

interface KeywordPanelProps {
  selectedKeyword: string;
  onSelect: (keyword: string) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

export default function KeywordPanel({
  selectedKeyword,
  onSelect,
  onGenerate,
  isGenerating,
}: KeywordPanelProps) {
  const [activeTab, setActiveTab] = useState<'trends' | 'evergreen'>('trends');
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchKeywords();
  }, [activeTab]);

  const fetchKeywords = async () => {
    setLoading(true);
    try {
      const endpoint = activeTab === 'trends' ? 'trending' : 'evergreen';
      const res = await fetch(`http://localhost:8003/api/keywords/${endpoint}`);
      const data = await res.json();
      setKeywords(data.keywords || []);
    } catch (error) {
      console.error('Failed to fetch keywords:', error);
      // 더미 데이터
      setKeywords([
        { keyword: '연말정산', trend_score: 5, category: '재테크', source: activeTab },
        { keyword: '청년도약계좌', trend_score: 4, category: '재테크', source: activeTab },
        { keyword: '실업급여', trend_score: 4, category: '생활', source: activeTab },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredKeywords = keywords.filter((k) =>
    k.keyword.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-400';
    if (score >= 3) return 'text-yellow-400';
    return 'text-muted-foreground';
  };

  return (
    <div className="card h-full">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-bold text-white">키워드</h2>
        </div>

        {/* 탭 */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setActiveTab('trends')}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
              activeTab === 'trends'
                ? 'bg-primary/20 text-primary'
                : 'text-muted-foreground hover:bg-secondary'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            트렌드
          </button>
          <button
            onClick={() => setActiveTab('evergreen')}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
              activeTab === 'evergreen'
                ? 'bg-accent/20 text-accent'
                : 'text-muted-foreground hover:bg-secondary'
            }`}
          >
            <Leaf className="w-4 h-4" />
            에버그린
          </button>
        </div>

        {/* 검색 */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="키워드 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input w-full pl-10"
          />
        </div>
      </div>

      {/* 키워드 목록 */}
      <div className="p-4 max-h-[400px] overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-5 h-5 text-primary animate-spin" />
          </div>
        ) : (
          <div className="space-y-2">
            {filteredKeywords.map((item, idx) => (
              <button
                key={idx}
                onClick={() => onSelect(item.keyword)}
                className={`w-full flex items-center justify-between p-3 rounded-lg transition-all ${
                  selectedKeyword === item.keyword
                    ? 'bg-primary/20 border border-primary'
                    : 'bg-secondary/50 hover:bg-secondary border border-transparent'
                }`}
              >
                <div className="text-left">
                  <p className="font-medium text-white">{item.keyword}</p>
                  <p className="text-xs text-muted-foreground">{item.category}</p>
                </div>
                <div className={`font-bold ${getScoreColor(item.trend_score)}`}>
                  {'★'.repeat(item.trend_score)}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 글 생성 버튼 */}
      <div className="p-4 border-t border-border">
        <button
          onClick={onGenerate}
          disabled={!selectedKeyword || isGenerating}
          className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isGenerating ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              생성 중...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              글 생성하기
            </>
          )}
        </button>
      </div>
    </div>
  );
}
