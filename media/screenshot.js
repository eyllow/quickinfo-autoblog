#!/usr/bin/env node
/**
 * Puppeteer 스크린샷 캡처 스크립트
 *
 * 사용법:
 *   node screenshot.js <url> <output_path> [keyword]
 *
 * 예시:
 *   node screenshot.js "https://naver.com" "/tmp/screenshot.png" "뉴스"
 */

const puppeteer = require('puppeteer');
const path = require('path');

// 사이트별 설정 (대기 시간, 스크롤 등)
const SITE_CONFIGS = {
    'www.gov.kr': {
        waitTime: 5000,
        scroll: false
    },
    'www.hometax.go.kr': {
        waitTime: 4000,
        scroll: false
    },
    'www.nhis.or.kr': {
        waitTime: 4000,
        scroll: false
    },
    'www.nps.or.kr': {
        waitTime: 4000,
        scroll: false
    },
    'www.ei.go.kr': {
        waitTime: 4000,
        scroll: false
    },
    'default': {
        waitTime: 2000,
        scroll: false
    }
};

// 도메인에서 설정 가져오기
function getSiteConfig(url) {
    try {
        const urlObj = new URL(url);
        return SITE_CONFIGS[urlObj.hostname] || SITE_CONFIGS['default'];
    } catch {
        return SITE_CONFIGS['default'];
    }
}

// 인물/연예인 키워드용 검색 URL 생성
function getSearchUrl(keyword) {
    // 네이버 뉴스 검색
    const encodedKeyword = encodeURIComponent(keyword);
    return `https://search.naver.com/search.naver?where=news&query=${encodedKeyword}`;
}

// 정보성 키워드별 공식 사이트 URL
const OFFICIAL_SITES = {
    '연말정산': 'https://www.hometax.go.kr/',
    '청년도약계좌': 'https://www.kinfa.or.kr/',
    '청년미래적금': 'https://www.kinfa.or.kr/',
    '주택청약': 'https://www.applyhome.co.kr/',
    '환율': 'https://finance.naver.com/marketindex/',
    '코스피': 'https://finance.naver.com/sise/',
    '코스닥': 'https://finance.naver.com/sise/',
    '비트코인': 'https://upbit.com/exchange?code=CRIX.UPBIT.KRW-BTC',
    '이더리움': 'https://upbit.com/exchange?code=CRIX.UPBIT.KRW-ETH',
    '날씨': 'https://weather.naver.com/',
    '자동차보험': 'https://www.knia.or.kr/',
    '실비보험': 'https://www.klia.or.kr/',
    '건강보험': 'https://www.nhis.or.kr/',
    '국민연금': 'https://www.nps.or.kr/',
    '고용보험': 'https://www.ei.go.kr/',
};

async function captureScreenshot(url, outputPath, keyword = '') {
    let browser;

    try {
        // 사이트별 설정 가져오기
        const siteConfig = getSiteConfig(url);
        console.error(`Site config: waitTime=${siteConfig.waitTime}ms`);

        // 브라우저 실행 (한글 설정 포함)
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process',
                '--no-zygote',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--window-size=1280,800',
                '--font-render-hinting=none',
                '--lang=ko-KR'
            ]
        });

        const page = await browser.newPage();

        // 뷰포트 설정
        await page.setViewport({
            width: 1280,
            height: 800,
            deviceScaleFactor: 2  // 고해상도
        });

        // User-Agent 설정 (최신 Chrome 버전)
        await page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );

        // 한국어 Accept-Language 헤더 설정
        await page.setExtraHTTPHeaders({
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        });

        // 페이지 로드
        console.error(`Loading: ${url}`);
        await page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        // 사이트별 대기 시간 적용 (동적 콘텐츠 로드)
        await new Promise(resolve => setTimeout(resolve, siteConfig.waitTime));

        // 팝업/모달 닫기 시도
        try {
            await page.evaluate(() => {
                // 일반적인 팝업 닫기 버튼 클릭
                const closeSelectors = [
                    '[class*="close"]',
                    '[class*="popup"] button',
                    '.modal-close',
                    '#close',
                    '.btn-close',
                    '[aria-label="닫기"]',
                    '[title="닫기"]',
                    '.layer_close',
                    '.popup_close'
                ];
                closeSelectors.forEach(selector => {
                    const btns = document.querySelectorAll(selector);
                    btns.forEach(btn => {
                        try { btn.click(); } catch {}
                    });
                });

                // 오버레이/모달 제거
                const overlaySelectors = [
                    '[class*="overlay"]',
                    '[class*="modal"]',
                    '[class*="popup"]',
                    '[class*="layer"]',
                    '.dimmed'
                ];
                overlaySelectors.forEach(selector => {
                    const els = document.querySelectorAll(selector);
                    els.forEach(el => {
                        if (el.style) el.style.display = 'none';
                    });
                });
            });
            console.error('Popup/modal close attempted');
        } catch (e) {
            // 팝업 없으면 무시
        }

        // 팝업 닫은 후 잠시 대기
        await new Promise(resolve => setTimeout(resolve, 500));

        // 스크린샷 캡처
        await page.screenshot({
            path: outputPath,
            type: 'png',
            clip: {
                x: 0,
                y: 0,
                width: 1280,
                height: 800
            }
        });

        console.log(JSON.stringify({
            success: true,
            path: outputPath,
            url: url,
            keyword: keyword
        }));

    } catch (error) {
        console.error(`Error: ${error.message}`);
        console.log(JSON.stringify({
            success: false,
            error: error.message,
            url: url
        }));
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// 메인 실행
async function main() {
    const args = process.argv.slice(2);

    if (args.length < 2) {
        console.error('Usage: node screenshot.js <url|keyword> <output_path> [is_person]');
        console.error('  url: URL to capture or keyword to search');
        console.error('  output_path: Where to save the screenshot');
        console.error('  is_person: "true" if keyword is a person/celebrity');
        process.exit(1);
    }

    let url = args[0];
    const outputPath = args[1];
    const isPerson = args[2] === 'true';
    const keyword = args[3] || '';

    // URL이 아닌 경우 (키워드인 경우) 적절한 URL 생성
    if (!url.startsWith('http')) {
        const searchKeyword = url;

        // 인물/연예인 키워드면 뉴스 검색
        if (isPerson) {
            url = getSearchUrl(searchKeyword);
        }
        // 정보성 키워드면 공식 사이트
        else if (OFFICIAL_SITES[searchKeyword]) {
            url = OFFICIAL_SITES[searchKeyword];
        }
        // 그 외에는 뉴스 검색
        else {
            url = getSearchUrl(searchKeyword);
        }
    }

    await captureScreenshot(url, outputPath, keyword);
}

main();
