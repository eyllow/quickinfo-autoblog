# Auto-Blog 5 Improvements Task

Read all relevant files before editing. Do ALL 5 tasks.

## Task 1: Fix Duplicate Post Publishing (URGENT)
Files: `main.py`, `publishers/wordpress.py`, `database/models.py`

Problem: Same topic gets published multiple times. Duplicate check only uses exact keyword match in SQLite.

Fix:
1. In `publishers/wordpress.py`, add method `get_recent_post_titles(days=7)` that calls WP REST API (`/wp-json/wp/v2/posts?per_page=50&status=publish`) and returns list of (title, slug) tuples.
2. In `main.py` `run_pipeline()`, before processing keywords, fetch recent WP titles. Skip keyword if it appears as substring in any recent title or vice versa.
3. In `database/models.py`, add `is_similar_keyword_published(keyword, days=7)` checking substring overlap with published keywords from last 7 days.

## Task 2: Add Blog Reference/Benchmarking Feature
Create `crawlers/blog_reference.py` (NEW)

1. Search Naver blog: `https://search.naver.com/search.naver?where=blog&query={keyword}&sm=tab_opt&sort=sim`
2. Fetch top 3 blog URLs from search results (parse HTML, find blog links)
3. For each blog, extract: heading structure, approximate length, key subtopics
4. Return structured summary string

Integration in `generators/content_generator.py`:
- In `generate_full_post()`, after Step 2 (web search), add blog reference crawling
- Pass blog analysis to content generation prompt as context
- In prompt: "[참고 블로그 구조 분석]\n{blog_analysis}\n위 인기 블로그의 구조와 소제목 패턴을 참고하여 작성하세요."

## Task 3: Improve Topic Selection Algorithm
Create `crawlers/topic_selector.py` (NEW), update `main.py`

TopicSelector class:
1. Combine sources:
   - Google Trends RSS (existing GoogleTrendsCrawler)
   - Naver DataLab real-time: scrape `https://datalab.naver.com/keyword/realtimeList.naver`
   - Naver autocomplete (existing in naver_related.py)
2. Score keywords:
   - Google Trends: +3
   - Naver autocomplete suggestion count: +1 per (max 5)
   - Naver DataLab: +4
   - Multi-source bonus: 2+ sources = x1.5
3. Return sorted by score, filtered by already-published

Update `main.py`: replace `trends_crawler.get_trending_keywords_simple()` with `TopicSelector().get_best_keywords(limit=5)`

## Task 4: Fix Image Insertion (Multi-source Fallback)
Find which image fetcher is actually used in the content pipeline and modify it.

1. Add Unsplash fallback: `https://api.unsplash.com/search/photos?query={query}&client_id={key}&per_page=5`
2. Add Pixabay fallback: `https://pixabay.com/api/?key={key}&q={query}&image_type=photo&per_page=5&min_width=800`
3. Fallback chain: Pexels -> Unsplash -> Pixabay
4. Add `unsplash_api_key` and `pixabay_api_key` to `config/settings.py` (env: UNSPLASH_ACCESS_KEY, PIXABAY_API_KEY)
5. Timeout: 5 seconds per source
6. If ALL fail, use colored div placeholder with keyword text (NOT via.placeholder.com)

## Task 5: Improve Related Link Cards
Files: `media/link_matcher.py`, `generators/prompts.py`

Replace gradient card with clean reference-style card. Use table-based layout for WP compat:

```html
<div style="margin: 24px 0; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
  <a href="{url}" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: block; padding: 20px 24px;">
    <table style="width: 100%; border: none; border-collapse: collapse;">
      <tr>
        <td style="width: 56px; vertical-align: middle; padding-right: 16px;">
          <div style="width: 48px; height: 48px; background: #f1f5f9; border-radius: 10px; text-align: center; line-height: 48px;">
            <img src="https://www.google.com/s2/favicons?domain={domain}&sz=32" alt="" style="width: 32px; height: 32px; vertical-align: middle;" onerror="this.style.display='none'" />
          </div>
        </td>
        <td style="vertical-align: middle;">
          <p style="margin: 0 0 4px 0; font-size: 16px; font-weight: 700; color: #1a202c;">{name}</p>
          <p style="margin: 0; font-size: 13px; color: #64748b;">{description}</p>
          <p style="margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;">{domain}</p>
        </td>
        <td style="width: 32px; vertical-align: middle; text-align: right; color: #94a3b8; font-size: 20px;">&#8594;</td>
      </tr>
    </table>
  </a>
</div>
```

Update both `generate_link_button_html()` in link_matcher.py AND `OFFICIAL_BUTTON_TEMPLATE` in prompts.py.
Extract domain from URL with urllib.parse.
Update `insert_link_into_content()` to insert ALL matching sites (max 3), not just primary.

## Rules
- Read each file FULLY before editing
- Do NOT break existing functionality  
- git add -A && git commit -m "feat: 5 improvements - dedup, blog reference, topic selection, image fallback, link cards"
- Test: python -c "from crawlers.topic_selector import TopicSelector; from crawlers.blog_reference import BlogReferenceCrawler; print('OK')"
