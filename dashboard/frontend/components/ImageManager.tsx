'use client';

import { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

interface ImageManagerProps {
  image: {
    id: string;
    url: string | null;
    status: string;
    type: string;
  };
  articleId: string;
  onUpdate: (image: any) => void;
}

export default function ImageManager({ image, articleId, onUpdate }: ImageManagerProps) {
  const [showOptions, setShowOptions] = useState(false);
  const [pexelsQuery, setPexelsQuery] = useState('');
  const [screenshotUrl, setScreenshotUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAction = async (action: string, query?: string) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/images/replace`, {
        article_id: articleId,
        image_id: image.id,
        action,
        query
      });
      onUpdate(res.data.image || { ...image, status: 'updated' });
      setShowOptions(false);
    } catch (error) {
      alert('이미지 처리 실패');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = () => {
    switch (image.status) {
      case 'success': return '[OK]';
      case 'failed': return '[X]';
      case 'pending': return '[...]';
      case 'deleted': return '[DEL]';
      default: return '[?]';
    }
  };

  return (
    <div className="border rounded-lg p-3">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span>{getStatusIcon()}</span>
          <span className="font-mono text-sm">{image.id}</span>
          <span className="text-xs text-gray-500">({image.type || 'N/A'})</span>
        </div>
        <button
          onClick={() => setShowOptions(!showOptions)}
          className="text-blue-600 text-sm"
        >
          {showOptions ? '닫기' : '변경'}
        </button>
      </div>

      {/* 이미지 미리보기 */}
      {image.url && image.status !== 'deleted' && (
        <img
          src={image.url}
          alt={image.id}
          className="mt-2 max-h-32 rounded"
        />
      )}

      {/* 옵션 패널 */}
      {showOptions && (
        <div className="mt-3 space-y-3 border-t pt-3">
          {/* Pexels 검색 */}
          <div>
            <label className="text-sm font-medium">Pexels 검색</label>
            <div className="flex gap-2 mt-1">
              <input
                type="text"
                value={pexelsQuery}
                onChange={(e) => setPexelsQuery(e.target.value)}
                placeholder="검색어..."
                className="flex-1 border rounded px-2 py-1 text-sm"
              />
              <button
                onClick={() => handleAction('pexels', pexelsQuery)}
                disabled={loading || !pexelsQuery}
                className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm disabled:opacity-50"
              >
                검색
              </button>
            </div>
          </div>

          {/* 스크린샷 */}
          <div>
            <label className="text-sm font-medium">스크린샷 URL</label>
            <div className="flex gap-2 mt-1">
              <input
                type="text"
                value={screenshotUrl}
                onChange={(e) => setScreenshotUrl(e.target.value)}
                placeholder="https://..."
                className="flex-1 border rounded px-2 py-1 text-sm"
              />
              <button
                onClick={() => handleAction('screenshot', screenshotUrl)}
                disabled={loading || !screenshotUrl}
                className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm disabled:opacity-50"
              >
                캡처
              </button>
            </div>
          </div>

          {/* 삭제 */}
          <button
            onClick={() => handleAction('delete')}
            disabled={loading}
            className="w-full px-3 py-1 bg-red-100 text-red-700 rounded text-sm"
          >
            이미지 삭제
          </button>
        </div>
      )}
    </div>
  );
}
