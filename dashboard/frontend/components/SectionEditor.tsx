'use client';

import { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

interface Section {
  id: string;
  index: number;
  type: string;
  content: string;
  html?: string;  // 호환용
  image_url?: string;
}

interface SectionEditorProps {
  section: Section;
  keyword?: string;
  onUpdate: (updatedSection: Section) => void;
  onDelete: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  isFirst: boolean;
  isLast: boolean;
}

export default function SectionEditor({
  section,
  keyword = '',
  onUpdate,
  onDelete,
  onMoveUp,
  onMoveDown,
  isFirst,
  isLast
}: SectionEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(section.content || section.html || '');
  const [aiInstruction, setAiInstruction] = useState('');
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [showScreenshotOptions, setShowScreenshotOptions] = useState(false);
  const [customUrl, setCustomUrl] = useState('');

  // 섹션의 HTML 콘텐츠
  const sectionHtml = section.content || section.html || '';

  // 섹션 타입별 스타일 (테두리 없이 배경색으로 구분)
  const sectionStyles: Record<string, string> = {
    heading: 'bg-purple-50 ring-1 ring-purple-200',
    intro: 'bg-blue-50 ring-1 ring-blue-200',
    paragraph: 'bg-white ring-1 ring-gray-200',
    list: 'bg-green-50 ring-1 ring-green-200',
    table: 'bg-orange-50 ring-1 ring-orange-200',
    image: 'bg-pink-50 ring-1 ring-pink-200',
    cta: 'bg-red-50 ring-1 ring-red-200',
    quote: 'bg-yellow-50 ring-1 ring-yellow-200',
  };

  const typeLabels: Record<string, string> = {
    heading: '제목',
    intro: '서론',
    paragraph: '문단',
    list: '리스트',
    table: '표',
    image: '이미지',
    cta: 'CTA',
    quote: '인용',
  };

  // 직접 편집 저장
  const handleSaveEdit = () => {
    onUpdate({ ...section, content: editContent, html: editContent });
    setIsEditing(false);
  };

  // 직접 편집 취소
  const handleCancelEdit = () => {
    setEditContent(sectionHtml);
    setIsEditing(false);
  };

  // AI 수정 요청
  const handleAiEdit = async (instruction: string) => {
    if (!instruction.trim()) return;

    setIsAiLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/sections/edit`, {
        section_id: section.id,
        section_html: sectionHtml,
        instruction: instruction,
        section_type: section.type,
        keyword: keyword
      });

      if (response.data.success) {
        const updatedHtml = response.data.updated_html;
        onUpdate({ ...section, content: updatedHtml, html: updatedHtml });
        setEditContent(updatedHtml);
        setAiInstruction('');
      } else {
        alert(`수정 실패: ${response.data.error}`);
      }
    } catch (error: any) {
      console.error('AI 수정 오류:', error);
      alert(error.response?.data?.detail || 'AI 수정 중 오류가 발생했습니다.');
    } finally {
      setIsAiLoading(false);
    }
  };

  // 스크린샷 캡처
  const handleScreenshot = async (url: string) => {
    if (!url.trim()) return;

    setIsAiLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/sections/screenshot`, {
        url: url
      });

      if (response.data.success) {
        onUpdate({
          ...section,
          type: 'image',
          content: response.data.html,
          html: response.data.html,
          image_url: response.data.image_url
        });
        setEditContent(response.data.html);
        setShowScreenshotOptions(false);
        setCustomUrl('');
      } else {
        alert(`스크린샷 실패: ${response.data.error}`);
      }
    } catch (error: any) {
      console.error('스크린샷 오류:', error);
      alert(error.response?.data?.detail || '스크린샷 캡처 중 오류가 발생했습니다.');
    } finally {
      setIsAiLoading(false);
    }
  };

  // 글자수 계산
  const charCount = sectionHtml.replace(/<[^>]+>/g, '').length;

  // 퀵 버튼 정의 (섹션 타입별)
  const getQuickButtons = () => {
    if (section.type === 'heading') {
      return [
        { label: '매력적으로', instruction: '더 클릭하고 싶은 제목으로 바꿔줘' },
        { label: '키워드 강조', instruction: '키워드를 앞에 배치해줘' },
        { label: '숫자 추가', instruction: '숫자를 포함한 제목으로 바꿔줘' },
      ];
    }

    if (section.type === 'list') {
      return [
        { label: '더 자세히', instruction: '더 자세하게 설명해줘' },
        { label: '짧게', instruction: '더 짧게 요약해줘' },
        { label: '항목 추가', instruction: '관련 항목을 더 추가해줘' },
        { label: '표로 변환', instruction: '표로 변환해줘' },
      ];
    }

    if (section.type === 'table') {
      return [
        { label: '행 추가', instruction: '관련 행을 더 추가해줘' },
        { label: '스타일 개선', instruction: '표를 더 보기 좋게 개선해줘' },
      ];
    }

    // 기본 버튼 (paragraph, intro 등)
    return [
      { label: '더 자세히', instruction: '더 자세하게 설명해줘' },
      { label: '짧게', instruction: '더 짧게 요약해줘' },
      { label: '친근하게', instruction: '더 친근한 말투로 바꿔줘' },
      { label: '전문적으로', instruction: '더 전문적인 톤으로 바꿔줘' },
      { label: '예시 추가', instruction: '구체적인 예시를 추가해줘' },
    ];
  };

  return (
    <div className={`rounded-lg shadow overflow-hidden ${sectionStyles[section.type] || 'bg-white ring-1 ring-gray-200'}`}>
      {/* 섹션 헤더 */}
      <div className="px-4 py-2 bg-gray-50 border-b flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-600">
            {typeLabels[section.type] || '섹션'} {section.index + 1}
          </span>
          <span className="text-xs text-gray-400">({charCount}자)</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
            onClick={onMoveUp}
            disabled={isFirst || isAiLoading}
            title="위로 이동"
          >
            ▲
          </button>
          <button
            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
            onClick={onMoveDown}
            disabled={isLast || isAiLoading}
            title="아래로 이동"
          >
            ▼
          </button>
          <button
            className="p-1 text-red-400 hover:text-red-600"
            onClick={onDelete}
            disabled={isAiLoading}
            title="삭제"
          >
            ✕
          </button>
        </div>
      </div>

      {/* 섹션 콘텐츠 */}
      <div className={`p-4 ${isAiLoading ? 'opacity-50' : ''}`}>
        {isEditing ? (
          /* 편집 모드 */
          <div>
            <textarea
              className="w-full h-40 p-3 border rounded-lg font-mono text-sm resize-y focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
            />
            <div className="flex justify-end gap-2 mt-2">
              <button
                className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded"
                onClick={handleCancelEdit}
              >
                취소
              </button>
              <button
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                onClick={handleSaveEdit}
              >
                저장
              </button>
            </div>
          </div>
        ) : (
          /* 미리보기 모드 */
          <div
            className="prose max-w-none"
            dangerouslySetInnerHTML={{ __html: sectionHtml }}
          />
        )}
      </div>

      {/* 액션 버튼 */}
      <div className="px-4 py-3 bg-gray-50 border-t">
        <div className="flex flex-wrap gap-2 mb-3">
          {/* 직접 편집 버튼 */}
          <button
            className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
            onClick={() => {
              if (isEditing) {
                handleCancelEdit();
              } else {
                setEditContent(sectionHtml);
                setIsEditing(true);
              }
            }}
            disabled={isAiLoading}
          >
            ✏️ {isEditing ? '미리보기' : '직접 편집'}
          </button>

          {/* 이미지 섹션용 스크린샷 버튼 */}
          {section.type === 'image' && (
            <button
              className="px-3 py-1 text-sm bg-pink-100 text-pink-700 rounded hover:bg-pink-200"
              onClick={() => setShowScreenshotOptions(!showScreenshotOptions)}
              disabled={isAiLoading}
            >
              📸 스크린샷 변경
            </button>
          )}
        </div>

        {/* 스크린샷 옵션 */}
        {showScreenshotOptions && (
          <div className="mb-3 p-3 bg-pink-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">스크린샷 사이트 선택:</p>
            <div className="flex flex-wrap gap-2 mb-2">
              {[
                { label: '홈택스', url: 'https://hometax.go.kr' },
                { label: '국세청', url: 'https://nts.go.kr' },
                { label: '정부24', url: 'https://gov.kr' },
                { label: '국민연금', url: 'https://nps.or.kr' },
                { label: '건강보험', url: 'https://nhis.or.kr' },
                { label: '고용보험', url: 'https://ei.go.kr' },
              ].map((site) => (
                <button
                  key={site.label}
                  className="px-3 py-1 text-sm bg-white border rounded hover:bg-gray-50 disabled:opacity-50"
                  onClick={() => handleScreenshot(site.url)}
                  disabled={isAiLoading}
                >
                  {site.label}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                className="flex-1 px-3 py-1 text-sm border rounded"
                placeholder="직접 URL 입력 (예: https://example.com)"
                value={customUrl}
                onChange={(e) => setCustomUrl(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && customUrl.trim()) {
                    handleScreenshot(customUrl);
                  }
                }}
                disabled={isAiLoading}
              />
              <button
                className="px-3 py-1 text-sm bg-pink-600 text-white rounded hover:bg-pink-700 disabled:opacity-50"
                onClick={() => customUrl.trim() && handleScreenshot(customUrl)}
                disabled={isAiLoading || !customUrl.trim()}
              >
                캡처
              </button>
            </div>
          </div>
        )}

        {/* AI 수정 요청 */}
        <div className="space-y-2">
          <p className="text-xs text-gray-500">AI 수정 요청:</p>

          {/* 프리셋 버튼 */}
          <div className="flex flex-wrap gap-1">
            {getQuickButtons().map((btn) => (
              <button
                key={btn.label}
                className={`px-2 py-1 text-xs rounded hover:opacity-80 disabled:opacity-50 ${
                  section.type === 'heading'
                    ? 'bg-purple-100 text-purple-700'
                    : section.type === 'list'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-700'
                }`}
                onClick={() => handleAiEdit(btn.instruction)}
                disabled={isAiLoading}
              >
                {btn.label}
              </button>
            ))}
          </div>

          {/* 직접 입력 */}
          <div className="flex gap-2">
            <input
              type="text"
              className="flex-1 px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
              placeholder="수정 요청을 입력하세요..."
              value={aiInstruction}
              onChange={(e) => setAiInstruction(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAiEdit(aiInstruction)}
              disabled={isAiLoading}
            />
            <button
              className="px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50"
              onClick={() => handleAiEdit(aiInstruction)}
              disabled={isAiLoading || !aiInstruction.trim()}
            >
              {isAiLoading ? '처리중...' : 'AI 수정'}
            </button>
          </div>
        </div>
      </div>

      {/* 로딩 오버레이 */}
      {isAiLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
        </div>
      )}
    </div>
  );
}
