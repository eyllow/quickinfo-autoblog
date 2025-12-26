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
    '비트코인': 'https://upbit.com/exchange?code=CRIX.UPBIT.KRW-BTC',
    '날씨': 'https://weather.naver.com/',
};

async function captureScreenshot(url, outputPath, keyword = '') {
    let browser;

    try {
        // 브라우저 실행
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--window-size=1280,800'
            ]
        });

        const page = await browser.newPage();

        // 뷰포트 설정
        await page.setViewport({
            width: 1280,
            height: 800,
            deviceScaleFactor: 2  // 고해상도
        });

        // User-Agent 설정
        await page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );

        // 페이지 로드
        console.error(`Loading: ${url}`);
        await page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        // 페이지 로드 후 잠시 대기 (동적 콘텐츠)
        await new Promise(resolve => setTimeout(resolve, 2000));

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
