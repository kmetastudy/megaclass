// /static/js/teacher/course/contents_panel.js

window.ContentsPanel = {
    currentTab: 'search',
    searchResults: [],
    
    // 패널 토글
    toggle: function() {
        const mainContainer = document.querySelector('.main-container');
        const contentsPanel = document.getElementById('contentsPanel');
        const treePanel = document.getElementById('treePanel');
        const icon = document.getElementById('contentsPanelToggle');
        
        window.contentsPanelOpen = !window.contentsPanelOpen;
        
        if (window.contentsPanelOpen) {
            mainContainer.classList.add('contents-open');
            contentsPanel.classList.remove('collapsed');
            treePanel.classList.add('collapsed');
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-left');
            
            // 초기 로드
            this.loadChapterOptions();
        } else {
            mainContainer.classList.remove('contents-open');
            contentsPanel.classList.add('collapsed');
            treePanel.classList.remove('collapsed');
            icon.classList.remove('fa-chevron-left');
            icon.classList.add('fa-chevron-right');
        }
    },
    
    // 탭 전환
    switchTab: function(tabName) {
        this.currentTab = tabName;
        
        // 탭 버튼 활성화
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.closest('.tab-button').classList.add('active');
        
        // 탭 콘텐츠 전환
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}Tab`).classList.add('active');
    },
    
    // 대단원 옵션 로드
    loadChapterOptions: async function() {
        try {
            const data = await apiRequest(`/teacher/api/course/${window.courseConfig.courseId}/detail/`);
            const chapterSelect = document.getElementById('chapterFilter');
            
            chapterSelect.innerHTML = '<option value="">모든 대단원</option>';
            
            if (data.chapters) {
                data.chapters.forEach(chapter => {
                    chapterSelect.innerHTML += `
                        <option value="${chapter.id}">${chapter.order}. ${chapter.title}</option>
                    `;
                });
            }
        } catch (error) {
            console.error('대단원 로드 실패:', error);
        }
    },
    
    // 소단원 옵션 로드
    loadSubchapterOptions: async function(chapterId) {
        const subchapterSelect = document.getElementById('subchapterFilter');
        
        if (!chapterId) {
            subchapterSelect.innerHTML = '<option value="">모든 소단원</option>';
            return;
        }
        
        try {
            const data = await apiRequest(`/teacher/api/chapter/${chapterId}/detail/`);
            
            subchapterSelect.innerHTML = '<option value="">모든 소단원</option>';
            
            if (data.subchapters) {
                data.subchapters.forEach(sub => {
                    subchapterSelect.innerHTML += `
                        <option value="${sub.id}">${sub.order}. ${sub.title}</option>
                    `;
                });
            }
        } catch (error) {
            console.error('소단원 로드 실패:', error);
        }
    },
    
    // 콘텐츠 검색
    search: async function() {
        const searchInput = document.getElementById('contentSearchInput').value;
        const contentType = document.getElementById('contentTypeFilter').value;
        const chapter = document.getElementById('chapterFilter').value;
        const subchapter = document.getElementById('subchapterFilter').value;
        
        const params = new URLSearchParams({
            q: searchInput,
            content_type: contentType,
            chapter: chapter,
            subchapter: subchapter
        });
        
        try {
            const response = await fetch(`${window.courseConfig.urls.contentsSearch}?${params}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            this.displaySearchResults(data.results || []);
            
        } catch (error) {
            showError('콘텐츠 검색 중 오류가 발생했습니다.');
        }
    },
    
    // 검색 결과 표시
    displaySearchResults: function(results) {
        const listContainer = document.getElementById('contentsList');
        
        if (results.length === 0) {
            listContainer.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-inbox text-4xl mb-2"></i>
                    <p>검색 결과가 없습니다</p>
                </div>
            `;
            return;
        }
        
        listContainer.innerHTML = results.map(content => `
            <div class="content-item" 
                 draggable="true"
                 data-content-id="${content.id}"
                 data-content-title="${escapeHtml(content.title)}"
                 data-content-type="${escapeHtml(content.content_type)}">
                <h6 class="font-semibold text-gray-800 mb-1">${escapeHtml(content.title)}</h6>
                <div class="flex items-center justify-between text-sm">
                    <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        ${escapeHtml(content.content_type)}
                    </span>
                    <span class="text-gray-500">${content.created_at}</span>
                </div>
                ${content.preview ? `
                    <p class="text-xs text-gray-600 mt-2 line-clamp-2">${escapeHtml(content.preview)}</p>
                ` : ''}
                <button onclick="ContentsPanel.addToCurrentChasi(${content.id})" 
                        class="mt-2 text-xs text-blue-600 hover:text-blue-800">
                    <i class="fas fa-plus mr-1"></i>현재 차시에 추가
                </button>
            </div>
        `).join('');
        
        // 드래그 이벤트 설정
        this.initializeDragAndDrop();
    },
    
    // 드래그 앤 드롭 초기화
    initializeDragAndDrop: function() {
        const contentItems = document.querySelectorAll('.content-item[draggable="true"]');
        
        contentItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.effectAllowed = 'copy';
                e.dataTransfer.setData('contentId', item.dataset.contentId);
                e.dataTransfer.setData('contentTitle', item.dataset.contentTitle);
                e.dataTransfer.setData('contentType', item.dataset.contentType);
                item.classList.add('dragging');
            });
            
            item.addEventListener('dragend', (e) => {
                item.classList.remove('dragging');
            });
        });
    },
    
    // 현재 차시에 콘텐츠 추가
    addToCurrentChasi: async function(contentId) {
        if (!window.currentNode || window.currentNode.data.type !== 'chasi') {
            showError('차시를 먼저 선택해주세요.');
            return;
        }
        
        const chasiId = window.currentNode.data.id;
        
        try {
            const formData = new FormData();
            formData.append('content_id', contentId);
            formData.append('slide_title', '');
            formData.append('estimated_time', '5');
            
            const response = await submitForm(`/teacher/api/chasis/${chasiId}/slides/add/`, formData);
            
            if (response.success) {
                showSuccess('슬라이드가 추가되었습니다.');
                
                // 슬라이드 목록 새로고침
                if (window.SlideManager) {
                    window.SlideManager.loadSlides(chasiId);
                }
                
                // 트리 새로고침
                refreshTree();
            }
        } catch (error) {
            showError('슬라이드 추가 중 오류가 발생했습니다.');
        }
    },
    
    // 빠른 콘텐츠 생성
    createQuickContent: async function(formData) {
        try {
            // meta_data와 tags 기본값 설정
            formData.append('meta_data', JSON.stringify({
                created_from: 'onepage_panel',
                course_id: window.courseConfig.courseId
            }));
            formData.append('tags', '{}');
            
            const response = await submitForm('/teacher/contents/create/', formData);
            
            if (response.success) {
                showSuccess('콘텐츠가 생성되었습니다.');
                
                // 폼 초기화
                document.getElementById('quickContentForm').reset();
                
                // 검색 탭으로 전환하고 새로고침
                this.switchTab('search');
                this.search();
            }
        } catch (error) {
            showError('콘텐츠 생성 중 오류가 발생했습니다.');
        }
    }
};

// 전역 함수로 노출
window.toggleContentsPanel = function() {
    ContentsPanel.toggle();
};

window.switchTab = function(tabName) {
    ContentsPanel.switchTab(tabName);
};

window.searchContents = function() {
    ContentsPanel.search();
};

// 이벤트 리스너
document.addEventListener('DOMContentLoaded', function() {
    // 대단원 선택 시 소단원 로드
    const chapterFilter = document.getElementById('chapterFilter');
    if (chapterFilter) {
        chapterFilter.addEventListener('change', function() {
            ContentsPanel.loadSubchapterOptions(this.value);
        });
    }
    
    // 검색 입력 엔터키
    const searchInput = document.getElementById('contentSearchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                ContentsPanel.search();
            }
        });
    }
    
    // 빠른 콘텐츠 생성 폼
    const quickForm = document.getElementById('quickContentForm');
    if (quickForm) {
        quickForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            ContentsPanel.createQuickContent(formData);
        });
    }
});