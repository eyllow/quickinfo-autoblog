"""구글 시트 연동 모듈 - 쿠팡 상품 DB"""
import logging
from typing import Optional
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """구글 시트 클라이언트"""

    def __init__(self):
        self.spreadsheet_id = settings.google_sheets_spreadsheet_id
        self.credentials_path = settings.google_credentials_path
        self._client = None
        self._sheet = None

    def _get_client(self) -> gspread.Client:
        """인증된 gspread 클라이언트 반환"""
        if self._client is None:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly'
            ]

            try:
                creds = Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=scopes
                )
                self._client = gspread.authorize(creds)
                logger.info("Google Sheets client authorized successfully")
            except Exception as e:
                logger.error(f"Failed to authorize Google Sheets: {e}")
                raise

        return self._client

    def _get_sheet(self) -> gspread.Spreadsheet:
        """스프레드시트 반환"""
        if self._sheet is None:
            client = self._get_client()
            try:
                self._sheet = client.open_by_key(self.spreadsheet_id)
                logger.info(f"Opened spreadsheet: {self._sheet.title}")
            except Exception as e:
                logger.error(f"Failed to open spreadsheet: {e}")
                raise

        return self._sheet

    def get_coupang_products(self, worksheet_name: str = None) -> list[dict]:
        """
        구글 시트에서 쿠팡 상품 목록 가져오기

        Args:
            worksheet_name: 워크시트 이름 (None이면 첫 번째 시트)

        Returns:
            상품 딕셔너리 리스트
        """
        if not self.spreadsheet_id:
            logger.warning("Google Sheets spreadsheet ID not configured")
            return []

        try:
            sheet = self._get_sheet()

            if worksheet_name:
                worksheet = sheet.worksheet(worksheet_name)
            else:
                worksheet = sheet.sheet1

            # 모든 값 가져오기
            all_values = worksheet.get_all_values()

            if len(all_values) < 2:
                logger.warning("Sheet has insufficient data")
                return []

            # 헤더 찾기: '상품명'이 있는 행을 헤더로 사용
            header_row_idx = 0
            for idx, row in enumerate(all_values):
                if '상품명' in row:
                    header_row_idx = idx
                    break

            headers = all_values[header_row_idx]
            data_rows = all_values[header_row_idx + 1:]

            logger.info(f"Found headers at row {header_row_idx + 1}: {headers}")
            logger.info(f"Fetched {len(data_rows)} data rows from Google Sheets")

            # 컬럼 인덱스 찾기 (띄어쓰기 유연하게 처리)
            def find_col_idx(name_patterns: list[str]) -> int:
                for pattern in name_patterns:
                    pattern_clean = pattern.replace(' ', '').lower()
                    for idx, header in enumerate(headers):
                        if header.replace(' ', '').lower() == pattern_clean:
                            return idx
                return -1

            col_name = find_col_idx(['상품명'])
            col_category = find_col_idx(['카테고리'])
            col_keywords = find_col_idx(['키워드'])
            col_price = find_col_idx(['가격대'])
            col_url = find_col_idx(['제휴링크'])
            col_html = find_col_idx(['HTML블로그용', 'HTML 블로그용'])

            products = []
            for row in data_rows:
                # 행 데이터가 충분한지 확인
                if len(row) <= max(col_name, col_html):
                    continue

                # 필수 필드 확인: 상품명과 HTML블로그용
                product_name = row[col_name].strip() if col_name >= 0 else ''
                html_content = row[col_html].strip() if col_html >= 0 else ''

                if product_name and html_content:
                    # 키워드를 쉼표로 분리
                    keywords_str = row[col_keywords] if col_keywords >= 0 and col_keywords < len(row) else ''
                    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]

                    product = {
                        'name': product_name,
                        'category': row[col_category].strip() if col_category >= 0 and col_category < len(row) else '',
                        'keywords': keywords,
                        'price': row[col_price].strip() if col_price >= 0 and col_price < len(row) else '',
                        'url': row[col_url].strip() if col_url >= 0 and col_url < len(row) else '',
                        'html': html_content
                    }
                    products.append(product)

            logger.info(f"Parsed {len(products)} valid products")
            return products

        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Spreadsheet not found: {self.spreadsheet_id}")
            return []
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Worksheet not found: {worksheet_name}")
            return []
        except Exception as e:
            logger.error(f"Error fetching products from Google Sheets: {e}")
            return []


# 싱글톤 인스턴스
_sheets_client: Optional[GoogleSheetsClient] = None


def get_sheets_client() -> GoogleSheetsClient:
    """GoogleSheetsClient 싱글톤 인스턴스 반환"""
    global _sheets_client
    if _sheets_client is None:
        _sheets_client = GoogleSheetsClient()
    return _sheets_client


def get_coupang_products() -> list[dict]:
    """
    구글 시트에서 쿠팡 상품 목록 가져오기 (편의 함수)

    Returns:
        상품 딕셔너리 리스트
        [
            {
                'name': '상품명',
                'category': '카테고리',
                'keywords': ['키워드1', '키워드2'],
                'price': '가격대',
                'url': '제휴링크',
                'html': 'HTML블로그용'
            },
            ...
        ]
    """
    client = get_sheets_client()
    return client.get_coupang_products()


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    products = get_coupang_products()
    print(f"\n총 {len(products)}개 상품 로드됨\n")

    for i, product in enumerate(products[:5], 1):
        print(f"{i}. {product['name']}")
        print(f"   카테고리: {product['category']}")
        print(f"   키워드: {product['keywords']}")
        print(f"   가격대: {product['price']}")
        print(f"   HTML 길이: {len(product['html'])} chars")
        print()
