'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

type SectionType = 'title' | 'image' | 'paragraph' | 'list' | 'table' | 'quote' | 'other';

interface Section {
  id: string;
  type: SectionType;
  tagName: string;
  content: string;
  text?: string;
  imageUrl?: string;
}

interface ArticleEditorProps {
  article: any;
  onUpdate: (article: any) => void;
  onBack: () => void;
  onPublish: () => void;
}

// 빠른 버튼 컴포넌트
const QuickButton = ({ label, onClick }: { label: string; onClick: () => void }) => (
  <button
    onClick={onClick}
    className="text-xs px-2 py-1 bg-white border rounded hover:bg-purple-50 transition-colors"
  >
    {label}
  </button>
);

export default function ArticleEditor({ article, onUpdate, onBack, onPublish }: ArticleEditorProps) {
  const [sections, setSections] = useState<Section[]>([]);
  const [sectionInstructions, setSectionInstructions] = useState<Record<string, string>>({});
  const [globalInstruction, setGlobalInstruction] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingSection, setLoadingSection] = useState<string | null>(null);
  const [charCount, setCharCount] = useState(0);
  const [screenshotUrl, setScreenshotUrl] = useState<Record<string, string>>({});
  const [pexelsQuery, setPexelsQuery] = useState<Record<string, string>>({});

  // HTML을 개별 섹션으로 분리
  useEffect(() => {
    if (article?.raw_content) {
      const parsed = parseContentToSections(article.raw_content);
      setSections(parsed);

      // 글자수 계산 (HTML 태그 제외)
      const textOnly = article.raw_content.replace(/<[^>]*>/g, '');
      setCharCount(textOnly.length);
    }
  }, [article?.raw_content]);

  // 모든 요소를 개별 섹션으로 분리하는 파싱 함수
  const parseContentToSections = (html: string): Section[] => {
    const sections: Section[] = [];
    let sectionIndex = 0;

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;

    const processElement = (element: Element) => {
      const tagName = element.tagName.toLowerCase();
      const outerHTML = element.outerHTML;
      const textContent = element.textContent?.trim() || '';

      // 제목 (h1, h2, h3)
      if (['h1', 'h2', 'h3'].includes(tagName)) {
        sections.push({
          id: `title-${sectionIndex++}`,
          type: 'title',
          tagName,
          content: outerHTML,
          text: textContent
        });
      }
      // 이미지 (figure, img)
      else if (tagName === 'figure' || tagName === 'img') {
        const imgEl = element.querySelector('img') || element;
        const imgSrc = (imgEl as HTMLImageElement).src || '';
        sections.push({
          id: `image-${sectionIndex++}`,
          type: 'image',
          tagName,
          content: outerHTML,
          imageUrl: imgSrc
        });
      }
      // 표 (table)
      else if (tagName === 'table') {
        sections.push({
          id: `table-${sectionIndex++}`,
          type: 'table',
          tagName,
          content: outerHTML
        });
      }
      // 리스트 (ul, ol)
      else if (['ul', 'ol'].includes(tagName)) {
        sections.push({
          id: `list-${sectionIndex++}`,
          type: 'list',
          tagName,
          content: outerHTML
        });
      }
      // 인용문 (blockquote)
      else if (tagName === 'blockquote') {
        sections.push({
          id: `quote-${sectionIndex++}`,
          type: 'quote',
          tagName,
          content: outerHTML,
          text: textContent
        });
      }
      // 일반 문단 (p, div with text)
      else if (['p', 'div'].includes(tagName) && textContent) {
        sections.push({
          id: `paragraph-${sectionIndex++}`,
          type: 'paragraph',
          tagName,
          content: outerHTML,
          text: textContent
        });
      }
      // 기타 요소
      else if (outerHTML.trim() && textContent) {
        sections.push({
          id: `other-${sectionIndex++}`,
          type: 'other',
          tagName,
          content: outerHTML,
          text: textContent
        });
      }
    };

    Array.from(tempDiv.children).forEach(processElement);

    return sections;
  };

  // 섹션 타입 라벨
  const getTypeLabel = (type: SectionType): string => {
    const labels: Record<SectionType, string> = {
      title: '제목',
      image: '이미지',
      paragraph: '문단',
      list: '리스트',
      table: '표',
      quote: '인용',
      other: '기타'
    };
    return labels[type];
  };

  // 섹션 타입별 border 색상
  const getBorderColor = (type: SectionType): string => {
    const colors: Record<SectionType, string> = {
      title: 'border-purple-400',
      image: 'border-blue-400',
      paragraph: 'border-gray-300',
      list: 'border-green-400',
      table: 'border-orange-400',
      quote: 'border-yellow-400',
      other: 'border-gray-200'
    };
    return colors[type];
  };

  // 섹션 수정 요청
  const handleSectionEdit = async (sectionId: string) => {
    const instruction = sectionInstructions[sectionId];
    if (!instruction) return;

    const section = sections.find(s => s.id === sectionId);
    if (!section) return;

    const sectionNumber = sections.findIndex(s => s.id === sectionId) + 1;

    setLoadingSection(sectionId);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/natural-edit`, {
        instruction: `${sectionNumber}번째 ${getTypeLabel(section.type)}: ${instruction}`,
        section_id: sectionId
      });

      if (res.data.success) {
        const articleRes = await axios.get(`${API_URL}/api/articles/${article.id}`);
        if (articleRes.data) {
          onUpdate(articleRes.data);
        }
        setSectionInstructions(prev => ({ ...prev, [sectionId]: '' }));
        alert(res.data.message || '수정 완료!');
      } else {
        alert(res.data.error || '수정 실패');
      }
    } catch (error: any) {
      console.error('Section edit error:', error);
      alert(error.response?.data?.detail || '수정 실패');
    } finally {
      setLoadingSection(null);
    }
  };

  // 이미지 스크린샷 교체
  const handleImageScreenshot = async (sectionId: string) => {
    const url = screenshotUrl[sectionId];
    if (!url) {
      alert('URL을 입력하세요');
      return;
    }

    setLoadingSection(sectionId);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/natural-edit`, {
        instruction: `${url} 스크린샷으로 변경해줘`
      });

      if (res.data.success) {
        const articleRes = await axios.get(`${API_URL}/api/articles/${article.id}`);
        if (articleRes.data) {
          onUpdate(articleRes.data);
        }
        setScreenshotUrl(prev => ({ ...prev, [sectionId]: '' }));
        alert('이미지가 교체되었습니다.');
      } else {
        alert(res.data.error || '이미지 교체 실패');
      }
    } catch (error: any) {
      console.error('Image screenshot error:', error);
      alert(error.response?.data?.detail || '이미지 교체 실패');
    } finally {
      setLoadingSection(null);
    }
  };

  // 이미지 Pexels 검색 교체
  const handleImagePexels = async (sectionId: string) => {
    const query = pexelsQuery[sectionId];
    if (!query) {
      alert('검색어를 입력하세요');
      return;
    }

    setLoadingSection(sectionId);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/natural-edit`, {
        instruction: `${query} 관련 이미지로 바꿔줘`
      });

      if (res.data.success) {
        const articleRes = await axios.get(`${API_URL}/api/articles/${article.id}`);
        if (articleRes.data) {
          onUpdate(articleRes.data);
        }
        setPexelsQuery(prev => ({ ...prev, [sectionId]: '' }));
        alert('이미지가 교체되었습니다.');
      } else {
        alert(res.data.error || '이미지 교체 실패');
      }
    } catch (error: any) {
      console.error('Image pexels error:', error);
      alert(error.response?.data?.detail || '이미지 교체 실패');
    } finally {
      setLoadingSection(null);
    }
  };

  // 이미지 삭제
  const handleImageDelete = async (sectionId: string) => {
    if (!confirm('이미지를 삭제하시겠습니까?')) return;

    const imageIndex = sections.filter(s => s.type === 'image').findIndex(s => s.id === sectionId) + 1;

    setLoadingSection(sectionId);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/natural-edit`, {
        instruction: `${imageIndex}번째 이미지 삭제해줘`
      });

      if (res.data.success) {
        const articleRes = await axios.get(`${API_URL}/api/articles/${article.id}`);
        if (articleRes.data) {
          onUpdate(articleRes.data);
        }
        alert('이미지가 삭제되었습니다.');
      }
    } catch (error: any) {
      console.error('Image delete error:', error);
      alert(error.response?.data?.detail || '이미지 삭제 실패');
    } finally {
      setLoadingSection(null);
    }
  };

  // 전체 수정 요청
  const handleGlobalEdit = async () => {
    if (!globalInstruction) return;

    setIsLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/natural-edit`, {
        instruction: globalInstruction
      });

      if (res.data.success) {
        const articleRes = await axios.get(`${API_URL}/api/articles/${article.id}`);
        if (articleRes.data) {
          onUpdate(articleRes.data);
        }
        setGlobalInstruction('');
        alert(`[${res.data.action_type}] ${res.data.message || '수정 완료!'}`);
      } else {
        alert(res.data.error || '수정 실패');
      }
    } catch (error: any) {
      console.error('Global edit error:', error);
      alert(error.response?.data?.detail || '전체 수정 실패');
    } finally {
      setIsLoading(false);
    }
  };

  // 발행
  const handlePublish = async () => {
    if (!confirm('WordPress에 발행하시겠습니까?')) return;

    setIsLoading(true);
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
      alert(`발행 실패:\n${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // instruction 설정 헬퍼
  const setInstruction = (sectionId: string, value: string) => {
    setSectionInstructions(prev => ({ ...prev, [sectionId]: value }));
  };

  // 이미지 카운터
  let imageCounter = 0;

  return (
    <div className="max-w-4xl mx-auto space-y-4">
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
          disabled={isLoading}
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          발행하기
        </button>
      </div>

      {/* 제목 + 메타정보 */}
      <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">{article.title}</h1>
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          <span>키워드: <strong className="text-purple-600">{article.keyword}</strong></span>
          <span>글자수: <strong>{charCount.toLocaleString()}자</strong></span>
          <span>카테고리: <strong>{article.category || '트렌드'}</strong></span>
          <span>섹션수: <strong>{sections.length}개</strong></span>
          {article.has_coupang && <span className="text-orange-500 font-medium">쿠팡 포함</span>}
        </div>
      </div>

      {/* 전체 수정 입력 (상단) */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
        <h3 className="font-semibold mb-2 text-purple-700">전체 수정 요청</h3>
        <div className="flex flex-wrap gap-2 mb-3">
          {['전체적으로 더 친근하게', '표 추가해줘', '쿠팡 배너 추가해줘', 'SEO 최적화해줘'].map(preset => (
            <QuickButton key={preset} label={preset} onClick={() => setGlobalInstruction(preset)} />
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={globalInstruction}
            onChange={(e) => setGlobalInstruction(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleGlobalEdit()}
            placeholder="전체 글에 대한 수정 요청... 예: https://nts.go.kr 스크린샷 추가해줘"
            className="flex-1 border rounded-lg px-4 py-2"
          />
          <button
            onClick={handleGlobalEdit}
            disabled={isLoading || !globalInstruction}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {isLoading ? '처리중...' : '적용'}
          </button>
        </div>
      </div>

      {/* 개별 섹션 카드 */}
      {sections.map((section, index) => {
        if (section.type === 'image') imageCounter++;
        const currentImageNumber = imageCounter;

        return (
          <div key={section.id} className="mb-4">
            <div
              className={`bg-white rounded-lg shadow p-4 border-l-4 ${getBorderColor(section.type)}
                hover:shadow-md transition-shadow ${loadingSection === section.id ? 'opacity-50' : ''}`}
            >
              {/* 섹션 타입 라벨 */}
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                  {getTypeLabel(section.type)} {index + 1}
                  <span className="ml-2 text-gray-300">&lt;{section.tagName}&gt;</span>
                </span>

                {/* 이미지인 경우 교체/삭제 버튼 */}
                {section.type === 'image' && (
                  <button
                    className="text-xs px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                    onClick={() => handleImageDelete(section.id)}
                    disabled={loadingSection === section.id}
                  >
                    삭제
                  </button>
                )}
              </div>

              {/* 실제 콘텐츠 */}
              <div
                className="prose max-w-none text-gray-700 mb-4"
                dangerouslySetInnerHTML={{ __html: section.content }}
              />

              {/* 수정 입력창 - 섹션 타입별로 다르게 */}
              <div className="mt-3 p-3 bg-purple-50 rounded-lg">
                {/* 빠른 버튼 */}
                <div className="flex flex-wrap gap-2 mb-2">
                  {section.type === 'paragraph' && (
                    <>
                      <QuickButton label="더 자세히" onClick={() => setInstruction(section.id, '더 자세히 설명해줘')} />
                      <QuickButton label="짧게" onClick={() => setInstruction(section.id, '더 짧게 요약해줘')} />
                      <QuickButton label="친근하게" onClick={() => setInstruction(section.id, '더 친근하게 써줘')} />
                      <QuickButton label="전문적으로" onClick={() => setInstruction(section.id, '더 전문적으로 써줘')} />
                      <QuickButton label="예시 추가" onClick={() => setInstruction(section.id, '구체적인 예시를 추가해줘')} />
                    </>
                  )}
                  {section.type === 'title' && (
                    <>
                      <QuickButton label="더 매력적으로" onClick={() => setInstruction(section.id, '제목을 더 클릭하고 싶게 바꿔줘')} />
                      <QuickButton label="키워드 강조" onClick={() => setInstruction(section.id, '키워드를 앞에 배치해줘')} />
                      <QuickButton label="숫자 추가" onClick={() => setInstruction(section.id, '숫자를 포함해서 바꿔줘')} />
                    </>
                  )}
                  {section.type === 'list' && (
                    <>
                      <QuickButton label="항목 추가" onClick={() => setInstruction(section.id, '항목을 더 추가해줘')} />
                      <QuickButton label="표로 변환" onClick={() => setInstruction(section.id, '이 리스트를 표로 변환해줘')} />
                      <QuickButton label="순서 정리" onClick={() => setInstruction(section.id, '중요한 순서대로 정렬해줘')} />
                    </>
                  )}
                  {section.type === 'table' && (
                    <>
                      <QuickButton label="행 추가" onClick={() => setInstruction(section.id, '행을 추가해줘')} />
                      <QuickButton label="열 추가" onClick={() => setInstruction(section.id, '열을 추가해줘')} />
                      <QuickButton label="스타일 개선" onClick={() => setInstruction(section.id, '표 스타일을 더 보기 좋게 해줘')} />
                    </>
                  )}
                  {section.type === 'quote' && (
                    <>
                      <QuickButton label="출처 추가" onClick={() => setInstruction(section.id, '인용 출처를 추가해줘')} />
                      <QuickButton label="강조" onClick={() => setInstruction(section.id, '더 인상적으로 바꿔줘')} />
                    </>
                  )}
                </div>

                {/* 이미지용 특수 입력 */}
                {section.type === 'image' && (
                  <div className="space-y-2 mb-3">
                    {/* Pexels 검색 */}
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Pexels 이미지 검색어..."
                        className="flex-1 px-3 py-2 border rounded-lg text-sm"
                        value={pexelsQuery[section.id] || ''}
                        onChange={(e) => setPexelsQuery(prev => ({ ...prev, [section.id]: e.target.value }))}
                        onKeyPress={(e) => e.key === 'Enter' && handleImagePexels(section.id)}
                      />
                      <button
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
                        onClick={() => handleImagePexels(section.id)}
                        disabled={loadingSection === section.id || !pexelsQuery[section.id]}
                      >
                        Pexels 교체
                      </button>
                    </div>
                    {/* URL 스크린샷 */}
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="스크린샷 URL (https://...)..."
                        className="flex-1 px-3 py-2 border rounded-lg text-sm"
                        value={screenshotUrl[section.id] || ''}
                        onChange={(e) => setScreenshotUrl(prev => ({ ...prev, [section.id]: e.target.value }))}
                        onKeyPress={(e) => e.key === 'Enter' && handleImageScreenshot(section.id)}
                      />
                      <button
                        className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50"
                        onClick={() => handleImageScreenshot(section.id)}
                        disabled={loadingSection === section.id || !screenshotUrl[section.id]}
                      >
                        스크린샷 캡처
                      </button>
                    </div>
                  </div>
                )}

                {/* 일반 수정 입력창 (이미지가 아닌 경우만) */}
                {section.type !== 'image' && (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder={`이 ${getTypeLabel(section.type)} 수정 요청...`}
                      className="flex-1 px-3 py-2 border rounded-lg text-sm"
                      value={sectionInstructions[section.id] || ''}
                      onChange={(e) => setSectionInstructions(prev => ({
                        ...prev,
                        [section.id]: e.target.value
                      }))}
                      onKeyPress={(e) => e.key === 'Enter' && handleSectionEdit(section.id)}
                    />
                    <button
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 disabled:opacity-50"
                      onClick={() => handleSectionEdit(section.id)}
                      disabled={loadingSection === section.id || !sectionInstructions[section.id]}
                    >
                      {loadingSection === section.id ? '수정중...' : '적용'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}

      {/* 전체 수정 입력 (하단) */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200">
        <h3 className="font-semibold mb-2 text-blue-700">전체 수정 요청 (하단)</h3>
        <div className="flex flex-wrap gap-2 mb-3">
          {['글 마무리 추가', '전체 길이 늘리기', '전체 길이 줄이기', 'CTA 추가'].map(preset => (
            <QuickButton key={preset} label={preset} onClick={() => setGlobalInstruction(preset)} />
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={globalInstruction}
            onChange={(e) => setGlobalInstruction(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleGlobalEdit()}
            placeholder="전체 글에 대한 수정 요청..."
            className="flex-1 border rounded-lg px-4 py-2"
          />
          <button
            onClick={handleGlobalEdit}
            disabled={isLoading || !globalInstruction}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? '처리중...' : '적용'}
          </button>
        </div>
      </div>

      {/* 하단 발행 버튼 */}
      <div className="flex justify-center gap-4 py-6">
        <button
          onClick={onBack}
          className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
        >
          취소
        </button>
        <button
          onClick={handlePublish}
          disabled={isLoading}
          className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
        >
          {isLoading ? '처리중...' : 'WordPress에 발행하기'}
        </button>
      </div>

      {/* 로딩 오버레이 */}
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg text-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 mx-auto"></div>
            <p className="mt-3 text-gray-600">AI가 처리 중...</p>
          </div>
        </div>
      )}
    </div>
  );
}
