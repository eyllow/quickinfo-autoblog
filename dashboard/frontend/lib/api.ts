/**
 * 중앙 집중식 API URL 설정
 * Mixed Content 에러 방지를 위해 프로토콜을 명시적으로 처리
 */

const ensureHttps = (url: string): string => {
  // 프로덕션 도메인에서는 항상 HTTPS 강제
  if (url.includes('admin.quickinfo.kr') || url.includes('quickinfo.kr')) {
    return url.replace(/^http:\/\//i, 'https://');
  }
  return url;
};

const getApiUrl = (): string => {
  // 1. 브라우저 환경에서는 현재 origin 사용 (가장 안전)
  if (typeof window !== 'undefined') {
    // 현재 페이지가 HTTPS면 API도 HTTPS로
    return window.location.origin;
  }

  // 2. 환경변수 (서버사이드 렌더링용)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return ensureHttps(process.env.NEXT_PUBLIC_API_URL);
  }

  // 3. 폴백
  return 'https://admin.quickinfo.kr';
};

export const API_URL = getApiUrl();
export default API_URL;
