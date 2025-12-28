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
  const [naturalInstruction, setNaturalInstruction] = useState('');
  const [loading, setLoading] = useState(false);
  const [publishing, setPublishing] = useState(false);

  // 실제 콘텐츠 길이 계산 (HTML 태그 제외)
  const getContentLength = () => {
    const rawContent = article.raw_content || '';
    const textOnly = rawContent.replace(/<[^>]*>/g, '');
    return textOnly.length;
  };
  const contentLength = getContentLength();

  // 섹션 수정 (선택된 섹션에 대해)
  const handleEditSection = async () => {
    if (!selectedSection || !editInstruction) return;

    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/natural-edit`, {
        instruction: editInstruction,
        section_id: selectedSection
      });

      if (res.data.success) {
        // 전체 글 다시 가져오기
        const articleRes = await axios.get(`${API_URL}/api/articles/${article.id}`);
        if (articleRes.data) {
          onUpdate(articleRes.data);
        }
        alert(`${res.data.message || '수정 완료!'}`);
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

  // 자연어 수정 (전체 글에 대해)
  const handleNaturalEdit = async () => {
    if (!naturalInstruction) return;

    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/natural-edit`, {
        instruction: naturalInstruction
      });

      if (res.data.success) {
        // 전체 글 다시 가져오기
        const articleRes = await axios.get(`${API_URL}/api/articles/${article.id}`);
        if (articleRes.data) {
          onUpdate(articleRes.data);
        }
        alert(`[${res.data.action_type}] ${res.data.message || '수정 완료!'}`);
      } else {
        alert(res.data.error || '수정 실패');
      }
      setNaturalInstruction('');
    } catch (error: any) {
      console.error('Natural edit error:', error);
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
            className="px-6 py-2 bg-green-600 text-white rounded-lg disabled:opacity-50 hover:bg-green-700"
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

      {/* 자연어 수정 입력 (항상 표시) */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
        <h3 className="font-semibold mb-2 text-purple-700">AI 수정 요청</h3>
        <p className="text-sm text-gray-600 mb-3">
          자연어로 수정을 요청하세요. 예시:
        </p>
        <div className="flex flex-wrap gap-2 mb-3">
          <button
            onClick={() => setNaturalInstruction('전체적으로 더 친근하게 써줘')}
            className="text-xs px-2 py-1 bg-white border rounded hover:bg-gray-50"
          >
            더 친근하게
          </button>
          <button
            onClick={() => setNaturalInstruction('첫 번째 섹션 더 자세히 써줘')}
            className="text-xs px-2 py-1 bg-white border rounded hover:bg-gray-50"
          >
            첫 섹션 확장
          </button>
          <button
            onClick={() => setNaturalInstruction('표를 추가해줘')}
            className="text-xs px-2 py-1 bg-white border rounded hover:bg-gray-50"
          >
            표 추가
          </button>
          <button
            onClick={() => setNaturalInstruction('첫 번째 이미지 삭제해줘')}
            className="text-xs px-2 py-1 bg-white border rounded hover:bg-gray-50"
          >
            이미지 삭제
          </button>
          <button
            onClick={() => setNaturalInstruction('금융 관련 이미지로 바꿔줘')}
            className="text-xs px-2 py-1 bg-white border rounded hover:bg-gray-50"
          >
            이미지 교체
          </button>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={naturalInstruction}
            onChange={(e) => setNaturalInstruction(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleNaturalEdit()}
            placeholder="예: https://nts.go.kr 스크린샷으로 변경해줘, 두 번째 섹션 늘려줘..."
            className="flex-1 border rounded-lg px-4 py-2"
          />
          <button
            onClick={handleNaturalEdit}
            disabled={loading || !naturalInstruction}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg disabled:opacity-50 hover:bg-purple-700"
          >
            {loading ? '처리중...' : '수정 적용'}
          </button>
        </div>
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
            onSelect={() => setSelectedSection(selectedSection === section.id ? null : section.id)}
            articleId={article.id}
            onUpdate={(updatedSection) => {
              const updatedSections = [...article.sections];
              updatedSections[index] = updatedSection;
              onUpdate({ ...article, sections: updatedSections });
            }}
          />
        ))}
      </div>

      {/* 섹션 선택 시 개별 수정 */}
      {selectedSection && (
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <h3 className="font-semibold mb-2 text-blue-700">
            선택된 섹션 수정
          </h3>
          <textarea
            value={editInstruction}
            onChange={(e) => setEditInstruction(e.target.value)}
            placeholder="이 섹션에 대한 수정 요청을 입력하세요..."
            className="w-full border rounded-lg p-3 min-h-[80px]"
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleEditSection}
              disabled={loading || !editInstruction}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50 hover:bg-blue-700"
            >
              {loading ? '수정 중...' : '섹션 수정'}
            </button>
            <button
              onClick={() => {
                setSelectedSection(null);
                setEditInstruction('');
              }}
              className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
            >
              취소
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
