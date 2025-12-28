'use client';

import ImageManager from './ImageManager';

interface SectionEditorProps {
  section: any;
  isSelected: boolean;
  onSelect: () => void;
  articleId: string;
  onUpdate: (section: any) => void;
}

export default function SectionEditor({ section, isSelected, onSelect, articleId, onUpdate }: SectionEditorProps) {
  return (
    <div
      onClick={onSelect}
      className={`bg-white rounded-lg shadow p-6 cursor-pointer transition ${
        isSelected ? 'ring-2 ring-blue-500' : 'hover:shadow-md'
      }`}
    >
      <h3 className="font-semibold text-lg mb-2">{section.title}</h3>

      {/* 콘텐츠 미리보기 */}
      <div
        className="prose prose-sm max-w-none text-gray-600"
        dangerouslySetInnerHTML={{ __html: section.content?.substring(0, 500) + '...' }}
      />

      {/* 이미지 관리 */}
      {section.images && section.images.length > 0 && (
        <div className="mt-4 border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">이미지</h4>
          <div className="space-y-2">
            {section.images.map((img: any) => (
              <ImageManager
                key={img.id}
                image={img}
                articleId={articleId}
                onUpdate={(updatedImage) => {
                  const updatedImages = section.images.map((i: any) =>
                    i.id === updatedImage.id ? updatedImage : i
                  );
                  onUpdate({ ...section, images: updatedImages });
                }}
              />
            ))}
          </div>
        </div>
      )}

      {isSelected && (
        <div className="mt-4 flex gap-2">
          <span className="text-sm text-blue-600">선택됨 - 아래에서 수정 요청을 입력하세요</span>
        </div>
      )}
    </div>
  );
}
