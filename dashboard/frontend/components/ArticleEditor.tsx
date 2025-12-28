'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

interface Section {
  id: string;
  index: number;
  type: string;  // heading, image, paragraph, list, table, quote
  html: string;
}

interface Article {
  id: string;
  title: string;
  keyword: string;
  category: string;
  raw_content: string;
  sections_v2?: Section[];  // 새 섹션 구조
  sections?: any[];  // 기존 호환용
  has_coupang: boolean;
}

interface ArticleEditorProps {
  article: Article;
  onUpdate: (article: Article) => void;
  onBack: () => void;
  onPublish: () => void;
}

export default function ArticleEditor({ article: initialArticle, onUpdate, onBack, onPublish }: ArticleEditorProps) {
  const [article, setArticle] = useState<Article>(initialArticle);
  const [sections, setSections] = useState<Section[]>([]);
  const [editInputs, setEditInputs] = useState<Record<string, string>>({});
  const [loadingSections, setLoadingSections] = useState<Record<string, boolean>>({});
  const [isPublishing, setIsPublishing] = useState(false);
  const [globalInstruction, setGlobalInstruction] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // 초기 섹션 설정
  useEffect(() => {
    // sections_v2가 있으면 사용, 없으면 raw_content에서 파싱
    if (initialArticle.sections_v2 && initialArticle.sections_v2.length > 0) {
      setSections(initialArticle.sections_v2);
    } else if (initialArticle.raw_content) {
      // 프론트엔드에서 파싱 (폴백)
      const parsed = parseContentToSections(initialArticle.raw_content);
      setSections(parsed);
    }
  }, [initialArticle]);

  // HTML을 섹션으로 파싱 (폴백용)
  const parseContentToSections = (html: string): Section[] => {
    const result: Section[] = [];
    const parser = new DOMParser();
    const doc = parser.parseFromString(`<div>${html}</div>`, 'text/html');
    const container = doc.body.firstChild as HTMLElement;

    if (!container) return result;

    let index = 0;
    Array.from(container.children).forEach((element) => {
      const tagName = element.tagName.toLowerCase();
      const outerHTML = element.outerHTML;
      const textContent = element.textContent?.trim() || '';

      // 빈 요소 제외 (이미지는 예외)
      if (!outerHTML.trim()) return;
      if (!textContent && !['figure', 'img'].includes(tagName)) return;

      const type = getElementType(tagName, outerHTML);
      result.push({
        id: `section-${Math.random().toString(36).substr(2, 8)}`,
        index: index++,
        type,
        html: outerHTML
      });
    });

    return result;
  };

  // 요소 타입 판별
  const getElementType = (tagName: string, html: string): string => {
    if (['h1', 'h2', 'h3', 'h4'].includes(tagName)) return 'heading';
    if (['figure', 'img'].includes(tagName) || html.includes('<img')) return 'image';
    if (['ul', 'ol'].includes(tagName)) return 'list';
    if (tagName === 'table') return 'table';
    if (tagName === 'blockquote') return 'quote';
    return 'paragraph';
  };

  // 섹션 수정 요청 - 새 API 사용
  const handleSectionEdit = async (sectionId: string) => {
    const instruction = editInputs[sectionId];
    if (!instruction?.trim()) return;

    const section = sections.find(s => s.id === sectionId);
    if (!section) return;

    setLoadingSections(prev => ({ ...prev, [sectionId]: true }));

    try {
      // 스크린샷 요청 감지
      if (instruction.includes('스크린샷') || instruction.includes('캡처')) {
        const response = await axios.post(`${API_URL}/api/sections/screenshot`, {
          keyword: instruction
        });

        if (response.data.success && response.data.html) {
          // 현재 섹션 뒤에 스크린샷 섹션 추가
          const newSection: Section = {
            id: `section-screenshot-${Date.now()}`,
            index: section.index + 1,
            type: 'image',
            html: response.data.html
          };

          setSections(prev => {
            const newSections = [...prev];
            const insertIndex = newSections.findIndex(s => s.id === sectionId) + 1;
            newSections.splice(insertIndex, 0, newSection);
            // 인덱스 재정렬
            return newSections.map((s, i) => ({ ...s, index: i }));
          });

          alert('스크린샷이 추가되었습니다.');
        } else {
          alert(`스크린샷 실패: ${response.data.error || '알 수 없는 오류'}`);
        }
      } else {
        // 일반 섹션 수정 - /api/sections/edit 사용
        const response = await axios.post(`${API_URL}/api/sections/edit`, {
          section_id: sectionId,
          section_html: section.html,
          instruction: instruction,
          section_type: section.type,
          keyword: article.keyword
        });

        if (response.data.success) {
          // 해당 섹션만 업데이트
          setSections(prev =>
            prev.map(s =>
              s.id === sectionId
                ? { ...s, html: response.data.updated_html }
                : s
            )
          );
          alert('섹션이 수정되었습니다.');
        } else {
          alert(`수정 실패: ${response.data.error || '알 수 없는 오류'}`);
        }
      }

      // 입력창 초기화
      setEditInputs(prev => ({ ...prev, [sectionId]: '' }));

    } catch (error: any) {
      console.error('섹션 수정 오류:', error);
      alert(error.response?.data?.detail || '수정 중 오류가 발생했습니다.');
    } finally {
      setLoadingSections(prev => ({ ...prev, [sectionId]: false }));
    }
  };

  // 섹션 삭제
  const handleDeleteSection = (sectionId: string) => {
    if (!confirm('이 섹션을 삭제하시겠습니까?')) return;
    setSections(prev => prev.filter(s => s.id !== sectionId).map((s, i) => ({ ...s, index: i })));
  };

  // 전체 수정 요청
  const handleGlobalEdit = async () => {
    if (!globalInstruction?.trim()) return;

    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/articles/${article.id}/natural-edit`, {
        instruction: globalInstruction
      });

      if (response.data.success && response.data.updated_content) {
        // 전체 콘텐츠 다시 파싱
        const newSections = parseContentToSections(response.data.updated_content);
        setSections(newSections);
        setGlobalInstruction('');
        alert(`[${response.data.action_type}] ${response.data.message || '수정 완료!'}`);
      } else {
        alert(response.data.error || '수정 실패');
      }
    } catch (error: any) {
      console.error('전체 수정 오류:', error);
      alert(error.response?.data?.detail || '수정 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 발행 - 모든 섹션 합쳐서 WordPress 발행
  const handlePublish = async () => {
    if (!confirm('WordPress에 발행하시겠습니까?')) return;

    setIsPublishing(true);

    try {
      // 모든 섹션의 HTML 합치기
      const fullContent = sections.map(s => s.html).join('\n');

      // 먼저 content 업데이트
      try {
        await axios.put(`${API_URL}/api/articles/${article.id}/content`, {
          content: fullContent
        });
      } catch (e) {
        // content 업데이트 API가 없으면 무시
      }

      // WordPress 발행
      const response = await axios.post(`${API_URL}/api/publish/`, {
        article_id: article.id,
        status: 'publish'
      });

      if (response.data.success) {
        alert(`발행 완료!\n\nURL: ${response.data.url || '확인 필요'}\nPost ID: ${response.data.post_id || '-'}`);
        onBack();
      } else {
        alert(`발행 실패: ${response.data.error || '알 수 없는 오류'}`);
      }
    } catch (error: any) {
      console.error('발행 오류:', error);
      alert(`발행 실패:\n${error.response?.data?.detail || error.message}`);
    } finally {
      setIsPublishing(false);
    }
  };

  // 섹션 타입별 스타일
  const getSectionStyle = (type: string): string => {
    const styles: Record<string, string> = {
      heading: 'border-l-purple-500',
      image: 'border-l-blue-500',
      paragraph: 'border-l-gray-300',
      list: 'border-l-green-500',
      table: 'border-l-orange-500',
      quote: 'border-l-yellow-500',
    };
    return styles[type] || 'border-l-gray-300';
  };

  // 섹션 타입별 라벨
  const getSectionLabel = (type: string): string => {
    const labels: Record<string, string> = {
      heading: '제목',
      image: '이미지',
      paragraph: '문단',
      list: '리스트',
      table: '표',
      quote: '인용',
    };
    return labels[type] || '콘텐츠';
  };

  // 퀵 버튼 정의
  const getQuickButtons = (type: string) => {
    const common = [
      { label: '더 자세히', instruction: '더 자세하게 설명해줘' },
      { label: '짧게', instruction: '더 짧게 요약해줘' },
      { label: '친근하게', instruction: '더 친근한 말투로 바꿔줘' },
    ];

    const typeSpecific: Record<string, typeof common> = {
      heading: [
        { label: '매력적으로', instruction: '더 클릭하고 싶은 제목으로 바꿔줘' },
        { label: '키워드 강조', instruction: '키워드를 앞쪽에 배치해줘' },
        { label: '숫자 추가', instruction: '숫자를 포함해서 바꿔줘' },
      ],
      image: [
        { label: '홈택스 스크린샷', instruction: '홈택스 스크린샷 추가해줘' },
        { label: '국세청 스크린샷', instruction: '국세청 스크린샷 추가해줘' },
        { label: '정부24 스크린샷', instruction: '정부24 스크린샷 추가해줘' },
      ],
      paragraph: common,
      list: [
        ...common,
        { label: '항목 추가', instruction: '관련 항목을 더 추가해줘' },
        { label: '표로 변환', instruction: '이 리스트를 표로 변환해줘' },
      ],
      table: [
        { label: '행 추가', instruction: '관련 행을 더 추가해줘' },
        { label: '스타일 개선', instruction: '표를 더 보기 좋게 개선해줘' },
      ],
      quote: [
        { label: '출처 추가', instruction: '인용 출처를 추가해줘' },
        { label: '강조', instruction: '더 인상적으로 바꿔줘' },
      ],
    };

    return typeSpecific[type] || common;
  };

  // 전체 글자수 계산
  const totalCharCount = sections.reduce((acc, s) => {
    const text = s.html.replace(/<[^>]+>/g, '');
    return acc + text.length;
  }, 0);

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-4">
      {/* 상단: 뒤로가기 + 발행 */}
      <div className="flex justify-between items-center">
        <button
          onClick={onBack}
          className="text-gray-600 hover:text-gray-900"
        >
          &larr; 키워드 선택으로
        </button>
        <button
          onClick={handlePublish}
          disabled={isPublishing || isLoading}
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {isPublishing ? '발행 중...' : '발행하기'}
        </button>
      </div>

      {/* 상단: 제목 + 메타정보 */}
      <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
        <h1 className="text-2xl font-bold text-gray-800">{article.title}</h1>
        <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-600">
          <span>키워드: <strong className="text-purple-600">{article.keyword}</strong></span>
          <span>글자수: <strong>{totalCharCount.toLocaleString()}자</strong></span>
          <span>카테고리: <strong>{article.category}</strong></span>
          <span>섹션수: <strong>{sections.length}개</strong></span>
          {article.has_coupang && <span className="text-orange-500 font-medium">쿠팡 포함</span>}
        </div>
      </div>

      {/* 전체 수정 입력 */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
        <h3 className="font-semibold mb-2 text-purple-700">전체 수정 요청</h3>
        <div className="flex flex-wrap gap-2 mb-3">
          {['전체적으로 더 친근하게', '표 추가해줘', '쿠팡 배너 추가해줘', 'SEO 최적화해줘'].map(preset => (
            <button
              key={preset}
              className="px-2 py-1 text-xs bg-white border border-purple-200 rounded hover:bg-purple-100 disabled:opacity-50"
              onClick={() => setGlobalInstruction(preset)}
              disabled={isLoading}
            >
              {preset}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 px-4 py-2 border border-purple-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400"
            placeholder="전체 글에 대한 수정 요청... 예: https://nts.go.kr 스크린샷 추가해줘"
            value={globalInstruction}
            onChange={(e) => setGlobalInstruction(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleGlobalEdit()}
            disabled={isLoading}
          />
          <button
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
            onClick={handleGlobalEdit}
            disabled={isLoading || !globalInstruction?.trim()}
          >
            {isLoading ? '처리중...' : '적용'}
          </button>
        </div>
      </div>

      {/* 섹션 목록 */}
      {sections.map((section, idx) => (
        <div
          key={section.id}
          className={`bg-white rounded-lg shadow overflow-hidden border-l-4 ${getSectionStyle(section.type)}`}
        >
          {/* 섹션 헤더 */}
          <div className="px-4 py-2 bg-gray-50 border-b flex justify-between items-center">
            <span className="text-sm text-gray-500">
              {getSectionLabel(section.type)} {idx + 1}
              <span className="text-xs text-gray-400 ml-2">
                ({section.html.replace(/<[^>]+>/g, '').length}자)
              </span>
            </span>
            <button
              className="text-xs px-2 py-1 text-red-500 hover:bg-red-50 rounded"
              onClick={() => handleDeleteSection(section.id)}
            >
              삭제
            </button>
          </div>

          {/* 섹션 콘텐츠 */}
          <div className={`p-4 ${loadingSections[section.id] ? 'opacity-50' : ''}`}>
            <div
              className="prose max-w-none"
              dangerouslySetInnerHTML={{ __html: section.html }}
            />
          </div>

          {/* 수정 입력창 */}
          <div className="px-4 py-3 bg-purple-50 border-t">
            {/* 퀵 버튼 */}
            <div className="flex flex-wrap gap-2 mb-2">
              {getQuickButtons(section.type).map((btn) => (
                <button
                  key={btn.label}
                  className="px-2 py-1 text-xs bg-white border border-purple-200 rounded hover:bg-purple-100 disabled:opacity-50"
                  onClick={() => setEditInputs(prev => ({
                    ...prev,
                    [section.id]: btn.instruction
                  }))}
                  disabled={loadingSections[section.id]}
                >
                  {btn.label}
                </button>
              ))}
            </div>

            {/* 입력창 */}
            <div className="flex gap-2">
              <input
                type="text"
                className="flex-1 px-3 py-2 border border-purple-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
                placeholder={`이 ${getSectionLabel(section.type)} 수정 요청... (예: 더 자세히 써줘, 홈택스 스크린샷 추가해줘)`}
                value={editInputs[section.id] || ''}
                onChange={(e) => setEditInputs(prev => ({
                  ...prev,
                  [section.id]: e.target.value
                }))}
                onKeyPress={(e) => e.key === 'Enter' && handleSectionEdit(section.id)}
                disabled={loadingSections[section.id]}
              />
              <button
                className="px-4 py-2 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 disabled:opacity-50"
                onClick={() => handleSectionEdit(section.id)}
                disabled={loadingSections[section.id] || !editInputs[section.id]?.trim()}
              >
                {loadingSections[section.id] ? '처리중...' : '적용'}
              </button>
            </div>
          </div>
        </div>
      ))}

      {/* 하단: 발행 버튼 */}
      <div className="flex justify-center gap-4 py-6">
        <button
          className="px-8 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          onClick={onBack}
        >
          취소
        </button>
        <button
          className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          onClick={handlePublish}
          disabled={isPublishing || isLoading || sections.length === 0}
        >
          {isPublishing ? '발행 중...' : 'WordPress에 발행하기'}
        </button>
      </div>

      {/* 로딩 오버레이 */}
      {(isLoading || isPublishing) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg text-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 mx-auto"></div>
            <p className="mt-3 text-gray-600">
              {isPublishing ? '발행 중...' : 'AI가 처리 중...'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
