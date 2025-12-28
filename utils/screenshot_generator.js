/**
 * Puppeteer 스크린샷 생성기 - AI 기반 동적 URL 지원
 * 키워드별 또는 동적 URL로 웹페이지 스크린샷 캡쳐
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// 키워드별 캡쳐 대상 URL (폴백용)
const SCREENSHOT_TARGETS = {
    // 금융/재테크
    "환율": {
        url: "https://finance.naver.com/marketindex/",
        selector: "#exchangeList",
        waitFor: 2000,
        viewport: { width: 800, height: 600 }
    },
    "비트코인": {
        url: "https://upbit.com/exchange?code=CRIX.UPBIT.KRW-BTC",
        selector: ".chart",
        waitFor: 5000,
        viewport: { width: 1000, height: 600 }
    },
    "주식": {
        url: "https://finance.naver.com/sise/",
        selector: ".kospi_area",
        waitFor: 2000,
        viewport: { width: 800, height: 500 }
    },
    "코스피": {
        url: "https://finance.naver.com/sise/sise_index.naver?code=KOSPI",
        selector: "#chart_area",
        waitFor: 2000,
        viewport: { width: 800, height: 500 }
    },
    "코스닥": {
        url: "https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ",
        selector: "#chart_area",
        waitFor: 2000,
        viewport: { width: 800, height: 500 }
    },

    // 생활정보
    "날씨": {
        url: "https://weather.naver.com/",
        selector: ".weather_area",
        waitFor: 2000,
        viewport: { width: 800, height: 600 }
    },
    "부동산": {
        url: "https://land.naver.com/",
        selector: ".section_price",
        waitFor: 2000,
        viewport: { width: 800, height: 500 }
    },

    // 기본값 (네이버 검색 결과)
    "default": {
        urlTemplate: "https://search.naver.com/search.naver?query={keyword}",
        waitFor: 2000,
        viewport: { width: 800, height: 600 },
        clip: { x: 0, y: 150, width: 800, height: 450 }
    }
};

/**
 * 동적 URL로 스크린샷 캡쳐 (AI 추천 URL용)
 */
async function captureDynamicScreenshot(url, outputPath) {
    console.log(`📸 동적 스크린샷 시작: ${url}`);

    const browser = await puppeteer.launch({
        headless: 'new',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
    });

    try {
        const page = await browser.newPage();

        // 기본 뷰포트 설정
        await page.setViewport({ width: 1280, height: 800 });

        // User-Agent 설정 (봇 탐지 방지)
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

        // 페이지 이동
        console.log(`🌐 페이지 로딩: ${url}`);
        await page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        // 로딩 대기
        await new Promise(r => setTimeout(r, 3000));

        // 스크린샷 (상단 영역)
        await page.screenshot({
            path: outputPath,
            type: 'png',
            clip: { x: 0, y: 0, width: 1280, height: 700 }
        });

        console.log(`✅ 동적 스크린샷 저장: ${outputPath}`);
        return outputPath;

    } catch (error) {
        console.error(`❌ 동적 스크린샷 에러: ${error.message}`);
        return null;
    } finally {
        await browser.close();
    }
}

/**
 * 키워드 기반 스크린샷 캡쳐 (기존 로직)
 */
async function captureScreenshot(keyword, outputPath) {
    console.log(`📸 스크린샷 캡쳐 시작: ${keyword}`);

    const browser = await puppeteer.launch({
        headless: 'new',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
    });

    try {
        const page = await browser.newPage();

        // 키워드에 맞는 타겟 찾기
        let target = null;
        let matchedKey = null;
        for (const [key, value] of Object.entries(SCREENSHOT_TARGETS)) {
            if (key !== 'default' && keyword.includes(key)) {
                target = value;
                matchedKey = key;
                console.log(`🎯 매칭된 타겟: ${key}`);
                break;
            }
        }

        // 타겟 없으면 기본값 사용
        if (!target) {
            target = { ...SCREENSHOT_TARGETS["default"] };
            target.url = target.urlTemplate.replace("{keyword}", encodeURIComponent(keyword));
            console.log(`🔍 기본 검색 결과 캡쳐: ${keyword}`);
        }

        // 뷰포트 설정
        await page.setViewport(target.viewport || { width: 800, height: 600 });

        // User-Agent 설정 (봇 탐지 방지)
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

        // 페이지 이동
        console.log(`🌐 페이지 로딩: ${target.url}`);
        await page.goto(target.url, {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        // 대기
        if (target.waitFor) {
            await new Promise(r => setTimeout(r, target.waitFor));
        }

        // 스크린샷 옵션
        const screenshotOptions = {
            path: outputPath,
            type: 'png'
        };

        // 특정 셀렉터가 있으면 해당 요소만 캡쳐
        if (target.selector) {
            try {
                const element = await page.$(target.selector);
                if (element) {
                    await element.screenshot(screenshotOptions);
                    console.log(`✅ 요소 캡쳐 완료: ${target.selector}`);
                } else {
                    // 셀렉터 못 찾으면 전체 페이지 캡쳐
                    if (target.clip) {
                        screenshotOptions.clip = target.clip;
                    }
                    await page.screenshot(screenshotOptions);
                    console.log(`⚠️ 셀렉터 없음, 전체 캡쳐`);
                }
            } catch (e) {
                await page.screenshot(screenshotOptions);
                console.log(`⚠️ 셀렉터 에러, 전체 캡쳐`);
            }
        } else {
            // 클립 영역이 있으면 해당 영역만
            if (target.clip) {
                screenshotOptions.clip = target.clip;
            }
            await page.screenshot(screenshotOptions);
        }

        console.log(`📸 스크린샷 저장: ${outputPath}`);
        return outputPath;

    } catch (error) {
        console.error(`❌ 스크린샷 에러: ${error.message}`);
        return null;
    } finally {
        await browser.close();
    }
}

/**
 * 텍스트 오버레이 추가 (Sharp 사용)
 */
async function addTextOverlay(inputPath, text, outputPath) {
    try {
        const sharp = require('sharp');

        // 이미지 크기 가져오기
        const metadata = await sharp(inputPath).metadata();
        const width = metadata.width;
        const height = 60;

        // HTML 엔티티 이스케이프
        const escapedText = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');

        // SVG 텍스트 오버레이 생성
        const svgText = `
        <svg width="${width}" height="${height}">
            <rect x="0" y="0" width="${width}" height="${height}" fill="rgba(0,0,0,0.75)"/>
            <text x="${width/2}" y="40" font-family="Arial, sans-serif" font-size="22"
                  fill="white" text-anchor="middle" font-weight="bold">
                ${escapedText}
            </text>
        </svg>`;

        const textBuffer = Buffer.from(svgText);

        await sharp(inputPath)
            .composite([{
                input: textBuffer,
                top: 0,
                left: 0
            }])
            .toFile(outputPath);

        console.log(`✏️ 텍스트 오버레이 추가: ${outputPath}`);
        return outputPath;

    } catch (error) {
        console.error(`❌ 오버레이 에러: ${error.message}`);
        // 오버레이 실패해도 원본 반환
        return inputPath;
    }
}

// CLI 실행
if (require.main === module) {
    const args = process.argv.slice(2);

    // 파라미터 파싱 헬퍼
    const getArg = (name) => {
        const idx = args.indexOf(`--${name}`);
        return idx !== -1 ? args[idx + 1] : null;
    };

    const url = getArg('url');           // 동적 URL (AI 추천)
    const keyword = getArg('keyword');   // 키워드 (기존 방식)
    const output = getArg('output') || './screenshot.png';
    const text = getArg('text');

    // 동적 URL이 있으면 동적 캡쳐, 아니면 키워드 기반 캡쳐
    const capturePromise = url
        ? captureDynamicScreenshot(url, output)
        : captureScreenshot(keyword || '테스트', output);

    capturePromise.then(async (result) => {
        if (result && text) {
            const finalOutput = output.replace('.png', '_overlay.png');
            const overlayResult = await addTextOverlay(result, text, finalOutput);
            console.log(`RESULT:${overlayResult}`);
        } else if (result) {
            console.log(`RESULT:${result}`);
        } else {
            console.log('RESULT:FAILED');
        }
    });
}

module.exports = { captureScreenshot, captureDynamicScreenshot, addTextOverlay };
