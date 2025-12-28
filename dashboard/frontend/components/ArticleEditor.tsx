'use client';

import { useState } from 'react';
import { FileText, Edit3, RotateCcw, ChevronDown, ChevronUp, Maximize2, Minimize2 } from 'lucide-react';
import type { Article } from '@/app/page';

interface ArticleEditorProps {
  article: Article | null;
  onUpdate: (article: Article) => void;
  mode: 'semi' | 'auto';
}

export default function ArticleEditor({ article, onUpdate, mode }: ArticleEditorProps) {
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  if (!article) {
    return (
      <div className="card h-full flex flex-col items-center justify-center p-8 text-center">
        <FileText className="w-16 h-16 text-muted-foreground mb-4" />
        <h3 className="text-xl font-bold text-white mb-2">글을 생성해주세요</h3>
        <p className="text-muted-foreground">
          왼쪽에서 키워드를 선택하고
          <br />
          &apos;글 생성하기&apos; 버튼을 클릭하세요
        </p>
      </div>
    );
  }

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const startEdit = (sectionId: string, content: string) => {
    setEditingSection(sectionId);
    setEditContent(content);
  };

  const saveEdit = async (sectionId: string) => {
    try {
      await fetch(`http://localhost:8003/api/articles/${article.id}/edit-section`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ section_id: sectionId, new_content: editContent }),
      });

      const updatedSections = article.sections.map((s) =>
        s.id === sectionId ? { ...s, content: editContent } : s
      );
      onUpdate({ ...article, sections: updatedSections });
    } catch (error) {
      console.error('Save failed:', error);
    }
    setEditingSection(null);
  };

  const regenerateSection = async (sectionId: string) => {
    try {
      const res = await fetch(
        `http://localhost:8003/api/articles/${article.id}/regenerate-section?section_id=${sectionId}`,
        { method: 'POST' }
      );
      const data = await res.json();

      if (data.success) {
        const updatedSections = article.sections.map((s) =>
          s.id === sectionId ? { ...s, content: data.new_content } : s
        );
        onUpdate({ ...article, sections: updatedSections });
      }
    } catch (error) {
      console.error('Regenerate failed:', error);
    }
  };

  return (
    <div className="card h-full flex flex-col">
      {/* 헤더 */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-2">
          <span className="px-2 py-1 rounded bg-primary/20 text-primary text-xs font-medium">
            {article.keyword}
          </span>
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${
              article.status === 'published'
                ? 'bg-accent/20 text-accent'
                : 'bg-yellow-500/20 text-yellow-400'
            }`}
          >
            {article.status === 'published' ? '발행됨' : '초안'}
          </span>
        </div>
        <h2 className="text-xl font-bold text-white">{article.title}</h2>
      </div>

      {/* 섹션 목록 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {article.sections.map((section) => {
          const isExpanded = expandedSections.has(section.id);
          const isEditing = editingSection === section.id;

          return (
            <div
              key={section.id}
              className="border border-border rounded-lg overflow-hidden"
            >
              {/* 섹션 헤더 */}
              <div
                className="flex items-center justify-between p-3 bg-secondary/50 cursor-pointer"
                onClick={() => toggleSection(section.id)}
              >
                <div className="flex items-center gap-2">
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  )}
                  <h3 className="font-medium text-white">{section.title}</h3>
                </div>

                {mode === 'semi' && (
                  <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => startEdit(section.id, section.content)}
                      className="p-1.5 rounded hover:bg-primary/20 text-muted-foreground hover:text-primary transition-colors"
                    >
                      <Edit3 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => regenerateSection(section.id)}
                      className="p-1.5 rounded hover:bg-accent/20 text-muted-foreground hover:text-accent transition-colors"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>

              {/* 섹션 내용 */}
              {isExpanded && (
                <div className="p-4 bg-background/50">
                  {isEditing ? (
                    <div className="space-y-3">
                      <textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        className="input w-full h-40 resize-none"
                      />
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => setEditingSection(null)}
                          className="btn-secondary text-sm"
                        >
                          취소
                        </button>
                        <button
                          onClick={() => saveEdit(section.id)}
                          className="btn-primary text-sm"
                        >
                          저장
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div
                      className="prose prose-invert prose-sm max-w-none"
                      dangerouslySetInnerHTML={{ __html: section.content }}
                    />
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 하단 액션 */}
      <div className="p-4 border-t border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="btn-secondary text-sm flex items-center gap-2">
            <Minimize2 className="w-4 h-4" />
            짧게
          </button>
          <button className="btn-secondary text-sm flex items-center gap-2">
            <Maximize2 className="w-4 h-4" />
            길게
          </button>
        </div>
        <div className="text-sm text-muted-foreground">
          섹션 {article.sections.length}개
        </div>
      </div>
    </div>
  );
}
