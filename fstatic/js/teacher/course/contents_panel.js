// contents_panel.js
// 콘텐츠 라이브러리 패널 관리

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
document.getElementById('quickContentForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch('/teacher/api/contents/quick-create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.courseConfig.csrfToken
            },
            body: JSON.stringify({
                ...data,
                course_id: window.courseConfig.courseId,
                chapter_id: window.currentNode?.data?.chapter_id,
                subchapter_id: window.currentNode?.data?.subchapter_id
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage('콘텐츠가 생성되었습니다.', 'success');
            e.target.reset();
            
            // 생성된 콘텐츠를 자동으로 드롭 영역에 추가
            if (result.content) {
                addDroppedContent({
                    id: result.content.id,
                    title: result.content.title,
                    type: result.content.content_type_display,
                    chapter: result.content.chapter_name,
                    subchapter: result.content.subchapter_name
                });
            }
        } else {
            const error = await response.json();
            throw new Error(error.message || '콘텐츠 생성에 실패했습니다.');
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
});

// 대단원 필터 초기화
async function initChapterFilters() {
    try {
        const response = await fetch(`/teacher/api/courses/${window.courseConfig.courseId}/chapters/`, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (response.ok) {
            const chapters = await response.json();
            const chapterFilter = document.getElementById('chapterFilter');
            
            chapterFilter.innerHTML = '<option value="">모든 대단원</option>';
            chapters.forEach(chapter => {
                chapterFilter.innerHTML += `<option value="${chapter.id}">${chapter.chapter_name}</option>`;
            });
            
            // 대단원 변경 시 소단원 필터 업데이트
            chapterFilter.addEventListener('change', () => {
                updateSubchapterFilter(chapterFilter.value);
            });
        }
    } catch (error) {
        console.error('대단원 필터 초기화 오류:', error);
    }
}

// 소단원 필터 업데이트
async function updateSubchapterFilter(chapterId) {
    const subchapterFilter = document.getElementById('subchapterFilter');
    
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
            const subchapters = await response.json();
            
            subchapterFilter.innerHTML = '<option value="">모든 소단원</option>';
            subchapters.forEach(subchapter => {
                subchapterFilter.innerHTML += `<option value="${subchapter.id}">${subchapter.subchapter_name}</option>`;
            });
        }
    } catch (error) {
        console.error('소단원 필터 업데이트 오류:', error);
    }
}

// 엔터키로 검색 실행
document.getElementById('contentSearchInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchContents();
    }
});

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    initChapterFilters();
});