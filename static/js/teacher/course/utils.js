// /static/js/teacher/course/utils.js
// 공통 유틸리티 함수들
// 브라우저 콘솔에서 실행할 수 있는 디버깅 함수
window.debugContentSelection = function() {
    console.log('=== 현재 상태 디버깅 ===');
    console.log('currentNode:', window.currentNode);
    console.log('currentActiveNodeId:', window.currentActiveNodeId);
    console.log('courseConfig:', window.courseConfig);
    console.log('SlideManager 존재:', !!window.SlideManager);
    console.log('ContentSelectionManager 존재:', !!window.ContentSelectionManager);
    
    if (window.currentNode) {
        console.log('현재 노드 타입:', window.currentNode.data.type);
        console.log('현재 노드 ID:', window.currentNode.data.id);
    }
    
    console.log('=== 디버깅 종료 ===');
}
// CSRF 토큰 가져오기
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

// 메시지 표시
function showMessage(message, type = 'success') {
    const messageContainer = document.getElementById('messageContainer');
    if (!messageContainer) return;
    
    const alertDiv = document.createElement('div');
    
    alertDiv.className = `alert-message alert-${type}`;
    alertDiv.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} mr-3"></i>
            <span>${message}</span>
        </div>
    `;
    
    messageContainer.appendChild(alertDiv);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        alertDiv.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => alertDiv.remove(), 300);
    }, 3000);
}

// 성공 메시지
function showSuccess(message) {
    showMessage(message, 'success');
}

// 에러 메시지
function showError(message) {
    showMessage(message, 'error');
}

// 로딩 표시
function showLoading(container) {
    if (!container) return;
    container.innerHTML = `
        <div class="loading-container">
            <div class="loading-spinner"></div>
        </div>
    `;
}

// 빈 상태 표시
function showEmptyState(container, icon, message, actionButton = null) {
    if (!container) return;
    
    let html = `
        <div class="text-center py-12 bg-gray-50 rounded-lg">
            <i class="fas ${icon} text-gray-300 text-5xl mb-4"></i>
            <p class="text-gray-500">${message}</p>
    `;
    
    if (actionButton) {
        html += actionButton;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

// 폼 데이터를 객체로 변환
function formDataToObject(formData) {
    const object = {};
    formData.forEach((value, key) => {
        object[key] = value;
    });
    return object;
}

// Ajax 요청 래퍼
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'X-CSRFToken': getCookie('csrftoken') || window.courseConfig?.csrfToken || '',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        },
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        // Content-Type 확인
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || '요청 처리 중 오류가 발생했습니다.');
            }
            
            return data;
        } else {
            // JSON이 아닌 응답 처리
            if (!response.ok) {
                throw new Error(`서버 오류: ${response.status}`);
            }
            return { success: true };
        }
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

// 폼 제출 헬퍼
async function submitForm(url, formData, method = 'POST') {
    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'X-CSRFToken': getCookie('csrftoken') || window.courseConfig?.csrfToken || '',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        });
        
        // Content-Type 확인
        const contentType = response.headers.get('content-type');
        const isJson = contentType && contentType.includes('application/json');
        
        if (!response.ok) {
            if (isJson) {
                const errorData = await response.json();
                throw new Error(errorData.error || '폼 제출 중 오류가 발생했습니다.');
            } else {
                throw new Error('서버 오류가 발생했습니다.');
            }
        }
        
        // JSON이 아닌 경우 처리
        if (!isJson) {
            // HTML 응답인 경우 (리다이렉트 등) 성공으로 간주
            return { success: true, message: '저장되었습니다.' };
        }
        
        return await response.json();
    } catch (error) {
        console.error('Form Submit Error:', error);
        throw error;
    }
}

// 디바운스 함수
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// HTML 이스케이프
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

// 트리 새로고침 - 순수 JavaScript 버전만 사용
function refreshTree() {
    // course_detail_onepage.html의 loadCourseStructure 함수 호출
    if (typeof loadCourseStructure === 'function') {
        console.log('트리 구조 새로고침');
        loadCourseStructure();
    } else {
        console.warn('loadCourseStructure 함수를 찾을 수 없습니다.');
    }
}

// 폼 취소
function cancelForm(cardId) {
    const card = document.getElementById(cardId);
    if (card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(-10px)';
        setTimeout(() => card.remove(), 300);
    }
}

// URL 파라미터 가져오기
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// 노드 콘텐츠 로드 함수는 course_detail_onepage.html에서 직접 구현하므로 제거


// utils.js에 추가
window.ContentSelectionManager = {
    // 선택된 콘텐츠 ID들을 저장하는 Map (context별로 관리)
    selections: new Map(),
    
    // 컨텍스트별 선택 상태 가져오기
    getSelection: function(context = 'global') {
        if (!this.selections.has(context)) {
            this.selections.set(context, new Set());
        }
        return this.selections.get(context);
    },
    
    // 선택 토글
    toggle: function(contentId, context = 'global') {
        const selection = this.getSelection(context);
        
        if (selection.has(contentId)) {
            selection.delete(contentId);
            return false; // 선택 해제됨
        } else {
            selection.add(contentId);
            return true; // 선택됨
        }
    },
    
    // 선택 상태 확인
    isSelected: function(contentId, context = 'global') {
        return this.getSelection(context).has(contentId);
    },
    
    // 전체 선택 해제
    clearAll: function(context = 'global') {
        this.getSelection(context).clear();
    },
    
    // 선택 개수
    getCount: function(context = 'global') {
        return this.getSelection(context).size;
    }
};