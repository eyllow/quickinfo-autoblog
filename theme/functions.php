<?php
// 자식 테마 스타일 로드
function quickinfo_enqueue_styles() {
    // 부모 테마 스타일
    wp_enqueue_style('parent-style', get_template_directory_uri() . '/style.css');

    // 자식 테마 스타일 (우선순위 높임)
    wp_enqueue_style('child-style', get_stylesheet_uri(), array('parent-style'), '1.0.1');

    // Google Fonts (Noto Sans KR)
    wp_enqueue_style('google-fonts', 'https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
}
add_action('wp_enqueue_scripts', 'quickinfo_enqueue_styles');

// 푸터 메뉴 등록
function quickinfo_register_menus() {
    register_nav_menus(array(
        'footer-menu' => '푸터 메뉴',
    ));
}
add_action('init', 'quickinfo_register_menus');

// 저작권 연도 자동 업데이트
function quickinfo_copyright() {
    return '© ' . date('Y') . ' QuickInfo. All rights reserved.';
}
add_shortcode('copyright', 'quickinfo_copyright');

// 특성 이미지 없는 포스트 처리 (빈 공간 제거)
function quickinfo_remove_empty_featured_image($html, $post_id, $post_thumbnail_id, $size, $attr) {
    if (empty($html)) {
        return '';
    }
    return $html;
}
add_filter('post_thumbnail_html', 'quickinfo_remove_empty_featured_image', 10, 5);

// 다크 모드 비활성화 + 레이아웃 오버라이드
function quickinfo_head_styles() {
    echo '<style>
        html, body {
            color-scheme: light !important;
        }
        /* Fix: qi-grid 사이드바 레이아웃 — 부모 테마 constrained 오버라이드 */
        .qi-grid {
            max-width: 1100px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            display: grid !important;
            grid-template-columns: 1fr 300px !important;
            gap: 40px !important;
        }
        .qi-main-col {
            max-width: none !important;
            min-width: 0 !important;
        }
        .qi-side-col {
            max-width: none !important;
            min-width: 0 !important;
            position: sticky !important;
            top: 20px !important;
        }
        /* constrained 레이아웃이 qi-grid를 제한하지 못하게 */
        .is-layout-constrained > .qi-grid,
        .is-layout-constrained > .qi-container {
            max-width: none !important;
        }
        @media (max-width: 768px) {
            .qi-grid {
                grid-template-columns: 1fr !important;
            }
            .qi-side-col {
                position: static !important;
            }
        }
    </style>';
}
add_action('wp_head', 'quickinfo_head_styles');
?>
