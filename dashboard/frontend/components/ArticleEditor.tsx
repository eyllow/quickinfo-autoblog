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
  const [targetLength, setTargetLength] = useState(article.total_length || 3000);
  const [loading, setLoading] = useState(false);
  const [publishing, setPublishing] = useState(false);

  const handleEditSection = async () => {
    if (!selectedSection || !editInstruction) return;

    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/edit-section`, {
        section_id: selectedSection,
        new_content: editInstruction
      });

      // 업데이트된 섹션 반영
      if (res.data.success) {
        const updatedSections = article.sections.map((s: any) =>
          s.id === selectedSection ? { ...s, content: editInstruction } : s
        );
        onUpdate({ ...article, sections: updatedSections });
      }
      setEditInstruction('');
    } catch (error) {
      alert('수정 실패');
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
        setTargetLength(res.data.new_length);
      }
    } catch (error) {
      alert('길이 조절 실패');
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async () => {
    setPublishing(true);
    try {
      const res = await axios.post(`${API_URL}/api/publish/`, {
        article_id: article.id
      });

      if (res.data.success) {
        alert(`발행 완료!\n${res.data.url || ''}`);
        onBack();
      }
    } catch (error) {
      alert('발행 실패');
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

      {/* 글 길이 조절 */}
      <div className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
        <span>글 길이: {targetLength.toLocaleString()}자</span>
        <div className="flex gap-2">
          <button
            onClick={() => handleAdjustLength('decrease')}
            disabled={loading}
            className="px-3 py-1 bg-gray-100 rounded disabled:opacity-50"
          >
            - 줄이기
          </button>
          <button
            onClick={() => handleAdjustLength('increase')}
            disabled={loading}
            className="px-3 py-1 bg-gray-100 rounded disabled:opacity-50"
          >
            + 늘리기
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
