// /static/js/teacher/course/chapter.js
// 대단원(Chapter) 관련 기능

window.ChapterManager = {
    // 대단원 상세 렌더링
    renderDetail: function(data) {
        return `
            <div>
                <div class="content-card mb-6">
                    <h3 class="font-semibold text-gray-800 mb-4">대단원 정보</h3>
                    <form id="chapterEditForm" data-id="${data.id}">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">제목 *</label>
                            <input type="text" name="chapter_title" value="${data.chapter_title}" 
                                   class="form-input" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">순서 *</label>
                            <input type="number" name="chapter_order" value="${data.chapter_order}" 
                                   class="form-input" required min="1">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">설명</label>
                            <textarea name="description" rows="3" class="form-input">${data.description || ''}</textarea>
                        </div>
                        <div class="flex gap-3">
                            <button type="submit" class="btn-modern btn-primary">
                                <i class="fas fa-save"></i> 저장
                            </button>
                            <button type="button" onclick="ChapterManager.delete(${data.id})" class="btn-modern btn-danger">
                                <i class="fas fa-trash"></i> 삭제
                            </button>
                        </div>
                    </form>
                </div>

                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-800">소단원 목록</h3>
                    <button onclick="SubChapterManager.showCreateForm(${data.id})" class="btn-modern btn-primary">
                        <i class="fas fa-plus"></i> 소단원 추가
                    </button>
                </div>
                
                <div id="subchapters-container">
                    ${this.renderSubchaptersList(data.subchapters)}
                </div>
            </div>
        `;
    },

    // 소단원 목록 렌더링
    renderSubchaptersList: function(subchapters) {
        if (!subchapters || subchapters.length === 0) {
            return `
                <div class="text-center py-12 bg-gray-50 rounded-lg">
                    <i class="fas fa-folder-open text-gray-300 text-5xl mb-4"></i>
                    <p class="text-gray-500">소단원이 없습니다.</p>
                </div>
            `;
        }

        return `
            <div class="space-y-3">
                ${subchapters.map(sc => `
                    <div class="content-card" id="subchapter-${sc.id}">
                        <div class="flex justify-between items-center">
                            <div>
                                <h4 class="font-semibold text-gray-800">${sc.order}. ${sc.title}</h4>
                                <p class="text-sm text-gray-600 mt-1">
                                    <i class="fas fa-clock mr-1"></i>${sc.chasi_count}개 차시
                                </p>
                            </div>
                            <div class="flex space-x-2">
                                <button onclick="SubChapterManager.toggleEdit(${sc.id})" class="text-gray-600 hover:text-blue-600 transition">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button onclick="SubChapterManager.delete(${sc.id})" class="text-gray-600 hover:text-red-600 transition">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        <div id="subchapter-edit-${sc.id}" class="hidden accordion-form mt-4">
                            <!-- 수정 폼이 여기에 동적으로 추가됩니다 -->
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    },

    // 대단원 추가 폼 표시
    showCreateForm: function() {
        const formHtml = `
            <div class="new-item-card" id="new-chapter-card">
                <h4 class="font-semibold text-gray-800 mb-4">
                    <i class="fas fa-plus-circle mr-2"></i>새 대단원 추가
                </h4>
                <form id="chapterCreateForm">
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">대단원명 *</label>
                        <input type="text" name="chapter_title" class="form-input" 
                               placeholder="예: 문학의 갈래와 성격" required>
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">순서 *</label>
                        <input type="number" name="chapter_order" class="form-input" 
                               value="1" required min="1">
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">설명</label>
                        <textarea name="description" rows="3" class="form-input" 
                                  placeholder="대단원에 대한 설명을 입력하세요 (선택사항)"></textarea>
                    </div>
                    <div class="flex gap-3">
                        <button type="submit" class="btn-modern btn-primary">
                            <i class="fas fa-save"></i> 저장
                        </button>
                        <button type="button" onclick="cancelForm('new-chapter-card')" class="btn-modern btn-secondary">
                            <i class="fas fa-times"></i> 취소
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        const container = document.getElementById('chapters-container');
        container.insertAdjacentHTML('afterbegin', formHtml);
        document.querySelector('#new-chapter-card input[name="chapter_title"]').focus();
    },

    // 대단원 생성
    create: async function(formData) {
        try {
            const url = window.courseConfig.urls.chapterCreate;
            const response = await submitForm(url, formData);
            
            showSuccess('대단원이 생성되었습니다.');
            refreshTree();
            loadCourseOverview();
            
        } catch (error) {
            showError('대단원 생성에 실패했습니다: ' + error.message);
        }
    },

    // 대단원 수정
    update: async function(chapterId, formData) {
        try {
            const response = await submitForm(`/teacher/chapters/${chapterId}/edit/`, formData);
            
            showSuccess('대단원이 수정되었습니다.');
            refreshTree();
            loadNodeContent(window.currentNode);
            
        } catch (error) {
            showError('대단원 수정에 실패했습니다: ' + error.message);
        }
    },

    // 대단원 삭제
    delete: async function(chapterId) {
        if (!confirm('정말 이 대단원을 삭제하시겠습니까?\n하위의 모든 소단원과 차시도 함께 삭제됩니다.')) {
            return;
        }

        try {
            await apiRequest(`/teacher/chapters/${chapterId}/delete/`, {
                method: 'POST'
            });
            
            showSuccess('대단원이 삭제되었습니다.');
            refreshTree();
            loadCourseOverview();
            
        } catch (error) {
            showError('대단원 삭제에 실패했습니다: ' + error.message);
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    // 대단원 생성 폼 제출
    document.addEventListener('submit', function(e) {
        if (e.target.id === 'chapterCreateForm') {
            e.preventDefault();
            const formData = new FormData(e.target);
            ChapterManager.create(formData);
        }
        
        // 대단원 수정 폼 제출
        if (e.target.id === 'chapterEditForm') {
            e.preventDefault();
            const chapterId = e.target.dataset.id;
            const formData = new FormData(e.target);
            ChapterManager.update(chapterId, formData);
        }
    });
});