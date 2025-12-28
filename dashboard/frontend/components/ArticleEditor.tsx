'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

interface Section {
  id: string;
  type: 'text' | 'image';
  title?: string;
  content: string;
  imageUrl?: string;
}

interface ArticleEditorProps {
  article: any;
  onUpdate: (article: any) => void;
  onBack: () => void;
  onPublish: () => void;
}

export default function ArticleEditor({ article, onUpdate, onBack, onPublish }: ArticleEditorProps) {
  const [sections, setSections] = useState<Section[]>([]);
  const [sectionInstructions, setSectionInstructions] = useState<Record<string, string>>({});
  const [globalInstruction, setGlobalInstruction] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingSection, setLoadingSection] = useState<string | null>(null);
  const [charCount, setCharCount] = useState(0);

  // HTML을 섹션으로 분리
  useEffect(() => {
    if (article?.raw_content) {
      const parsed = parseContentToSections(article.raw_content);
      setSections(parsed);

      // 글자수 계산 (HTML 태그 제외)
      const textOnly = article.raw_content.replace(/<[^>]*>/g, '');
      setCharCount(textOnly.length);
    }
  }, [article?.raw_content]);

  // 섹션 파싱 함수 (클라이언트 사이드)
  const parseContentToSections = (html: string): Section[] => {
    const sections: Section[] = [];
    let sectionIndex = 0;

    // 임시 div에 HTML 파싱
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;

    let currentSection: Section | null = null;

    Array.from(tempDiv.children).forEach((element) => {
      const tagName = element.tagName.toLowerCase();

      // H2는 새 섹션 시작
      if (tagName === 'h2') {
        if (currentSection) {
          sections.push(currentSection);
        }
        currentSection = {
          id: `section-${sectionIndex++}`,
          type: 'text',
          title: element.textContent || '',
          content: element.outerHTML
        };
      }
      // figure/img는 별도 이미지 섹션
      else if (tagName === 'figure' || tagName === 'img') {
        if (currentSection) {
          sections.push(currentSection);
          currentSection = null;
        }
        const imgEl = element.querySelector('img') || element;
        const imgSrc = (imgEl as HTMLImageElement).src || '';
        sections.push({
          id: `image-${sectionIndex++}`,
          type: 'image',
          content: element.outerHTML,
          imageUrl: imgSrc
        });
      }
      // 그 외는 현재 섹션에 추가
      else {
        if (!currentSection) {
          currentSection = {
            id: `section-${sectionIndex++}`,
            type: 'text',
            content: ''
          };
        }
        currentSection.content += element.outerHTML;
      }
    });

    if (currentSection) {
      sections.push(currentSection);
    }

    return sections;
  };

  // 섹션 수정 요청
  const handleSectionEdit = async (sectionId: string) => {
    const instruction = sectionInstructions[sectionId];
    if (!instruction) return;

    const section = sections.find(s => s.id === sectionId);
    if (!section) return;

    setLoadingSection(sectionId);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/natural-edit`, {
        instruction: `${section.title ? `"${section.title}" 섹션: ` : ''}${instruction}`,
        section_id: sectionId
      });

      if (res.data.success) {
        // 전체 글 다시 가져오기
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

  // 이미지 교체 (URL 스크린샷)
  const handleImageReplace = async (sectionId: string) => {
    const url = prompt('스크린샷을 캡처할 URL을 입력하세요:');
    if (!url) return;

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
        alert('이미지가 교체되었습니다.');
      } else {
        alert(res.data.error || '이미지 교체 실패');
      }
    } catch (error: any) {
      console.error('Image replace error:', error);
      alert(error.response?.data?.detail || '이미지 교체 실패');
    } finally {
      setLoadingSection(null);
    }
  };

  // 이미지 Pexels 검색 교체
  const handleImagePexels = async (sectionId: string) => {
    const query = prompt('검색할 이미지 키워드를 입력하세요:');
    if (!query) return;

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
  const handleImageDelete = async (sectionId: string, index: number) => {
    if (!confirm('이미지를 삭제하시겠습니까?')) return;

    setLoadingSection(sectionId);
    try {
      const res = await axios.post(`${API_URL}/api/articles/${article.id}/natural-edit`, {
        instruction: `${index + 1}번째 이미지 삭제해줘`
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

  // 이미지 인덱스 계산
  let imageIndex = 0;

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
              onClick={() => setGlobalInstruction(preset)}
              className="text-xs px-2 py-1 bg-white border rounded hover:bg-gray-50"
            >
              {preset}
            </button>
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

      {/* 섹션별 카드 */}
      {sections.map((section, index) => {
        const currentImageIndex = section.type === 'image' ? ++imageIndex : 0;

        return (
          <div
            key={section.id}
            className={`bg-white rounded-lg shadow overflow-hidden ${loadingSection === section.id ? 'opacity-50' : ''}`}
          >
            {section.type === 'image' ? (
              /* 이미지 섹션 */
              <div className="p-4">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-sm font-medium text-gray-500">
                    이미지 {currentImageIndex}
                  </span>
                  <div className="flex gap-2">
                    <button
                      className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                      onClick={() => handleImagePexels(section.id)}
                      disabled={loadingSection === section.id}
                    >
                      Pexels 검색
                    </button>
                    <button
                      className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
                      onClick={() => handleImageReplace(section.id)}
                      disabled={loadingSection === section.id}
                    >
                      URL 스크린샷
                    </button>
                    <button
                      className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                      onClick={() => handleImageDelete(section.id, currentImageIndex - 1)}
                      disabled={loadingSection === section.id}
                    >
                      삭제
                    </button>
                  </div>
                </div>
                <div
                  className="prose max-w-none"
                  dangerouslySetInnerHTML={{ __html: section.content }}
                />
              </div>
            ) : (
              /* 텍스트 섹션 */
              <div className="p-4">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-sm font-medium text-purple-600">
                    {section.title || `섹션 ${index + 1}`}
                  </span>
                </div>
                <div
                  className="prose max-w-none text-gray-700 mb-4"
                  dangerouslySetInnerHTML={{ __html: section.content }}
                />

                {/* 섹션 수정 입력창 */}
                <div className="p-3 bg-gray-50 rounded-lg border">
                  <div className="flex flex-wrap gap-2 mb-2">
                    {['더 자세히', '짧게 요약', '표로 정리', '친근하게', '예시 추가'].map(preset => (
                      <button
                        key={preset}
                        onClick={() => setSectionInstructions(prev => ({
                          ...prev,
                          [section.id]: preset + ' 해줘'
                        }))}
                        className="text-xs px-2 py-1 bg-white border rounded hover:bg-purple-50"
                      >
                        {preset}
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="이 섹션 수정 요청..."
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
                </div>
              </div>
            )}
          </div>
        );
      })}

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
