// /static/js/teacher/course/utils.js
// 공통 유틸리티 함수들

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
    container.innerHTML = `
        <div class="loading-container">
            <div class="loading-spinner"></div>
        </div>
    `;
}

// 빈 상태 표시
function showEmptyState(container, icon, message, actionButton = null) {
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
// utils.js의 apiRequest 함수 수정
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest', // 추가
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

async function apiRequest_0616(url, options = {}) {
    const defaultOptions = {
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
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
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '요청 처리 중 오류가 발생했습니다.');
        }
        
        return data;
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
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest', // AJAX 요청임을 명시
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
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// 트리 새로고침
function refreshTree() {
    $('#courseTree').jstree('refresh');
}

// 트리 패널 토글
function toggleTreePanel() {
    const panel = document.getElementById('treePanel');
    const icon = document.getElementById('treePanelToggle');
    
    panel.classList.toggle('collapsed');
    if (panel.classList.contains('collapsed')) {
        icon.classList.remove('fa-chevron-left');
        icon.classList.add('fa-chevron-right');
    } else {
        icon.classList.remove('fa-chevron-right');
        icon.classList.add('fa-chevron-left');
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

// 노드 콘텐츠 로드
async function loadNodeContent(node) {
    const type = node.data.type;
    const id = node.data.id;
    const contentArea = document.getElementById('contentArea');
    
    showLoading(contentArea);
    
    if (type === 'course') {
        loadCourseOverview();
        return;
    }
    
    try {
        const data = await apiRequest(`/teacher/api/${type}/${id}/detail/`);
        displayContent(type, data);
        
        // 차시인 경우 슬라이드 데이터도 로드
        if (type === 'chasi') {
            setTimeout(() => {
                if (window.SlideManager) {
                    window.SlideManager.loadChasiContent(id);
                }
            }, 100);
        }
    } catch (error) {
        contentArea.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-exclamation-circle text-red-500 text-5xl mb-4"></i>
                <p class="text-gray-700">콘텐츠를 불러올 수 없습니다.</p>
                <p class="text-sm text-gray-500 mt-2">${error.message}</p>
            </div>
        `;
    }
}

// 콘텐츠 표시
function displayContent(type, data) {
    let html = '';
    let title = '';
    
    switch(type) {
        case 'chapter':
            title = `<i class="fas fa-bookmark mr-2"></i>대단원 상세`;
            html = window.ChapterManager ? window.ChapterManager.renderDetail(data) : '';
            break;
        case 'subchapter':
            title = `<i class="fas fa-file-alt mr-2"></i>소단원 상세`;
            html = window.SubChapterManager ? window.SubChapterManager.renderDetail(data) : '';
            break;
        case 'chasi':
            title = `<i class="fas fa-clock mr-2"></i>차시 상세`;
            html = window.ChasiManager ? window.ChasiManager.renderDetail(data) : '';
            break;
    }
    
    document.getElementById('contentTitle').innerHTML = title;
    document.getElementById('contentArea').innerHTML = html;
}