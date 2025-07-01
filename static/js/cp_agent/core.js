// static/js/cp_agent/core.js - 전역 변수 및 유틸리티 함수 (수정됨)

/* ========== 전역 변수 ========== */
// 에디터 인스턴스들 - window 객체에 직접 할당하여 일관성 확보
window.metaEditor = null;
window.tagsEditor = null; 
window.htmlEditorInstance = null;
window.answerEditor = null;
window.answerInputEditor = null;

// 기타 전역 변수들
window.currentContent = null;
window.templates = [];
window.currentEditingImage = null;
window.temporaryUploads = []; // 임시 업로드된 파일들 추적
window.originalHtmlContent = '';
window.wordMappings = new Map();

/* ========== 유틸리티 함수들 ========== */

/**
 * CSRF 토큰 가져오기
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * 알림 토스트 표시
 */
function showToast(message, type = 'success') {
    // 기존 토스트 제거
    $('.toast-notification').remove();
    
    const toastClass = type === 'error' ? 'error' : type === 'warning' ? 'warning' : '';
    const icon = type === 'error' ? 'fas fa-times-circle' : 
                 type === 'warning' ? 'fas fa-exclamation-triangle' : 
                 'fas fa-check-circle';
    
    const $toast = $(`
        <div class="toast-notification ${toastClass}">
            <i class="${icon} mr-2"></i>${message}
        </div>
    `);
    
    $('body').append($toast);
    
    // 애니메이션으로 표시
    setTimeout(() => $toast.addClass('show'), 100);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        $toast.removeClass('show');
        setTimeout(() => $toast.remove(), 300);
    }, 3000);
}

/**
 * 임시 업로드 파일 정리
 */
function cleanupTemporaryUploads() {
    if (window.temporaryUploads.length === 0) return;
    
    console.log('임시 업로드 파일 정리:', window.temporaryUploads);
    
    window.temporaryUploads.forEach(attachmentId => {
        $.ajax({
            url: `/cp/api/cleanup-temp-upload/${attachmentId}/`,
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function() {
                console.log(`임시 파일 ${attachmentId} 정리 완료`);
            },
            error: function(xhr) {
                console.error(`임시 파일 ${attachmentId} 정리 실패:`, xhr);
            }
        });
    });
    
    window.temporaryUploads = [];
}

/**
 * 정규식 이스케이프 함수
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * URL 정규화 함수
 */
function normalizeUrl(url) {
    if (!url) return '';
    
    if (url.startsWith('http://') || url.startsWith('https://')) {
        try {
            const urlObj = new URL(url);
            return urlObj.pathname;
        } catch (e) {
            console.error('URL 파싱 오류:', e);
            return url;
        }
    }
    return url;
}

/**
 * 손상된(누적된) src인지 확인
 */
function isCorruptedSrc(src) {
    if (!src) return false;
    
    // 1. 확장자가 여러 번 나타나는지 확인
    const extensions = ['.gif', '.jpg', '.jpeg', '.png', '.webp', '.svg'];
    let extCount = 0;
    
    for (const ext of extensions) {
        const matches = src.match(new RegExp(ext, 'g'));
        if (matches) {
            extCount += matches.length;
        }
    }
    
    if (extCount > 1) {
        return true; // 확장자가 2개 이상이면 누적된 것
    }
    
    // 2. media 경로가 여러 번 나타나는지 확인
    const mediaMatches = src.match(/\/media\//g);
    if (mediaMatches && mediaMatches.length > 1) {
        return true;
    }
    
    // 3. static 경로가 여러 번 나타나는지 확인
    const staticMatches = src.match(/\/static\//g);
    if (staticMatches && staticMatches.length > 1) {
        return true;
    }
    
    // 4. 비정상적으로 긴 URL (500자 이상)
    if (src.length > 500) {
        return true;
    }
    
    return false;
}

/**
 * 디버깅 함수
 */
function debugLog(category, message, data = null) {
    if (typeof console !== 'undefined' && console.log) {
        const timestamp = new Date().toISOString();
        const prefix = `[${timestamp}] [${category}]`;
        
        if (data) {
            console.log(prefix, message, data);
        } else {
            console.log(prefix, message);
        }
    }
}

/**
 * 성능 측정 유틸리티 - 중복 정의 방지
 */
if (typeof window.PerformanceTimer === 'undefined') {
    window.PerformanceTimer = class PerformanceTimer {
        constructor(name) {
            this.name = name;
            this.startTime = performance.now();
        }
        
        end() {
            const endTime = performance.now();
            const duration = endTime - this.startTime;
            debugLog('PERF', `${this.name}: ${duration.toFixed(2)}ms`);
            return duration;
        }
    };
}

/**
 * 전역 네임스페이스
 */
window.CPAgent = {
    // 전역 변수들을 네임스페이스에 노출
    get currentContent() { return window.currentContent; },
    set currentContent(value) { window.currentContent = value; },
    
    get templates() { return window.templates; },
    set templates(value) { window.templates = value; },
    
    // 유틸리티 함수들
    showToast,
    debugLog,
    PerformanceTimer: window.PerformanceTimer,
    getCookie,
    escapeRegExp,
    normalizeUrl,
    isCorruptedSrc
};