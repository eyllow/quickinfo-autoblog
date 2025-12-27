<?php
// 자식 테마 스타일 로드
function quickinfo_enqueue_styles() {
    // 부모 테마 스타일
    wp_enqueue_style('parent-style', get_template_directory_uri() . '/style.css');

    // 자식 테마 스타일
    wp_enqueue_style('child-style', get_stylesheet_uri(), array('parent-style'));

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
?>
