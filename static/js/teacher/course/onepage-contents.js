// static/js/teacher/course/onepage-contents.js
// 콘텐츠 라이브러리 패널 관리 및 검색

// 콘텐츠 패널 상태
const contentsState = {
    initialized: false,
    filters: {
        contentTypes: [],
        chapters: [],
        subchapters: []
    },
    searchResults: [],
    draggedContent: null
};

// 탭 전환
window.switchTab = function(tabName) {
    // 모든 탭 버튼과 컨텐츠 비활성화
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        btn.classList.add('border-transparent', 'text-gray-500');
        btn.classList.remove('border-blue-500', 'text-blue-600');
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        content.style.display = 'none';
    });
    
    // 선택된 탭 활성화
    const activeButton = event ? event.target.closest('.tab-button') : 
                        document.querySelector(`[onclick="switchTab('${tabName}')"]`);
    
    if (activeButton) {
        activeButton.classList.add('active', 'border-blue-500', 'text-blue-600');
        activeButton.classList.remove('border-transparent', 'text-gray-500');
    }
    
    const activeContent = document.getElementById(tabName + 'Tab');
    if (activeContent) {
        activeContent.classList.add('active');
        activeContent.style.display = 'block';
    }
    
    // 생성 탭이 활성화되면 에디터 초기화
    if (tabName === 'create' && window.initCreateTabEditors) {
        setTimeout(() => {
            window.initCreateTabEditors();
        }, 100);
    }
};

// 콘텐츠 필터 초기화
window.initializeContentFilters = async function() {
    if (contentsState.initialized) return;
    
    try {
        // 콘텐츠 타입 로드
        await loadContentTypesForFilter();
        
        // 대단원 로드  
        await loadChaptersForFilter();
        
        contentsState.initialized = true;
        
    } catch (error) {
        console.error('콘텐츠 필터 초기화 오류:', error);
    }
};

// 콘텐츠 타입 필터 로드
async function loadContentTypesForFilter() {
    try {
        const response = await fetch('/teacher/api/content-types/', {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const select = document.getElementById('contentTypeFilter');
            
            if (select) {
                // 기존 옵션 제거 (첫 번째 기본 옵션 제외)
                while (select.children.length > 1) {
                    select.removeChild(select.lastChild);
                }
                
                data.content_types.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type.id;
                    option.textContent = type.type_name;
                    select.appendChild(option);
                });
                
                contentsState.filters.contentTypes = data.content_types;
            }
        }
    } catch (error) {
        console.error('콘텐츠 타입 로드 오류:', error);
    }
}

// 대단원 필터 로드
async function loadChaptersForFilter() {
    try {
        // 현재 코스의 구조 데이터 사용
        if (window.structureData && window.structureData.structure.chapters) {
            const chapters = window.structureData.structure.chapters;
            const select = document.getElementById('chapterFilter');
            
            if (select) {
                // 기존 옵션 제거
                while (select.children.length > 1) {
                    select.removeChild(select.lastChild);
                }
                
                chapters.forEach(chapter => {
                    const option = document.createElement('option');
                    option.value = chapter.id;
                    option.textContent = chapter.title;
                    select.appendChild(option);
                });
                
                contentsState.filters.chapters = chapters;
                
                // 대단원 변경 이벤트 리스너
                select.addEventListener('change', function() {
                    updateSubchapterFilter(this.value);
                });
            }
        }
    } catch (error) {
        console.error('대단원 필터 로드 오류:', error);
    }
}

// 소단원 필터 업데이트
function updateSubchapterFilter(chapterId) {
    const subchapterSelect = document.getElementById('subchapterFilter');
    if (!subchapterSelect) return;
    
    // 기존 옵션 제거
    while (subchapterSelect.children.length > 1) {
        subchapterSelect.removeChild(subchapterSelect.lastChild);
    }
    
    if (!chapterId) return;
    
    // 선택된 대단원의 소단원들 찾기
    const selectedChapter = contentsState.filters.chapters.find(ch => ch.id == chapterId);
    if (selectedChapter && selectedChapter.subchapters) {
        selectedChapter.subchapters.forEach(subchapter => {
            const option = document.createElement('option');
            option.value = subchapter.id;
            option.textContent = subchapter.title;
            subchapterSelect.appendChild(option);
        });
    }
}

// 콘텐츠 검색
window.searchContents = async function() {
    const searchInput = document.getElementById('contentSearchInput');
    const typeFilter = document.getElementById('contentTypeFilter');
    const chapterFilter = document.getElementById('chapterFilter');
    const subchapterFilter = document.getElementById('subchapterFilter');
    
    const params = new URLSearchParams({
        q: searchInput ? searchInput.value : '',
        content_type: typeFilter ? typeFilter.value : '',
        chapter: chapterFilter ? chapterFilter.value : '',
        subchapter: subchapterFilter ? subchapterFilter.value : '',
        course_id: window.courseConfig.courseId
    });
    
    const contentsList = document.getElementById('contentsList');
    
    try {
        // 로딩 상태 표시
        showLoadingInContentsList();
        
        const response = await fetch(`${window.courseConfig.urls.contentsSearch}?${params}`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            contentsState.searchResults = data.results || [];
            displaySearchResults(data.results || []);
        } else {
            throw new Error('검색 중 오류가 발생했습니다.');
        }
    } catch (error) {
        console.error('콘텐츠 검색 오류:', error);
        window.showMessage(error.message, 'error');
        displaySearchError();
    }
};

// 로딩 상태 표시
function showLoadingInContentsList() {
    const contentsList = document.getElementById('contentsList');
    if (contentsList) {
        contentsList.innerHTML = `
            <div class="text-center py-8">
                <div class="loading-spinner mx-auto mb-4"></div>
                <p class="text-gray-600">검색 중...</p>
            </div>
        `;
    }
}

// 검색 결과 표시
function displaySearchResults(results) {
    const contentsList = document.getElementById('contentsList');
    if (!contentsList) return;
    
    if (results.length === 0) {
        contentsList.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-search text-4xl mb-4"></i>
                <p class="mb-2">검색 결과가 없습니다</p>
                <p class="text-sm">다른 검색어나 필터를 시도해보세요</p>
            </div>
        `;
        return;
    }
    
    contentsList.innerHTML = results.map(content => {
        return `
            <div class="content-search-item" 
                 data-content-id="${content.id}"
                 draggable="true">
                <div class="content-item-title">${escapeHtml(content.title)}</div>
                <div class="content-item-meta">
                    <span class="content-type-badge ${getContentTypeBadgeClass(content.content_type_display)}">
                        ${escapeHtml(content.content_type_display || content.content_type)}
                    </span>
                    ${content.chapter_name ? `<span class="text-gray-600 text-xs"><i class="fas fa-bookmark mr-1"></i>${escapeHtml(content.chapter_name)}</span>` : ''}
                    ${content.subchapter_name ? `<span class="text-gray-500 text-xs"><i class="fas fa-file-alt mr-1"></i>${escapeHtml(content.subchapter_name)}</span>` : ''}
                </div>
                ${content.preview ? `<div class="text-sm text-gray-600 mt-2 line-clamp-2">${escapeHtml(content.preview.substring(0, 100))}...</div>` : ''}
                <div class="flex items-center justify-between mt-3">
                    <div class="text-xs text-gray-500">
                        ${content.created_at ? `생성: ${formatDate(content.created_at)}` : ''}
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="previewContent(${content.id})" 
                                class="text-blue-600 hover:text-blue-800 text-sm"
                                title="미리보기">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button onclick="addContentToDropZone(${content.id})" 
                                class="text-green-600 hover:text-green-800 text-sm"
                                title="추가">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // 드래그 이벤트 리스너 등록
    setTimeout(() => {
        setupContentDragEvents();
    }, 100);
}

// 검색 오류 표시
function displaySearchError() {
    const contentsList = document.getElementById('contentsList');
    if (contentsList) {
        contentsList.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <i class="fas fa-exclamation-circle text-4xl mb-4"></i>
                <p class="mb-2">검색 중 오류가 발생했습니다</p>
                <button onclick="searchContents()" class="mt-2 text-blue-600 hover:text-blue-800">
                    다시 시도
                </button>
            </div>
        `;
    }
}

// 콘텐츠 타입별 배지 클래스
function getContentTypeBadgeClass(type) {
    const typeMap = {
        '객관식': 'badge-blue',
        '단답형': 'badge-green',
        '서술형': 'badge-purple', 
        'PPT': 'badge-orange',
        '리포트': 'badge-gray'
    };
    
    // 타입 문자열에 포함된 키워드로 매칭
    for (const [key, className] of Object.entries(typeMap)) {
        if (type && type.includes(key)) {
            return className;
        }
    }
    
    return 'badge-gray';
}

// 날짜 포맷팅
function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (error) {
        return dateString;
    }
}

// 드래그 이벤트 설정
function setupContentDragEvents() {
    const contentItems = document.querySelectorAll('.content-search-item[draggable="true"]');
    
    contentItems.forEach(item => {
        item.addEventListener('dragstart', function(e) {
            const contentId = this.dataset.contentId;
            const content = contentsState.searchResults.find(c => c.id == contentId);
            
            if (content) {
                e.dataTransfer.setData('text/plain', content.id);
                e.dataTransfer.setData('title', content.title);
                e.dataTransfer.setData('type', content.content_type_display || content.content_type);
                e.dataTransfer.setData('chapter', content.chapter_name || '');
                e.dataTransfer.setData('subchapter', content.subchapter_name || '');
                
                // 드래그 중 스타일
                this.classList.add('opacity-50');
                contentsState.draggedContent = content;
            }
        });
        
        item.addEventListener('dragend', function(e) {
            this.classList.remove('opacity-50');
            contentsState.draggedContent = null;
        });
    });
}

// 콘텐츠 미리보기
window.previewContent = async function(contentId) {
    try {
        const response = await fetch(`/teacher/api/contents/${contentId}/preview/`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            showContentPreviewModal(data);
        } else {
            throw new Error('콘텐츠를 불러올 수 없습니다.');
        }
    } catch (error) {
        window.showMessage(error.message, 'error');
    }
};

// 콘텐츠 미리보기 모달
function showContentPreviewModal(content) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div class="p-6 border-b border-gray-200">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="text-xl font-semibold text-gray-800">${escapeHtml(content.title)}</h3>
                        <div class="flex items-center mt-2 space-x-2">
                            <span class="content-type-badge ${getContentTypeBadgeClass(content.content_type_display)}">
                                ${escapeHtml(content.content_type_display || content.content_type)}
                            </span>
                            ${content.difficulty ? `
                                <span class="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs">
                                    ${escapeHtml(content.difficulty)}
                                </span>
                            ` : ''}
                            ${content.estimated_time ? `
                                <span class="text-gray-600 text-sm">
                                    <i class="fas fa-clock mr-1"></i>${content.estimated_time}분
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    <button onclick="this.closest('.fixed').remove()" 
                            class="text-gray-500 hover:text-gray-700 p-2">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
            </div>
            
            <div class="p-6 overflow-y-auto" style="max-height: calc(90vh - 200px);">
                <div class="prose max-w-none">
                    ${content.page || content.content || '<p class="text-gray-500">내용이 없습니다.</p>'}
                </div>
                
                ${content.answer ? `
                    <div class="mt-6 pt-6 border-t border-gray-200">
                        <h4 class="font-semibold text-gray-700 mb-2">
                            <i class="fas fa-check-circle text-green-600 mr-1"></i>정답
                        </h4>
                        <div class="bg-green-50 p-4 rounded-lg border border-green-200">
                            <div class="text-green-700">${escapeHtml(content.answer)}</div>
                        </div>
                    </div>
                ` : ''}
                
                ${content.tags && Object.keys(content.tags).length > 0 ? `
                    <div class="mt-6 pt-6 border-t border-gray-200">
                        <h4 class="font-semibold text-gray-700 mb-2">
                            <i class="fas fa-tags text-blue-600 mr-1"></i>태그
                        </h4>
                        <div class="flex flex-wrap gap-2">
                            ${Object.entries(content.tags).map(([key, value]) => `
                                <span class="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm border border-blue-200">
                                    ${escapeHtml(key)}: ${escapeHtml(value)}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
            
            <div class="p-6 border-t border-gray-200 flex justify-between items-center">
                <div class="text-sm text-gray-500">
                    ${content.created_at ? `생성일: ${formatDate(content.created_at)}` : ''}
                </div>
                <div class="flex space-x-3">
                    <button onclick="this.closest('.fixed').remove()" 
                            class="btn-modern btn-secondary">
                        닫기
                    </button>
                    <button onclick="addContentToDropZone(${content.id}); this.closest('.fixed').remove();" 
                            class="btn-modern btn-primary">
                        <i class="fas fa-plus mr-2"></i>추가
                    </button>
                    ${content.id ? `
                        <a href="/teacher/contents/${content.id}/edit/" 
                           target="_blank"
                           class="btn-modern btn-secondary">
                            <i class="fas fa-edit mr-2"></i>수정
                        </a>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 모달 외부 클릭 시 닫기
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // ESC 키로 닫기
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
}

// 드롭존에 콘텐츠 추가
window.addContentToDropZone = function(contentId) {
    const content = contentsState.searchResults.find(c => c.id == contentId);
    if (content) {
        window.addDroppedContent({
            id: content.id,
            title: content.title,
            type: content.content_type_display || content.content_type,
            chapter: content.chapter_name || '',
            subchapter: content.subchapter_name || ''
        });
    }
};

// 검색 엔터키 처리
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('contentSearchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                window.searchContents();
            }
        });
        
        // 실시간 검색 (디바운스)
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 2 || this.value.length === 0) {
                    window.searchContents();
                }
            }, 500);
        });
    }
    
    // 필터 변경 시 자동 검색
    const filters = ['contentTypeFilter', 'chapterFilter', 'subchapterFilter'];
    filters.forEach(filterId => {
        const filter = document.getElementById(filterId);
        if (filter) {
            filter.addEventListener('change', function() {
                // 검색어가 있거나 다른 필터가 설정된 경우에만 자동 검색
                const searchInput = document.getElementById('contentSearchInput');
                if (searchInput && (searchInput.value || this.value)) {
                    window.searchContents();
                }
            });
        }
    });
});