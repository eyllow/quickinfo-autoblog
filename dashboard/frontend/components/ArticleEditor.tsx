'use client';

import { useState } from 'react';
import axios from 'axios';
import SectionEditor from './SectionEditor';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

interface ArticleEditorProps {
  article: any;
  onUpdate: (article: any) => void;
  onBack: () => void;
  onPublish: () => void;
}

export default function ArticleEditor({ article, onUpdate, onBack, onPublish }: ArticleEditorProps) {
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [editInstruction, setEditInstruction] = useState('');
  const [loading, setLoading] = useState(false);
  const [publishing, setPublishing] = useState(false);

  // 실제 콘텐츠 길이 계산 (HTML 태그 제외)
  const getContentLength = () => {
    const rawContent = article.raw_content || '';
    const textOnly = rawContent.replace(/<[^>]*>/g, '');
    return textOnly.length;
  };
  const contentLength = getContentLength();

  const handleEditSection = async () => {
    if (!selectedSection || !editInstruction) return;

    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/edit-section`, {
        section_id: selectedSection,
        instruction: editInstruction  // AI 수정 지시
      });

      // 업데이트된 섹션 반영
      if (res.data.success && res.data.section) {
        const updatedSections = article.sections.map((s: any) =>
          s.id === selectedSection ? res.data.section : s
        );
        onUpdate({ ...article, sections: updatedSections });
        alert('수정 완료!');
      } else {
        alert(res.data.error || '수정 실패');
      }
      setEditInstruction('');
      setSelectedSection(null);
    } catch (error: any) {
      console.error('Edit error:', error);
      alert(error.response?.data?.detail || '수정 실패');
    } finally {
      setLoading(false);
    }
  };

  const handleAdjustLength = async (type: 'increase' | 'decrease') => {
    const targetMap: { [key: string]: string } = {
      decrease: 'short',
      increase: 'long'
    };

    setLoading(true);

    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/adjust-length`, {
        target_length: targetMap[type]
      });
      if (res.data.success) {
        // 전체 글 다시 가져오기
        const articleRes = await axios.get(`${API_URL}/api/articles/${article.id}`);
        if (articleRes.data) {
          onUpdate(articleRes.data);
        }
        alert(`글 길이가 ${res.data.new_length.toLocaleString()}자로 조절되었습니다.`);
      } else {
        alert(res.data.error || '길이 조절 실패');
      }
    } catch (error: any) {
      console.error('Adjust length error:', error);
      alert(error.response?.data?.detail || '길이 조절 실패');
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!confirm('WordPress에 발행하시겠습니까?')) return;

    setPublishing(true);
    try {
      const res = await axios.post(`${API_URL}/api/publish/`, {
        article_id: article.id,
        status: 'publish'
      });

      if (res.data.success) {
        alert(`발행 완료!\n\nURL: ${res.data.url || '확인 필요'}\nPost ID: ${res.data.post_id || '-'}`);
        onBack();
      } else {
        alert(`발행 실패: ${res.data.error || '알 수 없는 오류'}`);
      }
    } catch (error: any) {
      console.error('Publish error:', error);
      const detail = error.response?.data?.detail || error.message || '발행 실패';
      alert(`발행 실패:\n${detail}`);
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 상단 컨트롤 */}
      <div className="flex justify-between items-center">
        <button
          onClick={onBack}
          className="text-gray-600 hover:text-gray-900"
        >
          &larr; 키워드 선택으로
        </button>
        <div className="flex gap-2">
          <button
            onClick={handlePublish}
            disabled={publishing}
            className="px-6 py-2 bg-green-600 text-white rounded-lg disabled:opacity-50"
          >
            {publishing ? '발행 중...' : '발행하기'}
          </button>
        </div>
      </div>

      {/* 제목 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold">{article.title}</h2>
        <p className="text-gray-500 mt-2">키워드: {article.keyword}</p>
      </div>

      {/* 글 정보 & 길이 조절 */}
      <div className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="font-medium">글 길이: {contentLength.toLocaleString()}자</span>
          <span className="text-sm text-gray-500">카테고리: {article.category || '트렌드'}</span>
          {article.has_coupang && <span className="text-sm text-orange-500">쿠팡 포함</span>}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleAdjustLength('decrease')}
            disabled={loading}
            className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
          >
            {loading ? '처리중...' : '- 줄이기'}
          </button>
          <button
            onClick={() => handleAdjustLength('increase')}
            disabled={loading}
            className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
          >
            {loading ? '처리중...' : '+ 늘리기'}
          </button>
        </div>
      </div>

      {/* 섹션 목록 */}
      <div className="space-y-4">
        {article.sections?.map((section: any, index: number) => (
          <SectionEditor
            key={section.id}
            section={section}
            isSelected={selectedSection === section.id}
            onSelect={() => setSelectedSection(section.id)}
            articleId={article.id}
            onUpdate={(updatedSection) => {
              const updatedSections = [...article.sections];
              updatedSections[index] = updatedSection;
              onUpdate({ ...article, sections: updatedSections });
            }}
          />
        ))}
      </div>

      {/* 수정 요청 입력 */}
      {selectedSection && (
        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2">수정 요청</h3>
          <textarea
            value={editInstruction}
            onChange={(e) => setEditInstruction(e.target.value)}
            placeholder="예: 좀 더 쉽게 설명해줘, 표를 추가해줘, 예시를 넣어줘..."
            className="w-full border rounded-lg p-3 min-h-[100px]"
          />
          <button
            onClick={handleEditSection}
            disabled={loading || !editInstruction}
            className="mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
          >
            {loading ? '수정 중...' : '수정 적용'}
          </button>
        </div>
      )}
    </div>
  );
}
