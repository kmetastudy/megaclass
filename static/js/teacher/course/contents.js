// /static/js/teacher/course/contents.js
// 콘텐츠(Contents) 관련 기능

window.ContentsManager = {
    // 콘텐츠 검색
    searchContents: async function(query, contentType = '', difficulty = '') {
        try {
            const params = new URLSearchParams({
                q: query,
                type: contentType,
                difficulty: difficulty
            });
            
            const data = await apiRequest(`/teacher/api/contents/search/?${params}`);
            return data.results || [];
        } catch (error) {
            showError('콘텐츠 검색 중 오류가 발생했습니다.');
            return [];
        }
    },

    // 콘텐츠 미리보기
    previewContent: async function(contentId) {
        try {
            const data = await apiRequest(`/teacher/api/contents/${contentId}/preview/`);
            this.showPreviewModal(data);
        } catch (error) {
            showError('콘텐츠 미리보기를 불러올 수 없습니다.');
        }
    },

    // 미리보기 모달 표시
    showPreviewModal: function(content) {
        const modalHtml = `
            <div id="contentPreviewModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                <div class="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
                    <div class="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                        <h3 class="text-lg font-semibold text-gray-800">${escapeHtml(content.title)}</h3>
                        <button onclick="ContentsManager.closePreviewModal()" class="text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    <div class="p-6 overflow-y-auto" style="max-height: calc(90vh - 120px);">
                        <div class="mb-4">
                            <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded text-sm">
                                ${escapeHtml(content.content_type)}
                            </span>
                            ${content.difficulty ? `
                                <span class="ml-2 bg-gray-100 text-gray-800 px-3 py-1 rounded text-sm">
                                    ${escapeHtml(content.difficulty)}
                                </span>
                            ` : ''}
                            ${content.estimated_time ? `
                                <span class="ml-2 text-gray-600 text-sm">
                                    <i class="fas fa-clock mr-1"></i>${content.estimated_time}분
                                </span>
                            ` : ''}
                        </div>
                        
                        <div class="prose max-w-none">
                            ${content.page || content.content || ''}
                        </div>
                        
                        ${content.answer ? `
                            <div class="mt-6 pt-6 border-t border-gray-200">
                                <h4 class="font-semibold text-gray-700 mb-2">정답</h4>
                                <div class="bg-green-50 p-4 rounded-lg">
                                    ${escapeHtml(content.answer)}
                                </div>
                            </div>
                        ` : ''}
                        
                        ${content.tags ? `
                            <div class="mt-6 pt-6 border-t border-gray-200">
                                <h4 class="font-semibold text-gray-700 mb-2">태그</h4>
                                <div class="flex flex-wrap gap-2">
                                    ${Object.entries(content.tags).map(([key, value]) => `
                                        <span class="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">
                                            ${escapeHtml(key)}: ${escapeHtml(value)}
                                        </span>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                        <button onclick="ContentsManager.closePreviewModal()" 
                                class="btn-modern btn-secondary">
                            닫기
                        </button>
                        ${content.id ? `
                            <a href="/teacher/contents/${content.id}/edit/" 
                               target="_blank"
                               class="btn-modern btn-primary">
                                <i class="fas fa-edit mr-2"></i>수정
                            </a>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // ESC 키로 닫기
        document.addEventListener('keydown', this.handleEscKey);
    },

    // 미리보기 모달 닫기
    closePreviewModal: function() {
        const modal = document.getElementById('contentPreviewModal');
        if (modal) {
            modal.style.opacity = '0';
            setTimeout(() => modal.remove(), 300);
        }
        document.removeEventListener('keydown', this.handleEscKey);
    },

    // ESC 키 핸들러
    handleEscKey: function(e) {
        if (e.key === 'Escape') {
            ContentsManager.closePreviewModal();
        }
    },

    // 콘텐츠 필터링 UI
    renderFilterUI: function(containerSelector) {
        const container = document.querySelector(containerSelector);
        if (!container) return;
        
        const filterHtml = `
            <div class="mb-4 p-4 bg-gray-50 rounded-lg">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">검색어</label>
                        <input type="text" id="contentSearchInput" 
                               class="form-input"
                               placeholder="콘텐츠 검색...">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">콘텐츠 타입</label>
                        <select id="contentTypeFilter" class="form-input">
                            <option value="">모든 타입</option>
                            <option value="multiple_choice">객관식 문제</option>
                            <option value="short_answer">단답형 문제</option>
                            <option value="essay">서술형 문제</option>
                            <option value="presentation">PPT</option>
                            <option value="report">리포트</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">난이도</label>
                        <select id="contentDifficultyFilter" class="form-input">
                            <option value="">모든 난이도</option>
                            <option value="easy">쉬움</option>
                            <option value="medium">보통</option>
                            <option value="hard">어려움</option>
                        </select>
                    </div>
                </div>
                <div class="mt-4 flex justify-end">
                    <button onclick="ContentsManager.applyFilter()" 
                            class="btn-modern btn-primary">
                        <i class="fas fa-search mr-2"></i>검색
                    </button>
                </div>
            </div>
        `;
        
        container.innerHTML = filterHtml;
    },

    // 필터 적용
    applyFilter: async function() {
        const searchInput = document.getElementById('contentSearchInput');
        const typeFilter = document.getElementById('contentTypeFilter');
        const difficultyFilter = document.getElementById('contentDifficultyFilter');
        
        if (!searchInput) return;
        
        const results = await this.searchContents(
            searchInput.value,
            typeFilter.value,
            difficultyFilter.value
        );
        
        // 결과 표시 (실제 구현 시 적절한 컨테이너에 표시)
        console.log('검색 결과:', results);
    },

    // 콘텐츠 복제
    duplicateContent: async function(contentId) {
        if (!confirm('이 콘텐츠를 복제하시겠습니까?')) {
            return;
        }
        
        try {
            const response = await apiRequest(`/teacher/contents/${contentId}/duplicate/`, {
                method: 'POST'
            });
            
            if (response.success) {
                showSuccess('콘텐츠가 복제되었습니다.');
                if (response.new_content_id) {
                    window.open(`/teacher/contents/${response.new_content_id}/edit/`, '_blank');
                }
            }
        } catch (error) {
            showError('콘텐츠 복제 중 오류가 발생했습니다.');
        }
    },

    // 콘텐츠 활성화/비활성화 토글
    toggleContentActive: async function(contentId) {
        try {
            const response = await apiRequest(`/teacher/contents/${contentId}/toggle-active/`, {
                method: 'POST'
            });
            
            if (response.success) {
                showSuccess(response.is_active ? '콘텐츠가 활성화되었습니다.' : '콘텐츠가 비활성화되었습니다.');
                return response.is_active;
            }
        } catch (error) {
            showError('상태 변경 중 오류가 발생했습니다.');
        }
        return null;
    },

    // 콘텐츠 타입별 템플릿 가져오기
    getContentTemplate: async function(contentTypeId) {
        try {
            const data = await apiRequest(`/teacher/api/content-types/${contentTypeId}/template/`);
            return data.template || '';
        } catch (error) {
            showError('템플릿을 불러올 수 없습니다.');
            return '';
        }
    },

    // 콘텐츠 유효성 검사
    validateContent: function(formData) {
        const title = formData.get('title');
        const page = formData.get('page');
        const contentType = formData.get('content_type');
        
        if (!title || title.trim().length < 2) {
            showError('제목은 2자 이상 입력해주세요.');
            return false;
        }
        
        if (!page || page.trim().length < 10) {
            showError('콘텐츠 내용은 10자 이상 입력해주세요.');
            return false;
        }
        
        if (!contentType) {
            showError('콘텐츠 타입을 선택해주세요.');
            return false;
        }
        
        return true;
    }
};

// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    // 콘텐츠 검색 엔터키 처리
    $(document).on('keypress', '#contentSearchInput', function(e) {
        if (e.key === 'Enter') {
            ContentsManager.applyFilter();
        }
    });
});