'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import SectionEditor from './SectionEditor';
import { getApiUrl } from '@/lib/api';

interface Section {
  id: string;
  index: number;
  type: string;
  content: string;
  html?: string;
  image_url?: string;
}

interface Article {
  id: string;
  title: string;
  keyword: string;
  category: string;
  raw_content?: string;
  sections?: Section[];
  sections_v2?: Section[];
  has_coupang?: boolean;
  char_count?: number;
}

interface ArticleEditorProps {
  article: Article;
  onUpdate?: (article: Article) => void;
  onBack: () => void;
  onPublish?: () => void;
}

export default function ArticleEditor({ article: initialArticle, onUpdate, onBack, onPublish }: ArticleEditorProps) {
  const [article, setArticle] = useState<Article>(initialArticle);
  const [sections, setSections] = useState<Section[]>([]);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isSavingDraft, setIsSavingDraft] = useState(false);

  // 초기 섹션 설정
  useEffect(() => {
    // sections_v2가 있으면 사용, 없으면 sections, 없으면 raw_content에서 파싱
    if (initialArticle.sections_v2 && initialArticle.sections_v2.length > 0) {
      // content 필드 정규화
      setSections(initialArticle.sections_v2.map(s => ({
        ...s,
        content: s.content || s.html || '',
        html: s.html || s.content || ''
      })));
    } else if (initialArticle.sections && initialArticle.sections.length > 0) {
      setSections(initialArticle.sections.map(s => ({
        ...s,
        content: s.content || s.html || '',
        html: s.html || s.content || ''
      })));
    } else if (initialArticle.raw_content) {
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

      if (!outerHTML.trim()) return;
      if (!textContent && !['figure', 'img'].includes(tagName) && !outerHTML.includes('<img')) return;

      const type = getElementType(tagName, outerHTML);
      result.push({
        id: `section-${Math.random().toString(36).substr(2, 8)}`,
        index: index++,
        type,
        content: outerHTML,
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

  // 섹션 업데이트
  const handleUpdateSection = (index: number, updatedSection: Section) => {
    setSections(prev => prev.map((s, i) => i === index ? { ...updatedSection, index: i } : s));
  };

  // 섹션 삭제
  const handleDeleteSection = (index: number) => {
    if (!confirm('이 섹션을 삭제하시겠습니까?')) return;
    setSections(prev => prev.filter((_, i) => i !== index).map((s, i) => ({ ...s, index: i })));
  };

  // 섹션 위로 이동
  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    setSections(prev => {
      const newSections = [...prev];
      [newSections[index - 1], newSections[index]] = [newSections[index], newSections[index - 1]];
      return newSections.map((s, i) => ({ ...s, index: i }));
    });
  };

  // 섹션 아래로 이동
  const handleMoveDown = (index: number) => {
    if (index === sections.length - 1) return;
    setSections(prev => {
      const newSections = [...prev];
      [newSections[index], newSections[index + 1]] = [newSections[index + 1], newSections[index]];
      return newSections.map((s, i) => ({ ...s, index: i }));
    });
  };

  // 새 섹션 추가
  const handleAddSection = (type: string) => {
    const defaultContent: Record<string, string> = {
      heading: '<h2>새 소제목</h2>',
      paragraph: '<p>새 문단 내용을 입력하세요.</p>',
      list: '<ul><li>항목 1</li><li>항목 2</li></ul>',
      image: '<figure><img src="" alt="이미지" /><figcaption>이미지 설명</figcaption></figure>',
      table: '<table><thead><tr><th>항목</th><th>내용</th></tr></thead><tbody><tr><td>-</td><td>-</td></tr></tbody></table>',
    };

    const newSection: Section = {
      id: `section-${Date.now()}`,
      index: sections.length,
      type: type,
      content: defaultContent[type] || '<p>새 섹션</p>',
      html: defaultContent[type] || '<p>새 섹션</p>'
    };
    setSections(prev => [...prev, newSection]);
  };

  // WordPress에 발행
  const handlePublish = async () => {
    if (!confirm('WordPress에 발행하시겠습니까?')) return;

    setIsPublishing(true);

    try {
      // 모든 섹션의 HTML 합치기
      const fullContent = sections.map(s => s.content || s.html || '').join('\n');

      // content 업데이트 시도
      try {
        await axios.put(`${getApiUrl()}/api/articles/${article.id}/content`, {
          content: fullContent
        });
      } catch (e) {
        // content 업데이트 API가 없으면 무시
      }

      // WordPress 발행
      const response = await axios.post(`${getApiUrl()}/api/publish/`, {
        article_id: article.id,
        status: 'publish'
      });

      if (response.data.success) {
        // 발행 성공 이벤트 발송 (PublishStats 새로고침용)
        window.dispatchEvent(new CustomEvent('post-published', { detail: { success: true } }));

        alert(`발행 완료!\n\nURL: ${response.data.url || '확인 필요'}\nPost ID: ${response.data.post_id || '-'}`);
        if (onPublish) onPublish();
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

  // WordPress Draft로 저장
  const handleSaveDraft = async () => {
    setIsSavingDraft(true);

    try {
      const fullContent = sections.map(s => s.content || s.html || '').join('\n');

      // content 업데이트 시도
      try {
        await axios.put(`${getApiUrl()}/api/articles/${article.id}/content`, {
          content: fullContent
        });
      } catch (e) {
        // 무시
      }

      // Draft로 발행
      const response = await axios.post(`${getApiUrl()}/api/publish/`, {
        article_id: article.id,
        status: 'draft'
      });

      if (response.data.success) {
        const postId = response.data.post_id;
        const editUrl = `https://quickinfo.kr/wp-admin/post.php?post=${postId}&action=edit`;

        const openWP = confirm(`임시저장 완료!\n\nPost ID: ${postId}\n\nWordPress 에디터에서 편집하시겠습니까?`);
        if (openWP) {
          window.open(editUrl, '_blank');
        }
      } else {
        alert(`임시저장 실패: ${response.data.error}`);
      }
    } catch (error: any) {
      console.error('임시저장 오류:', error);
      alert(`임시저장 실패:\n${error.response?.data?.detail || error.message}`);
    } finally {
      setIsSavingDraft(false);
    }
  };

  // 전체 글자수 계산
  const totalCharCount = sections.reduce((acc, s) => {
    const text = (s.content || s.html || '').replace(/<[^>]+>/g, '');
    return acc + text.length;
  }, 0);

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-4">
      {/* 상단 헤더 */}
      <div className="flex justify-between items-center">
        <button
          className="text-gray-600 hover:text-gray-900 flex items-center gap-1"
          onClick={onBack}
        >
          &larr; 키워드 선택으로
        </button>
        <button
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          onClick={handlePublish}
          disabled={isPublishing || isSavingDraft}
        >
          {isPublishing ? '발행 중...' : '발행하기'}
        </button>
      </div>

      {/* 글 정보 */}
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

      {/* 섹션 목록 */}
      <div className="space-y-4">
        {sections.map((section, index) => (
          <SectionEditor
            key={section.id}
            section={section}
            keyword={article.keyword}
            onUpdate={(updated) => handleUpdateSection(index, updated)}
            onDelete={() => handleDeleteSection(index)}
            onMoveUp={() => handleMoveUp(index)}
            onMoveDown={() => handleMoveDown(index)}
            isFirst={index === 0}
            isLast={index === sections.length - 1}
          />
        ))}
      </div>

      {/* 섹션 추가 버튼 */}
      <div className="bg-white rounded-lg shadow p-4">
        <p className="text-sm text-gray-500 mb-2">섹션 추가:</p>
        <div className="flex flex-wrap gap-2">
          <button
            className="px-3 py-2 bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
            onClick={() => handleAddSection('heading')}
          >
            + 소제목
          </button>
          <button
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            onClick={() => handleAddSection('paragraph')}
          >
            + 문단
          </button>
          <button
            className="px-3 py-2 bg-green-100 text-green-700 rounded hover:bg-green-200"
            onClick={() => handleAddSection('list')}
          >
            + 리스트
          </button>
          <button
            className="px-3 py-2 bg-orange-100 text-orange-700 rounded hover:bg-orange-200"
            onClick={() => handleAddSection('table')}
          >
            + 표
          </button>
          <button
            className="px-3 py-2 bg-pink-100 text-pink-700 rounded hover:bg-pink-200"
            onClick={() => handleAddSection('image')}
          >
            + 이미지
          </button>
        </div>
      </div>

      {/* 하단 버튼 */}
      <div className="flex justify-center gap-4 py-6">
        <button
          className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          onClick={onBack}
        >
          취소
        </button>
        <button
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          onClick={handleSaveDraft}
          disabled={isSavingDraft || isPublishing || sections.length === 0}
        >
          {isSavingDraft ? '저장 중...' : 'WordPress에서 편집'}
        </button>
        <button
          className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          onClick={handlePublish}
          disabled={isPublishing || isSavingDraft || sections.length === 0}
        >
          {isPublishing ? '발행 중...' : '발행하기'}
        </button>
      </div>

      {/* 로딩 오버레이 */}
      {(isPublishing || isSavingDraft) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg text-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 mx-auto"></div>
            <p className="mt-3 text-gray-600">
              {isPublishing ? '발행 중...' : '임시저장 중...'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
