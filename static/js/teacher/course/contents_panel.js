// contents_panel.js
// 콘텐츠 라이브러리 패널 관리
// 선택된 콘텐츠 ID들을 저장할 전역 변수 추가
// window.selectedContentIds = new Set();

// 탭 전환
function switchTab(tabName) {
    // 모든 탭 버튼과 컨텐츠 비활성화
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // 선택된 탭 활성화
    event.target.closest('.tab-button').classList.add('active');
    document.getElementById(tabName + 'Tab').classList.add('active');
}

// 콘텐츠 검색
async function searchContents() {
    const searchInput = document.getElementById('contentSearchInput').value;
    const typeFilter = document.getElementById('contentTypeFilter').value;
    const chapterFilter = document.getElementById('chapterFilter').value;
    const subchapterFilter = document.getElementById('subchapterFilter').value;
    
    const params = new URLSearchParams({
        q: searchInput,
        content_type: typeFilter,
        chapter: chapterFilter,
        subchapter: subchapterFilter,
        course_id: window.courseConfig.courseId
    });
    
    try {
        showLoadingInContentsList();
        
        const response = await fetch(`${window.courseConfig.urls.contentsSearch}?${params}`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displaySearchResults(data.results);
        } else {
            throw new Error('검색 중 오류가 발생했습니다.');
        }
    } catch (error) {
        showMessage(error.message, 'error');
        displaySearchError();
    }
}

// 검색 결과 표시
// 검색 결과 표시 함수 수정
function displaySearchResults(results) {
    const contentsList = document.getElementById('contentsList');
    
    if (results.length === 0) {
        contentsList.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-search text-4xl mb-2"></i>
                <p>검색 결과가 없습니다</p>
            </div>
        `;
        return;
    }
    
    contentsList.innerHTML = results.map(content => {
        const isSelected = window.selectedContentIds.has(content.id);
        const contentItem = `
            <div class="content-item-wrapper content-item ${isSelected ? 'selected' : ''}" 
                 data-content-id="${content.id}" 
                 draggable="true">
                <div class="content-search-item">
                    <div class="content-item-header">
                        <h4 class="content-item-title">${content.title}</h4>
                        <span class="content-type-badge ${getContentTypeBadgeClass(content.content_type)}">
                            ${content.content_type_display}
                        </span>
                    </div>
                    <div class="content-item-meta">
                        <span><i class="fas fa-book mr-1"></i>${content.chapter_name || '미분류'}</span>
                        ${content.subchapter_name ? `<span><i class="fas fa-bookmark mr-1"></i>${content.subchapter_name}</span>` : ''}
                    </div>
                    <div class="content-item-actions">
                        <button onclick="toggleContentSelection(${content.id})" 
                                class="btn-icon ${isSelected ? 'active' : ''}" 
                                title="선택">
                            <i class="fas ${isSelected ? 'fa-check-square' : 'fa-square'}"></i>
                        </button>
                        <button onclick="previewContent(${content.id})" 
                                class="btn-icon" 
                                title="미리보기">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        return contentItem;
    }).join('');
    
    // 각 콘텐츠 아이템을 드래그 가능하게 만들기
    setTimeout(() => {
        results.forEach(content => {
            const element = document.querySelector(`[data-content-id="${content.id}"]`);
            if (element) {
                // 클릭 이벤트 추가 (선택 토글)
                element.addEventListener('click', function(e) {
                    // 버튼 클릭이 아닌 경우에만 토글
                    if (!e.target.closest('button')) {
                        toggleContentSelection(content.id);
                    }
                });
                
                // 드래그 기능 추가
                makeContentItemDraggable(element, {
                    id: content.id,
                    title: content.title,
                    type: content.content_type_display,
                    chapter: content.chapter_name,
                    subchapter: content.subchapter_name
                });
            }
        });
    }, 100);
}
// contents_panel.js
// 전역 selectedContentIds 제거하고 ContentSelectionManager 사용
// window.selectedContentIds = new Set(); // 제거
// contents_panel.js의 toggleContentSelection 함수를 다음과 같이 수정

window.toggleContentSelection = function(contentId) {
    console.log('=== toggleContentSelection 시작 ===');
    console.log('contentId:', contentId);
    
    const element = document.querySelector(`[data-content-id="${contentId}"]`);
    if (!element) {
        console.error('Element not found for contentId:', contentId);
        return;
    }
    console.log('Element 찾음:', element);
    
    const checkIcon = element.querySelector('.content-item-actions button:first-child i');
    const checkButton = element.querySelector('.content-item-actions button:first-child');
    console.log('checkIcon:', checkIcon, 'checkButton:', checkButton);
    
    // ContentSelectionManager 사용 (library 컨텍스트)
    const isSelected = window.ContentSelectionManager.toggle(contentId, 'library');
    console.log('토글 후 선택 상태:', isSelected);
    
    // UI 업데이트
    if (isSelected) {
        console.log('콘텐츠 선택됨 - UI 업데이트 시작');
        element.classList.add('selected');
        checkIcon.classList.remove('fa-square');
        checkIcon.classList.add('fa-check-square');
        checkButton.classList.add('active');
        
        // 현재 노드 정보 확인
        console.log('currentActiveNodeId:', window.currentActiveNodeId);
        console.log('currentNode:', window.currentNode);
        
        // 선택된 콘텐츠를 상단으로 이동 (슬라이드 관리 화면에서만)
        // 조건문 수정: currentActiveNodeId는 체크하지 않음
        if (window.currentNode && window.currentNode.data) {
            const nodeType = window.currentNode.data.type;
            console.log('현재 노드 타입:', nodeType);
            
            if (nodeType === 'chasi') {
                const chasiId = window.currentNode.data.id;
                console.log('차시 ID:', chasiId);
                console.log('fetchContentAndMoveToTop 호출');
                
                // 서버에서 콘텐츠 정보 가져오기
                fetchContentAndMoveToTop(chasiId, contentId);
            } else {
                console.log('현재 노드가 차시가 아님:', nodeType);
            }
        } else {
            console.log('currentNode 정보 없음');
        }
    } else {
        console.log('콘텐츠 선택 해제됨 - UI 업데이트');
        element.classList.remove('selected');
        checkIcon.classList.remove('fa-check-square');
        checkIcon.classList.add('fa-square');
        checkButton.classList.remove('active');
    }
    
    updateSelectedCount('library');
    console.log('=== toggleContentSelection 종료 ===');
}

// 콘텐츠 정보를 가져와서 상단으로 이동하는 함수
async function fetchContentAndMoveToTop(chasiId, contentId) {
    console.log('=== fetchContentAndMoveToTop 시작 ===');
    console.log('chasiId:', chasiId, 'contentId:', contentId);
    
    try {
        const url = `/teacher/api/contents/${contentId}/detail/`;
        console.log('API 호출 URL:', url);
        
        const response = await fetch(url, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        console.log('API 응답 상태:', response.status, response.statusText);
        
        if (response.ok) {
            const data = await response.json();
            console.log('API 응답 데이터:', data);
            
            if (data.success) {
                console.log('콘텐츠 데이터 받음:', data.content);
                
                // SlideManager의 콘텐츠 리스트에 추가/이동
                if (window.SlideManager) {
                    console.log('SlideManager 존재함');
                    
                    // 현재 차시의 콘텐츠 리스트 컨테이너 확인
                    const container = document.getElementById(`content-list-${chasiId}`);
                    console.log('콘텐츠 리스트 컨테이너:', container);
                    
                    if (container) {
                        // 해당 콘텐츠가 이미 리스트에 있는지 확인
                        let contentElement = container.querySelector(`[data-content-id="${contentId}"]`);
                        console.log('기존 콘텐츠 엘리먼트:', contentElement);
                        
                        if (!contentElement) {
                            console.log('콘텐츠가 리스트에 없음 - 새로 생성');
                            // 없으면 새로 생성
                            contentElement = createContentElement(chasiId, data.content);
                            container.insertBefore(contentElement, container.firstChild);
                            console.log('새 콘텐츠 엘리먼트 추가 완료');
                        } else {
                            console.log('콘텐츠가 이미 리스트에 있음 - 상단으로 이동');
                            // 있으면 맨 위로 이동
                            if (window.SlideManager.moveContentToTop) {
                                window.SlideManager.moveContentToTop(chasiId, contentId);
                            } else {
                                console.warn('SlideManager.moveContentToTop 함수가 없음');
                                // 직접 이동
                                container.insertBefore(contentElement, container.firstChild);
                            }
                        }
                    } else {
                        console.error('콘텐츠 리스트 컨테이너를 찾을 수 없음');
                    }
                } else {
                    console.error('SlideManager가 없음');
                }
            } else {
                console.error('API 응답 success가 false:', data);
            }
        } else {
            console.error('API 응답 오류:', response.status);
        }
    } catch (error) {
        console.error('fetchContentAndMoveToTop 에러:', error);
        console.error('에러 스택:', error.stack);
    }
    
    console.log('=== fetchContentAndMoveToTop 종료 ===');
}

// 콘텐츠 엘리먼트 생성 함수
// 콘텐츠 엘리먼트 생성 함수
function createContentElement(chasiId, content) {
    console.log('=== createContentElement 시작 ===');
    console.log('chasiId:', chasiId);
    console.log('content:', content);
    
    const div = document.createElement('div');
    // selected와 bg-purple-50 클래스 제거 (선택 상태는 나중에 추가)
    div.className = 'content-item p-3 border-b border-gray-200 last:border-b-0 hover:bg-gray-50 cursor-pointer';
    div.setAttribute('onclick', `SlideManager.selectContent(${chasiId}, ${content.id}, '${escapeHtml(content.title)}')`);
    div.setAttribute('data-content-id', content.id);
    // draggable 속성 추가
    div.setAttribute('draggable', 'true');
    
    const html = `
        <div class="flex items-center justify-between">
            <div class="flex-1">
                <h6 class="font-medium text-gray-800">${escapeHtml(content.title)}</h6>
                <div class="flex items-center space-x-2 mt-1">
                    <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        ${escapeHtml(content.content_type)}
                    </span>
                    <span class="text-gray-500 text-xs">${content.created_at}</span>
                </div>
                ${content.preview ? `<p class="text-sm text-gray-600 mt-1">${escapeHtml(content.preview)}</p>` : ''}
            </div>
            <div class="flex items-center space-x-2">
                <input type="radio" name="content_id_${chasiId}" value="${content.id}" 
                       class="h-4 w-4 text-purple-600">
            </div>
        </div>
    `;
    
    console.log('생성할 HTML:', html);
    div.innerHTML = html;
    
    // 선택된 상태로 표시하려면 여기에 추가
    div.classList.add('selected', 'bg-purple-50');
    
    console.log('=== createContentElement 종료 ===');
    return div;
}
function createContentElement_0622(chasiId, content) {
    console.log('=== createContentElement 시작 ===');
    console.log('chasiId:', chasiId);
    console.log('content:', content);
    
    const div = document.createElement('div');
    div.className = 'content-item p-3 border-b border-gray-200 last:border-b-0 hover:bg-gray-50 cursor-pointer selected bg-purple-50';
    div.setAttribute('onclick', `SlideManager.selectContent(${chasiId}, ${content.id}, '${escapeHtml(content.title)}')`);
    div.setAttribute('data-content-id', content.id);
    
    const html = `
        <div class="flex items-center justify-between">
            <div class="flex-1">
                <h6 class="font-medium text-gray-800">${escapeHtml(content.title)}</h6>
                <div class="flex items-center space-x-2 mt-1">
                    <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        ${escapeHtml(content.content_type)}
                    </span>
                    <span class="text-gray-500 text-xs">${content.created_at}</span>
                </div>
                ${content.preview ? `<p class="text-sm text-gray-600 mt-1">${escapeHtml(content.preview)}</p>` : ''}
            </div>
            <div class="flex items-center space-x-2">
                <input type="radio" name="content_id_${chasiId}" value="${content.id}" 
                       class="h-4 w-4 text-purple-600">
            </div>
        </div>
    `;
    
    console.log('생성할 HTML:', html);
    div.innerHTML = html;
    
    console.log('=== createContentElement 종료 ===');
    return div;
}
window.toggleContentSelection_0622 = function(contentId) {
    console.log('Library panel - Toggle selection:', contentId);
    
    const element = document.querySelector(`[data-content-id="${contentId}"]`);
    if (!element) {
        console.error('Element not found for contentId:', contentId);
        return;
    }
    
    const checkIcon = element.querySelector('.content-item-actions button:first-child i');
    const checkButton = element.querySelector('.content-item-actions button:first-child');
    
    // ContentSelectionManager 사용 (library 컨텍스트)
    const isSelected = window.ContentSelectionManager.toggle(contentId, 'library');
    
    // UI 업데이트
    if (isSelected) {
        element.classList.add('selected');
        checkIcon.classList.remove('fa-square');
        checkIcon.classList.add('fa-check-square');
        checkButton.classList.add('active');
    } else {
        element.classList.remove('selected');
        checkIcon.classList.remove('fa-check-square');
        checkIcon.classList.add('fa-square');
        checkButton.classList.remove('active');
    }
    
    updateSelectedCount('library');
}

// 선택 개수 업데이트 (컨텍스트 추가)
function updateSelectedCount(context = 'library') {
    const count = window.ContentSelectionManager.getCount(context);
    const bulkActions = document.getElementById('bulkActions');
    let countDisplay = document.getElementById('selectedCountDisplay');
    
    if (!countDisplay) {
        const searchTab = document.getElementById('searchTab');
        const countHtml = `
            <div id="selectedCountDisplay" class="px-4 py-2 bg-blue-50 text-blue-700 text-sm ${count === 0 ? 'hidden' : ''}">
                <i class="fas fa-check-circle mr-1"></i>
                <span id="selectedCountText">${count}개 선택됨</span>
                <button onclick="clearAllSelections('library')" class="ml-2 text-blue-600 hover:text-blue-800">
                    <i class="fas fa-times"></i> 전체 해제
                </button>
            </div>
        `;
        searchTab.insertAdjacentHTML('afterbegin', countHtml);
        countDisplay = document.getElementById('selectedCountDisplay');
    }
    
    if (count > 0) {
        countDisplay.classList.remove('hidden');
        document.getElementById('selectedCountText').textContent = `${count}개 선택됨`;
    } else {
        countDisplay.classList.add('hidden');
    }

    if (bulkActions) {
        bulkActions.style.display = count > 0 ? 'flex' : 'none';
    }
}

// 전체 선택 해제
window.clearAllSelections = function(context = 'library') {
    window.ContentSelectionManager.clearAll(context);
    
    // UI 초기화
    document.querySelectorAll('.content-item.selected').forEach(element => {
        element.classList.remove('selected');
        const checkIcon = element.querySelector('.content-item-actions button:first-child i');
        const checkButton = element.querySelector('.content-item-actions button:first-child');
        if (checkIcon) {
            checkIcon.classList.remove('fa-check-square');
            checkIcon.classList.add('fa-square');
        }
        if (checkButton) {
            checkButton.classList.remove('active');
        }
    });
    
    updateSelectedCount(context);
}

// 선택된 콘텐츠 추가 함수 수정
window.addSelectedContentsToDropZone = function() {
    const selectedIds = window.ContentSelectionManager.getSelection('library');
    
    if (selectedIds.size === 0) {
        showMessage('선택된 콘텐츠가 없습니다.', 'warning');
        return;
    }
    
    selectedIds.forEach(contentId => {
        const element = document.querySelector(`[data-content-id="${contentId}"]`);
        if (element) {
            const title = element.querySelector('.content-item-title').textContent;
            const type = element.querySelector('.content-type-badge').textContent.trim();
            const chapter = element.querySelector('.content-item-meta span:first-child').textContent.replace(/^.*?\s/, '');
            const subchapter = element.querySelector('.content-item-meta span:last-child')?.textContent.replace(/^.*?\s/, '') || '';
            
            addDroppedContent({
                id: contentId,
                title: title,
                type: type,
                chapter: chapter,
                subchapter: subchapter
            });
        }
    });
    
    showMessage(`${selectedIds.size}개의 콘텐츠가 추가되었습니다.`, 'success');
    clearAllSelections('library');
}

// 검색 결과 표시 함수에서 선택 상태 확인
function displaySearchResults(results) {
    const contentsList = document.getElementById('contentsList');
    
    if (results.length === 0) {
        contentsList.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-search text-4xl mb-2"></i>
                <p>검색 결과가 없습니다</p>
            </div>
        `;
        return;
    }
    
    contentsList.innerHTML = results.map(content => {
        // ContentSelectionManager에서 선택 상태 확인
        const isSelected = window.ContentSelectionManager.isSelected(content.id, 'library');
        
        const contentItem = `
            <div class="content-item-wrapper content-item ${isSelected ? 'selected' : ''}" 
                 data-content-id="${content.id}" 
                 draggable="true">
                <div class="content-search-item">
                    <div class="content-item-header">
                        <h4 class="content-item-title">${content.title}</h4>
                        <span class="content-type-badge ${getContentTypeBadgeClass(content.content_type)}">
                            ${content.content_type_display}
                        </span>
                    </div>
                    <div class="content-item-meta">
                        <span><i class="fas fa-book mr-1"></i>${content.chapter_name || '미분류'}</span>
                        ${content.subchapter_name ? `<span><i class="fas fa-bookmark mr-1"></i>${content.subchapter_name}</span>` : ''}
                    </div>
                    <div class="content-item-actions">
                        <button onclick="toggleContentSelection(${content.id})" 
                                class="btn-icon ${isSelected ? 'active' : ''}" 
                                title="선택">
                            <i class="fas ${isSelected ? 'fa-check-square' : 'fa-square'}"></i>
                        </button>
                        <button onclick="previewContent(${content.id})" 
                                class="btn-icon" 
                                title="미리보기">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        return contentItem;
    }).join('');
    
    // 드래그 기능 추가
    setTimeout(() => {
        results.forEach(content => {
            const element = document.querySelector(`[data-content-id="${content.id}"]`);
            if (element) {
                // 클릭 이벤트 추가
                element.addEventListener('click', function(e) {
                    if (!e.target.closest('button')) {
                        toggleContentSelection(content.id);
                    }
                });
                
                // 드래그 기능
                makeContentItemDraggable(element, {
                    id: content.id,
                    title: content.title,
                    type: content.content_type_display,
                    chapter: content.chapter_name,
                    subchapter: content.subchapter_name
                });
            }
        });
    }, 100);
}

function displaySearchResults_0621(results) {
    const contentsList = document.getElementById('contentsList');
    
    if (results.length === 0) {
        contentsList.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-search text-4xl mb-2"></i>
                <p>검색 결과가 없습니다</p>
            </div>
        `;
        return;
    }
    
    contentsList.innerHTML = results.map(content => {
        const contentItem = `
            <div class="content-item-wrapper" data-content-id="${content.id}">
                <div class="content-search-item">
                    <div class="content-item-header">
                        <h4 class="content-item-title">${content.title}</h4>
                        <span class="content-type-badge ${getContentTypeBadgeClass(content.content_type)}">
                            ${content.content_type_display}
                        </span>
                    </div>
                    <div class="content-item-meta">
                        <span><i class="fas fa-book mr-1"></i>${content.chapter_name || '미분류'}</span>
                        ${content.subchapter_name ? `<span><i class="fas fa-bookmark mr-1"></i>${content.subchapter_name}</span>` : ''}
                    </div>
                    <div class="content-item-actions">
                        <button onclick="previewContent(${content.id})" class="btn-icon" title="미리보기">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        return contentItem;
    }).join('');
    
    // 각 콘텐츠 아이템을 드래그 가능하게 만들기
    setTimeout(() => {
        results.forEach(content => {
            const element = document.querySelector(`[data-content-id="${content.id}"]`);
            if (element) {
                makeContentItemDraggable(element, {
                    id: content.id,
                    title: content.title,
                    type: content.content_type_display,
                    chapter: content.chapter_name,
                    subchapter: content.subchapter_name
                });
            }
        });
    }, 100);
}

// 콘텐츠 타입별 배지 클래스
function getContentTypeBadgeClass(type) {
    const badgeClasses = {
        'multiple_choice': 'badge-blue',
        'short_answer': 'badge-green',
        'essay': 'badge-purple',
        'presentation': 'badge-orange'
    };
    return badgeClasses[type] || 'badge-gray';
}

// 로딩 표시
function showLoadingInContentsList() {
    const contentsList = document.getElementById('contentsList');
    contentsList.innerHTML = `
        <div class="text-center py-8">
            <div class="loading-spinner mx-auto mb-4"></div>
            <p class="text-gray-600">검색 중...</p>
        </div>
    `;
}

// 검색 오류 표시
function displaySearchError() {
    const contentsList = document.getElementById('contentsList');
    contentsList.innerHTML = `
        <div class="text-center py-8 text-red-500">
            <i class="fas fa-exclamation-circle text-4xl mb-2"></i>
            <p>검색 중 오류가 발생했습니다</p>
        </div>
    `;
}

// 전체 선택 해제 함수
window.clearAllSelections = function() {
    window.selectedContentIds.forEach(contentId => {
        const element = document.querySelector(`[data-content-id="${contentId}"]`);
        if (element) {
            element.classList.remove('selected');
            const checkIcon = element.querySelector('.content-item-actions button:first-child i');
            const checkButton = element.querySelector('.content-item-actions button:first-child');
            checkIcon.classList.remove('fa-check-square');
            checkIcon.classList.add('fa-square');
            checkButton.classList.remove('active');
        }
    });
    window.selectedContentIds.clear();
    updateSelectedCount();
}

// 선택된 콘텐츠들을 한번에 드롭 영역에 추가하는 함수
window.addSelectedContentsToDropZone_0621 = function() {
    if (window.selectedContentIds.size === 0) {
        showMessage('선택된 콘텐츠가 없습니다.', 'warning');
        return;
    }
    
    window.selectedContentIds.forEach(contentId => {
        const element = document.querySelector(`[data-content-id="${contentId}"]`);
        if (element) {
            const title = element.querySelector('.content-item-title').textContent;
            const type = element.querySelector('.content-type-badge').textContent.trim();
            const chapter = element.querySelector('.content-item-meta span:first-child').textContent.replace(/^.*?\s/, '');
            const subchapter = element.querySelector('.content-item-meta span:last-child')?.textContent.replace(/^.*?\s/, '') || '';
            
            addDroppedContent({
                id: contentId,
                title: title,
                type: type,
                chapter: chapter,
                subchapter: subchapter
            });
        }
    });
    
    // 선택 해제
    clearAllSelections();
    showMessage(`${window.selectedContentIds.size}개의 콘텐츠가 추가되었습니다.`, 'success');
}

// 검색 필터 아래에 다중 작업 버튼 추가
function addBulkActionButtons() {
    const filterContainer = document.querySelector('.contents-filters');
    if (!document.getElementById('bulkActions')) {
        const bulkActionsHtml = `
            <div id="bulkActions" class="bulk-actions hidden">
                <button onclick="addSelectedContentsToDropZone()" 
                        class="btn-modern btn-primary flex-1">
                    <i class="fas fa-plus mr-2"></i>선택 항목 추가
                </button>
                <button onclick="clearAllSelections()" 
                        class="btn-modern btn-secondary">
                    <i class="fas fa-times mr-2"></i>선택 해제
                </button>
            </div>
        `;
        filterContainer.insertAdjacentHTML('afterend', bulkActionsHtml);
    }
}


// 콘텐츠 미리보기
async function previewContent(contentId) {
    try {
        const response = await fetch(`/teacher/api/contents/${contentId}/preview/`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            showContentPreview(data);
        } else {
            throw new Error('콘텐츠를 불러올 수 없습니다.');
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// 콘텐츠 미리보기 모달 표시
function showContentPreview(content) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl max-w-3xl max-h-screen overflow-hidden">
            <div class="p-6">
                <div class="flex justify-between items-start mb-4">
                    <h3 class="text-xl font-semibold">${content.title}</h3>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
                <div class="content-preview max-h-96 overflow-y-auto">
                    ${content.page}
                    ${content.answer ? `<div class="mt-4 p-4 bg-green-50 rounded"><strong>정답:</strong> ${content.answer}</div>` : ''}
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
}

// 빠른 콘텐츠 생성 폼 제출
// document.getElementById('quickContentForm')?.addEventListener('submit', async (e) => {
//     e.preventDefault();
    
//     const formData = new FormData(e.target);
//     const data = Object.fromEntries(formData);
    
//     try {
//         const response = await fetch('/teacher/api/contents/quick-create/', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//                 'X-CSRFToken': window.courseConfig.csrfToken
//             },
//             body: JSON.stringify({
//                 ...data,
//                 course_id: window.courseConfig.courseId,
//                 chapter_id: window.currentNode?.data?.chapter_id,
//                 subchapter_id: window.currentNode?.data?.subchapter_id
//             })
//         });
        
//         if (response.ok) {
//             const result = await response.json();
//             showMessage('콘텐츠가 생성되었습니다.', 'success');
//             e.target.reset();
            
//             // 생성된 콘텐츠를 자동으로 드롭 영역에 추가
//             if (result.content) {
//                 addDroppedContent({
//                     id: result.content.id,
//                     title: result.content.title,
//                     type: result.content.content_type_display,
//                     chapter: result.content.chapter_name,
//                     subchapter: result.content.subchapter_name
//                 });
//             }
//         } else {
//             const error = await response.json();
//             throw new Error(error.message || '콘텐츠 생성에 실패했습니다.');
//         }
//     } catch (error) {
//         showMessage(error.message, 'error');
//     }
// });
// API 일관성 개선 후 - updateSubchapterFilter 함수 (최종 버전)

// contents_panel.js의 initChapterFilters 함수를 다음으로 교체하세요

// 대단원 필터 초기화 - 수정된 버전
async function initChapterFilters() {
    try {
        const response = await fetch(`/teacher/api/courses/${window.courseConfig.courseId}/chapters/`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();  // 전체 응답 객체
            const chapterFilter = document.getElementById('chapterFilter');
            
            if (chapterFilter && data.success && data.chapters) {
                chapterFilter.innerHTML = '<option value="">모든 대단원</option>';
                
                // data.chapters를 사용 (data는 {success: true, chapters: [...]} 형태)
                data.chapters.forEach(chapter => {
                    chapterFilter.innerHTML += `<option value="${chapter.id}">${chapter.chapter_name}</option>`;
                });
                
                // 대단원 변경 시 소단원 필터 업데이트
                chapterFilter.addEventListener('change', () => {
                    updateSubchapterFilter(chapterFilter.value);
                });
            }
        }
    } catch (error) {
        console.error('대단원 필터 초기화 오류:', error);
    }
}


async function updateSubchapterFilter(chapterId) {
    const subchapterFilter = document.getElementById('subchapterFilter');
    
    if (!subchapterFilter) return;
    
    if (!chapterId) {
        subchapterFilter.innerHTML = '<option value="">모든 소단원</option>';
        return;
    }
    
    try {
        const response = await fetch(`/teacher/api/chapters/${chapterId}/subchapters/`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();  // {success: true, subchapters: [...]}
            
            subchapterFilter.innerHTML = '<option value="">모든 소단원</option>';
            
            if (data.success && data.subchapters && Array.isArray(data.subchapters)) {
                data.subchapters.forEach(subchapter => {
                    subchapterFilter.innerHTML += `<option value="${subchapter.id}">${subchapter.subchapter_name}</option>`;
                });
            } else {
                console.error('소단원 데이터를 가져올 수 없습니다:', data);
            }
        }
    } catch (error) {
        console.error('소단원 필터 업데이트 오류:', error);
        subchapterFilter.innerHTML = '<option value="">모든 소단원</option>';
    }
}

// 엔터키로 검색 실행
document.getElementById('contentSearchInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchContents();
    }
});



// contents_panel.js 수정사항

// 콘텐츠 타입 카테고리별 매핑 (실제 데이터는 서버에서 가져와야 함)
const contentTypesByCategory = {
    'multiple_choice': [
        { id: 'multi-choice', name: '객관식' },
        { id: 'multiple-choice', name: '객관식' },
        { id: 'ordering', name: '객관식' }
    ],
    'short_answer': [
        { id: 'multi-input', name: '단답형' },
        { id: 'one_shot_submit', name: '단답형' },
        { id: 'short-answer', name: '단답형' }
    ],
    'essay': [
        { id: 'essay', name: '서술형' }
    ],
    'presentation': [
        { id: 'physical_record', name: '수행평가' },
        { id: 'report', name: '수행평가' },
        { id: 'rolling', name: '수행평가' },
        { id: 'take-action', name: '수행평가' }
    ]
};

// 콘텐츠 타입 카테고리 변경 시
document.getElementById('contentTypeCategoryFilter').addEventListener('change', async function(e) {
    const category = e.target.value;
    const contentTypeFilter = document.getElementById('contentTypeFilter');
    
    // 콘텐츠 타입 필터 초기화
    contentTypeFilter.innerHTML = '<option value="">모든 타입</option>';
    
    if (category) {
        // 서버에서 카테고리별 콘텐츠 타입 가져오기
        try {
            const response = await fetch(`/teacher/api/content-types/by-category/${category}/`, {
                headers: {
                    'X-CSRFToken': window.courseConfig.csrfToken
                }
            });


            
            if (response.ok) {
                const data = await response.json();
                data.content_types.forEach(type => {
                    contentTypeFilter.innerHTML += `<option value="${type.id}">${type.type_name}</option>`;
                });
            } else {
                // 임시로 하드코딩된 데이터 사용
                const types = contentTypesByCategory[category] || [];
                types.forEach(type => {
                    contentTypeFilter.innerHTML += `<option value="${type.id}">${type.name}</option>`;
                });
            }
        } catch (error) {
            console.error('콘텐츠 타입 로드 오류:', error);
        }
    }
});

// 대단원 필터 변경 시 소단원 업데이트
document.getElementById('chapterFilter').addEventListener('change', async function(e) {
    const chapterId = e.target.value;
    await updateSubchapterFilter(chapterId);
});

// 소단원 필터 업데이트 함수 수정
async function updateSubchapterFilter(chapterId) {
    const subchapterFilter = document.getElementById('subchapterFilter');
    
    if (!subchapterFilter) return;
    
    subchapterFilter.innerHTML = '<option value="">모든 소단원</option>';
    
    if (!chapterId) {
        return;
    }
    
    try {
        const response = await fetch(`/teacher/api/chapters/${chapterId}/subchapters/`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success && data.subchapters && Array.isArray(data.subchapters)) {
                data.subchapters.forEach(subchapter => {
                    subchapterFilter.innerHTML += `<option value="${subchapter.id}">${subchapter.subchapter_name || subchapter.sub_chapter_title}</option>`;
                });
            }
        }
    } catch (error) {
        console.error('소단원 필터 업데이트 오류:', error);
    }
}

// 검색 함수 수정
async function searchContents() {
    const searchInput = document.getElementById('contentSearchInput').value;
    const typeFilter = document.getElementById('contentTypeFilter').value;
    const chapterFilter = document.getElementById('chapterFilter').value;
    const subchapterFilter = document.getElementById('subchapterFilter').value;
    
    // 검색 결과 단계 표시 초기화
    const searchingResult = document.getElementById('searching-result');
    searchingResult.innerHTML = '<div class="p-4 bg-gray-100 rounded mb-4"><h5 class="font-semibold mb-2">검색 진행 상황</h5><div id="search-steps"></div></div>';
    
    const params = new URLSearchParams({
        q: searchInput,
        content_type: typeFilter,
        chapter: chapterFilter ? document.querySelector(`#chapterFilter option[value="${chapterFilter}"]`).textContent.replace('모든 대단원', '') : '',
        subchapter: subchapterFilter ? document.querySelector(`#subchapterFilter option[value="${subchapterFilter}"]`).textContent.replace('모든 소단원', '') : '',
        course_id: window.courseConfig.courseId
    });
    
    try {
        showLoadingInContentsList();
        
        const response = await fetch(`${window.courseConfig.urls.contentsSearch}?${params}`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // 검색 단계별 결과 표시
            displaySearchSteps(data);
            
            // 검색 결과 표시
            displaySearchResults(data.results);
        } else {
            throw new Error('검색 중 오류가 발생했습니다.');
        }
    } catch (error) {
        showMessage(error.message, 'error');
        displaySearchError();
    }
}

// 검색 단계별 결과 표시 함수
function displaySearchSteps(data) {
    const stepsContainer = document.getElementById('search-steps');
    if (!stepsContainer) return;
    
    // 서버에서 단계별 정보가 오면 표시 (현재는 시뮬레이션)
    const steps = [
        { step: 1, label: '활성화된 콘텐츠', count: data.total || 0 },
        { step: 2, label: '권한 필터 적용', count: data.total || 0 },
        { step: 3, label: '텍스트 검색', count: data.total || 0 },
        { step: 4, label: '콘텐츠 타입 필터', count: data.total || 0 },
        { step: 5, label: '코스 필터', count: data.total || 0 },
        { step: 6, label: '대단원 필터', count: data.total || 0 }
    ];
    
    let stepsHtml = '<div class="space-y-2">';
    steps.forEach(step => {
        stepsHtml += `
            <div class="flex justify-between text-sm">
                <span class="text-gray-600">[${step.step}단계] ${step.label}:</span>
                <span class="font-semibold">${step.count}개</span>
            </div>
        `;
    });
    stepsHtml += `
        <div class="mt-3 pt-3 border-t border-gray-300">
            <div class="flex justify-between text-sm font-semibold">
                <span>최종 결과:</span>
                <span class="text-blue-600">${data.total || 0}개</span>
            </div>
        </div>
    </div>`;
    
    stepsContainer.innerHTML = stepsHtml;
}

// 차시 선택 시 콘텐츠 검색 함수 추가
function searchContentsForChasi(chasiId) {
    // 검색 필드 초기화
    document.getElementById('contentSearchInput').value = '';
    document.getElementById('contentTypeCategoryFilter').value = '';
    document.getElementById('contentTypeFilter').value = '';
    document.getElementById('chapterFilter').value = '';
    document.getElementById('subchapterFilter').value = '';
    
    // 차시 ID로 검색
    const params = new URLSearchParams({
        chasi_id: chasiId,
        course_id: window.courseConfig.courseId
    });
    
    // 검색 실행
    searchContentsWithParams(params);
}

// 파라미터로 검색 실행
async function searchContentsWithParams(params) {
    try {
        showLoadingInContentsList();
        
        const response = await fetch(`${window.courseConfig.urls.contentsSearch}?${params}`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displaySearchSteps(data);
            displaySearchResults(data.results);
        } else {
            throw new Error('검색 중 오류가 발생했습니다.');
        }
    } catch (error) {
        showMessage(error.message, 'error');
        displaySearchError();
    }
}

// 대단원 필터 초기화 수정
async function initChapterFilters() {
    try {
        const response = await fetch(`/teacher/api/courses/${window.courseConfig.courseId}/chapters/`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const chapterFilter = document.getElementById('chapterFilter');
            
            if (chapterFilter && data.success && data.chapters) {
                chapterFilter.innerHTML = '<option value="">모든 대단원</option>';
                
                data.chapters.forEach(chapter => {
                    chapterFilter.innerHTML += `<option value="${chapter.id}">${chapter.chapter_title || chapter.chapter_name}</option>`;
                });
            }
        }
    } catch (error) {
        console.error('대단원 필터 초기화 오류:', error);
    }
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    initChapterFilters();
});


// // 초기화
// document.addEventListener('DOMContentLoaded', () => {
//     initChapterFilters();
// });