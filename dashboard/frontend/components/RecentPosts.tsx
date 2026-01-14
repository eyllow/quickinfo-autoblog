'use client';

import { useState, useEffect } from 'react';

interface Post {
  id: number;
  title: string;
  published_at: string;
  category: string;
  url?: string;
}

export default function RecentPosts() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecentPosts();
  }, []);

  const fetchRecentPosts = async () => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${API_BASE}/api/articles/recent?limit=5`);
      if (res.ok) {
        const data = await res.json();
        setPosts(data.posts || []);
      }
    } catch (error) {
      console.error('Failed to fetch recent posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;

    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  const getCategoryBadge = (category: string) => {
    const colors: Record<string, string> = {
      '트렌드': 'bg-red-100 text-red-600',
      '에버그린': 'bg-green-100 text-green-600',
      '재테크': 'bg-blue-100 text-blue-600',
      '생활정보': 'bg-purple-100 text-purple-600',
      '건강': 'bg-teal-100 text-teal-600',
      'IT테크': 'bg-indigo-100 text-indigo-600',
    };
    return colors[category] || 'bg-gray-100 text-gray-600';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          <div className="h-3 bg-gray-200 rounded w-full"></div>
          <div className="h-3 bg-gray-200 rounded w-full"></div>
          <div className="h-3 bg-gray-200 rounded w-full"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-3">
        <div className="flex items-center justify-between">
          <span className="text-white font-medium">최근 발행</span>
          <span className="text-white text-opacity-80 text-sm">{posts.length}개</span>
        </div>
      </div>
      <div className="divide-y divide-gray-100">
        {posts.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500">
            발행된 글이 없습니다.
          </div>
        ) : (
          posts.map((post, idx) => (
            <div key={post.id || idx} className="px-4 py-3 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  {post.url ? (
                    <a
                      href={post.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-gray-800 hover:text-blue-600 line-clamp-1"
                    >
                      {post.title}
                    </a>
                  ) : (
                    <span className="text-sm font-medium text-gray-800 line-clamp-1">
                      {post.title}
                    </span>
                  )}
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryBadge(post.category)}`}>
                      {post.category}
                    </span>
                    <span className="text-xs text-gray-400">{formatTime(post.published_at)}</span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
