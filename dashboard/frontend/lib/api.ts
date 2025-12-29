/**
 * 중앙 집중식 API URL 설정
 * Mixed Content 에러 방지를 위해 프로토콜을 명시적으로 처리
 */

const getApiUrl = (): string => {
  // 1. 환경변수 우선 (빌드 시점에 주입됨)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // 2. 브라우저 환경에서는 현재 origin 사용 (프로토콜 포함)
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }

  // 3. 서버 사이드 폴백
  return 'https://admin.quickinfo.kr';
};

export const API_URL = getApiUrl();
export default API_URL;
