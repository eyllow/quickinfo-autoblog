/**
 * 중앙 집중식 API URL 설정
 * Mixed Content 에러 방지를 위해 매 요청마다 동적으로 URL 결정
 */

/**
 * API URL을 동적으로 반환 (매 호출마다 평가)
 * - 브라우저: 현재 페이지의 origin 사용 (HTTPS 보장)
 * - 서버: 환경변수 또는 폴백 사용
 */
export const getApiUrl = (): string => {
  // 브라우저 환경에서는 현재 페이지의 origin 사용
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }

  // 서버사이드: 환경변수 사용 (HTTPS 강제)
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl) {
    // http:// -> https:// 변환 (프로덕션 도메인)
    if (envUrl.includes('quickinfo.kr')) {
      return envUrl.replace(/^http:\/\//i, 'https://');
    }
    return envUrl;
  }

  return 'https://admin.quickinfo.kr';
};

// 하위 호환성을 위한 API_URL 상수 (getter로 동작)
// 주의: 서버사이드에서는 환경변수 값 사용, 클라이언트에서는 window.location.origin 사용
export const API_URL = typeof window !== 'undefined'
  ? window.location.origin
  : (process.env.NEXT_PUBLIC_API_URL?.replace(/^http:\/\//i, 'https://') || 'https://admin.quickinfo.kr');

export default API_URL;
