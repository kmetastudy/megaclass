// static/js/teacher/course/onepage-main.js
// 메인 초기화 및 공통 기능

// 전역 변수
window.currentNode = null;
window.currentActiveNodeId = null;
window.contentsPanelOpen = false;
window.droppedContents = [];
window.structureData = null;

// 페이지 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    loadContentTypes();
});

// 페이지 초기화
function initializePage() {
    console.log('Initializing onepage course management...');
    
    // 초기 트리 로드
    if (window.loadCourseStructure) {
        window.loadCourseStructure();
    }
    
    // 콘텐츠 타입 로드
    loadContentTypes();
    
    // 이벤트 리스너 등록
    setupEventListeners();
    
    // 드롭 영역 초기화
    setupDropZone();
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 윈도우 리사이즈
    window.addEventListener('resize', debounce(handleWindowResize, 250));
    
    // 키보드 단축키
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // 패널 토글 버튼들
    const toggleButtons = document.querySelectorAll('[onclick*="toggle"]');
    toggleButtons.forEach(btn => {
        // onclick 이벤트는 HTML에서 이미 처리됨
    });
}

// 트리 패널 토글
window.toggleTreePanel = function() {
    const panel = document.getElementById('treePanel');
    const icon = document.getElementById('treePanelToggle');
    const mainContainer = document.getElementById('mainContainer');
    
    panel.classList.toggle('collapsed');
    
    if (panel.classList.contains('collapsed')) {
        icon.className = 'fas fa-chevron-right';
    } else {
        icon.className = 'fas fa-chevron-left';
    }
    
    // 컨테이너 레이아웃 조정
    updateMainContainerLayout();
};

// 콘텐츠 패널 토글
window.toggleContentsPanel = function() {
    const panel = document.getElementById('contentsPanel');
    const icon = document.getElementById('contentsPanelToggle');
    const mainContainer = document.getElementById('mainContainer');
    
    window.contentsPanelOpen = !window.contentsPanelOpen;
    
    if (window.contentsPanelOpen) {
        panel.classList.remove('collapsed');
        mainContainer.classList.add('contents-open');
        icon.className = 'fas fa-chevron-right';
        
        // 콘텐츠 패널이 열릴 때 필터 초기화
        if (window.initializeContentFilters) {
            window.initializeContentFilters();
        }
    } else {
        panel.classList.add('collapsed');
        mainContainer.classList.remove('contents-open');
        icon.className = 'fas fa-chevron-left';
    }
    
    updateMainContainerLayout();
};

// 메인 컨테이너 레이아웃 업데이트
function updateMainContainerLayout() {
    const mainContainer = document.getElementById('mainContainer');
    const treePanel = document.getElementById('treePanel');
    const contentPanel = document.getElementById('contentPanel');
    const contentsPanel = document.getElementById('contentsPanel');
    
    // 레이아웃 클래스 재계산
    setTimeout(() => {
        mainContainer.style.height = `calc(100vh - 120px)`;
    }, 50);
}

// 트리 새로고침
window.refreshTree = function() {
    if (window.loadCourseStructure) {
        window.loadCourseStructure();
        showMessage('코스 구조가 새로고침되었습니다.', 'success');
    }
};

// 콘텐츠 타입 로드
async function loadContentTypes() {
    try {
        const response = await fetch('/teacher/api/content-types/', {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            populateContentTypeSelects(data.content_types);
        }
    } catch (error) {
        console.error('콘텐츠 타입 로드 오류:', error);
    }
}

// 콘텐츠 타입 선택박스 채우기
function populateContentTypeSelects(contentTypes) {
    const selects = [
        document.getElementById('contentTypeFilter'),
        document.getElementById('createContentType')
    ];
    
    selects.forEach(select => {
        if (select) {
            contentTypes.forEach(type => {
                const option = document.createElement('option');
                option.value = type.id;
                option.textContent = type.type_name;
                select.appendChild(option);
            });
        }
    });
}

// 드롭 영역 설정
function setupDropZone() {
    const dropZone = document.getElementById('dropZone');
    const droppedContents = document.getElementById('droppedContents');
    const droppedContentsList = document.getElementById('droppedContentsList');
    
    if (!dropZone) return;
    
    // 드래그 오버 이벤트
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        dropZone.classList.add('drag-over');
    });
    
    // 드래그 리브 이벤트
    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        if (!dropZone.contains(e.relatedTarget)) {
            dropZone.classList.remove('drag-over');
        }
    });
    
    // 드롭 이벤트
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const contentData = {
            id: e.dataTransfer.getData('text/plain'),
            title: e.dataTransfer.getData('title'),
            type: e.dataTransfer.getData('type'),
            chapter: e.dataTransfer.getData('chapter'),
            subchapter: e.dataTransfer.getData('subchapter')
        };
        
        if (contentData.id) {
            addDroppedContent(contentData);
        }
    });
    
    // 드롭된 콘텐츠 목록 정렬 가능하게 만들기
    if (droppedContentsList && typeof Sortable !== 'undefined') {
        new Sortable(droppedContentsList, {
            animation: 150,
            ghostClass: 'sortable-ghost',
            onEnd: function(evt) {
                updateDroppedContentOrder();
            }
        });
    }
}

// 드롭된 콘텐츠 추가
window.addDroppedContent = function(contentData) {
    // 중복 확인
    const existingIndex = window.droppedContents.findIndex(item => item.id === contentData.id);
    if (existingIndex !== -1) {
        showMessage('이미 추가된 콘텐츠입니다.', 'warning');
        return;
    }
    
    window.droppedContents.push(contentData);
    renderDroppedContents();
    
    // 드롭 영역 숨기고 목록 표시
    const dropZone = document.getElementById('dropZone');
    const droppedContents = document.getElementById('droppedContents');
    
    if (dropZone && droppedContents) {
        dropZone.style.display = 'none';
        droppedContents.style.display = 'block';
    }
    
    showMessage(`"${contentData.title}"이(가) 추가되었습니다.`, 'success');
};

// 드롭된 콘텐츠 제거
window.removeDroppedContent = function(contentId) {
    const index = window.droppedContents.findIndex(item => item.id === contentId);
    if (index !== -1) {
        const removedItem = window.droppedContents.splice(index, 1)[0];
        renderDroppedContents();
        showMessage(`"${removedItem.title}"이(가) 제거되었습니다.`, 'info');
        
        // 목록이 비어있으면 드롭 영역 다시 표시
        if (window.droppedContents.length === 0) {
            const dropZone = document.getElementById('dropZone');
            const droppedContents = document.getElementById('droppedContents');
            
            if (dropZone && droppedContents) {
                dropZone.style.display = 'flex';
                droppedContents.style.display = 'none';
            }
        }
    }
};

// 드롭된 콘텐츠 렌더링
function renderDroppedContents() {
    const container = document.getElementById('droppedContentsList');
    if (!container) return;
    
    container.innerHTML = window.droppedContents.map((content, index) => `
        <div class="dropped-content-item" data-content-id="${content.id}">
            <div class="dropped-content-info">
                <div class="dropped-content-title">${escapeHtml(content.title)}</div>
                <div class="dropped-content-meta">
                    <span class="content-type-badge ${getContentTypeBadgeClass(content.type)}">
                        ${escapeHtml(content.type)}
                    </span>
                    ${content.chapter ? `<span class="ml-2 text-gray-600">${escapeHtml(content.chapter)}</span>` : ''}
                    ${content.subchapter ? `<span class="ml-1 text-gray-500">→ ${escapeHtml(content.subchapter)}</span>` : ''}
                </div>
            </div>
            <div class="dropped-content-actions">
                <button onclick="removeDroppedContent('${content.id}')" class="btn-remove" title="제거">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// 드롭된 콘텐츠 순서 업데이트
function updateDroppedContentOrder() {
    const items = document.querySelectorAll('#droppedContentsList .dropped-content-item');
    const newOrder = Array.from(items).map(item => {
        const contentId = item.dataset.contentId;
        return window.droppedContents.find(content => content.id === contentId);
    }).filter(Boolean);
    
    window.droppedContents = newOrder;
}

// 콘텐츠 타입별 배지 클래스
function getContentTypeBadgeClass(type) {
    const badgeMap = {
        '객관식': 'badge-blue',
        '단답형': 'badge-green', 
        '서술형': 'badge-purple',
        'PPT': 'badge-orange',
        '리포트': 'badge-gray'
    };
    return badgeMap[type] || 'badge-gray';
}

// 메시지 표시
window.showMessage = function(message, type = 'success') {
    const container = document.getElementById('messageContainer');
    if (!container) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `fixed top-4 right-4 z-50 max-w-sm w-full bg-white rounded-lg shadow-lg border-l-4 ${
        type === 'success' ? 'border-green-500' : 
        type === 'error' ? 'border-red-500' : 
        type === 'warning' ? 'border-yellow-500' : 'border-blue-500'
    } p-4 transform transition-transform duration-300 ease-in-out translate-x-full`;
    
    const iconClass = {
        success: 'fa-check-circle text-green-500',
        error: 'fa-exclamation-circle text-red-500',
        warning: 'fa-exclamation-triangle text-yellow-500',
        info: 'fa-info-circle text-blue-500'
    }[type] || 'fa-info-circle text-blue-500';
    
    alertDiv.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${iconClass} mr-3"></i>
            <div class="flex-1">
                <p class="text-gray-800 font-medium">${escapeHtml(message)}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-3 text-gray-400 hover:text-gray-600">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(alertDiv);
    
    // 애니메이션으로 표시
    setTimeout(() => {
        alertDiv.classList.remove('translate-x-full');
    }, 100);
    
    // 5초 후 자동 제거
    setTimeout(() => {
        alertDiv.classList.add('translate-x-full');
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 300);
    }, 5000);
};

// 윈도우 리사이즈 핸들러
function handleWindowResize() {
    updateMainContainerLayout();
}

// 키보드 단축키 처리
function handleKeyboardShortcuts(e) {
    // Ctrl/Cmd + R: 새로고침
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        window.refreshTree();
    }
    
    // ESC: 패널 닫기
    if (e.key === 'Escape') {
        if (window.contentsPanelOpen) {
            window.toggleContentsPanel();
        }
    }
    
    // Ctrl/Cmd + L: 콘텐츠 라이브러리 토글
    if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
        e.preventDefault();
        window.toggleContentsPanel();
    }
}

// 유틸리티 함수들
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

// API 요청 헬퍼
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'X-CSRFToken': getCookie('csrftoken') || window.courseConfig.csrfToken,
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
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || '요청 처리 중 오류가 발생했습니다.');
            }
            
            return data;
        } else {
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