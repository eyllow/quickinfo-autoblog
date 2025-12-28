'use client';

import { useState } from 'react';
import { Image as ImageIcon, Search, RefreshCw, Camera, Upload } from 'lucide-react';
import type { Article } from '@/app/page';

interface ImagePanelProps {
  article: Article | null;
}

interface PexelsImage {
  id: string;
  url: string;
  thumbnail: string;
  alt: string;
  photographer: string;
}

export default function ImagePanel({ article }: ImagePanelProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<PexelsImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<number | null>(null);

  const searchPexels = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const res = await fetch('http://localhost:8003/api/images/search/pexels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, count: 6 }),
      });
      const data = await res.json();
      setSearchResults(data.images || []);
    } catch (error) {
      console.error('Pexels search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectImage = async (image: PexelsImage) => {
    if (!article || selectedPosition === null) return;

    try {
      await fetch('http://localhost:8003/api/images/replace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          article_id: article.id,
          position: selectedPosition,
          new_image_url: image.url,
          source: 'pexels',
        }),
      });
      setSelectedPosition(null);
      setSearchResults([]);
      setSearchQuery('');
    } catch (error) {
      console.error('Image replace failed:', error);
    }
  };

  if (!article) {
    return (
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-4">
          <ImageIcon className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-bold text-white">이미지</h2>
        </div>
        <p className="text-sm text-muted-foreground text-center py-8">
          글이 생성되면 이미지를 관리할 수 있습니다
        </p>
      </div>
    );
  }

  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 mb-4">
        <ImageIcon className="w-5 h-5 text-purple-400" />
        <h2 className="text-lg font-bold text-white">이미지</h2>
        <span className="ml-auto text-sm text-muted-foreground">
          {article.image_types.length}개
        </span>
      </div>

      {/* 이미지 슬롯 */}
      <div className="space-y-2 mb-4">
        {article.image_types.map((type, idx) => (
          <div
            key={idx}
            onClick={() => setSelectedPosition(idx)}
            className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
              selectedPosition === idx
                ? 'bg-primary/20 border border-primary'
                : 'bg-secondary/50 hover:bg-secondary border border-transparent'
            }`}
          >
            <div className="flex items-center gap-3">
              {type === 'SCREENSHOT' ? (
                <Camera className="w-4 h-4 text-cyan-400" />
              ) : (
                <ImageIcon className="w-4 h-4 text-purple-400" />
              )}
              <span className="text-sm text-white">이미지 {idx + 1}</span>
            </div>
            <span
              className={`text-xs px-2 py-1 rounded ${
                type === 'SCREENSHOT'
                  ? 'bg-cyan-500/20 text-cyan-400'
                  : 'bg-purple-500/20 text-purple-400'
              }`}
            >
              {type}
            </span>
          </div>
        ))}
      </div>

      {/* Pexels 검색 */}
      {selectedPosition !== null && (
        <div className="border-t border-border pt-4 mt-4">
          <p className="text-sm text-muted-foreground mb-2">
            이미지 {selectedPosition + 1} 교체
          </p>
          <div className="flex gap-2 mb-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Pexels 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && searchPexels()}
                className="input w-full pl-10 text-sm"
              />
            </div>
            <button
              onClick={searchPexels}
              disabled={loading}
              className="btn-primary px-3"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* 검색 결과 */}
          {searchResults.length > 0 && (
            <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto">
              {searchResults.map((img) => (
                <button
                  key={img.id}
                  onClick={() => selectImage(img)}
                  className="relative aspect-square rounded-lg overflow-hidden border border-border hover:border-primary transition-colors group"
                >
                  <img
                    src={img.thumbnail}
                    alt={img.alt}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="text-xs text-white">선택</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 업로드 버튼 */}
      <button className="btn-secondary w-full mt-4 flex items-center justify-center gap-2 text-sm">
        <Upload className="w-4 h-4" />
        이미지 업로드
      </button>
    </div>
  );
}
