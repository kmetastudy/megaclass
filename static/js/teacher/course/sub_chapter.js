// /static/js/teacher/course/sub_chapter.js
// 소단원(SubChapter) 관련 기능

window.SubChapterManager = {
    // 소단원 상세 렌더링
    renderDetail: function(data) {
        return `
            <div>
                <div class="content-card mb-6">
                    <h3 class="font-semibold text-gray-800 mb-4">소단원 정보</h3>
                    <form id="subchapterEditForm" data-id="${data.id}">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">제목 *</label>
                            <input type="text" name="sub_chapter_title" value="${data.sub_chapter_title}" 
                                   class="form-input" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">순서 *</label>
                            <input type="number" name="sub_chapter_order" value="${data.sub_chapter_order}" 
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
                            <button type="button" onclick="SubChapterManager.delete(${data.id})" class="btn-modern btn-danger">
                                <i class="fas fa-trash"></i> 삭제
                            </button>
                        </div>
                    </form>
                </div>

                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-800">차시 목록</h3>
                    <button onclick="ChasiManager.showCreateForm(${data.id})" class="btn-modern btn-primary">
                        <i class="fas fa-plus"></i> 차시 추가
                    </button>
                </div>
                
                <div id="chasis-container">
                    ${this.renderChasisList(data.chasis)}
                </div>
            </div>
        `;
    },

    // 차시 목록 렌더링
    renderChasisList: function(chasis) {
        if (!chasis || chasis.length === 0) {
            return `
                <div class="text-center py-12 bg-gray-50 rounded-lg">
                    <i class="fas fa-clock text-gray-300 text-5xl mb-4"></i>
                    <p class="text-gray-500">차시가 없습니다.</p>
                </div>
            `;
        }

        return `
            <div class="space-y-3">
                ${chasis.map(ch => `
                    <div class="content-card" id="chasi-${ch.id}">
                        <div class="flex justify-between items-center">
                            <div>
                                <h4 class="font-semibold text-gray-800">${ch.order}. ${ch.title}</h4>
                                <div class="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                                    <span><i class="fas fa-images mr-1"></i>${ch.slide_count}개 슬라이드</span>
                                    <span><i class="fas fa-clock mr-1"></i>${ch.duration}분</span>
                                </div>
                            </div>
                            <div class="flex space-x-2">
                                <a href="${window.courseConfig.urls.chasiSlideManage.replace('0', ch.id)}" 
                                   class="text-green-600 hover:text-green-700 transition">
                                    <i class="fas fa-images"></i>
                                </a>
                                <button onclick="ChasiManager.toggleEdit(${ch.id})" class="text-gray-600 hover:text-blue-600 transition">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button onclick="ChasiManager.delete(${ch.id})" class="text-gray-600 hover:text-red-600 transition">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        <div id="chasi-edit-${ch.id}" class="hidden accordion-form mt-4">
                            <!-- 수정 폼이 여기에 동적으로 추가됩니다 -->
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    },

    // 소단원 추가 폼 표시
    showCreateForm: function(chapterId) {
        const formHtml = `
            <div class="new-item-card" id="new-subchapter-card">
                <h4 class="font-semibold text-gray-800 mb-4">
                    <i class="fas fa-plus-circle mr-2"></i>새 소단원 추가
                </h4>
                <form id="subchapterCreateForm" data-chapter-id="${chapterId}">
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">소단원명 *</label>
                        <input type="text" name="sub_chapter_title" class="form-input" 
                               placeholder="예: 갈래에 따른 문학의 성격" required>
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">순서 *</label>
                        <input type="number" name="sub_chapter_order" class="form-input" 
                               value="1" required min="1">
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">설명</label>
                        <textarea name="description" rows="3" class="form-input" 
                                  placeholder="소단원에 대한 설명을 입력하세요..."></textarea>
                    </div>
                    <div class="flex gap-3">
                        <button type="submit" class="btn-modern btn-primary">
                            <i class="fas fa-save"></i> 저장
                        </button>
                        <button type="button" onclick="cancelForm('new-subchapter-card')" class="btn-modern btn-secondary">
                            <i class="fas fa-times"></i> 취소
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        const container = document.getElementById('subchapters-container');
        container.insertAdjacentHTML('afterbegin', formHtml);
        document.querySelector('#new-subchapter-card input[name="sub_chapter_title"]').focus();
    },

    // 소단원 수정 토글
    toggleEdit: async function(subchapterId) {
        const editDiv = document.getElementById(`subchapter-edit-${subchapterId}`);
        
        if (editDiv.classList.contains('hidden')) {
            try {
                const data = await apiRequest(`/teacher/api/subchapter/${subchapterId}/detail/`);
                const formHtml = `
                    <form class="subchapterEditInlineForm" data-id="${subchapterId}">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">제목 *</label>
                            <input type="text" name="sub_chapter_title" value="${data.sub_chapter_title}" 
                                   class="form-input" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">순서 *</label>
                            <input type="number" name="sub_chapter_order" value="${data.sub_chapter_order}" 
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
                            <button type="button" onclick="SubChapterManager.toggleEdit(${subchapterId})" 
                                    class="btn-modern btn-secondary">
                                <i class="fas fa-times"></i> 취소
                            </button>
                        </div>
                    </form>
                `;
                editDiv.innerHTML = formHtml;
                editDiv.classList.remove('hidden');
                editDiv.classList.add('active');
            } catch (error) {
                showError('소단원 정보를 불러올 수 없습니다.');
            }
        } else {
            editDiv.classList.add('hidden');
            editDiv.classList.remove('active');
        }
    },

    // 소단원 생성
    create: async function(chapterId, formData) {
        try {
            const response = await submitForm(`/teacher/chapters/${chapterId}/subchapters/create/`, formData);
            
            showSuccess('소단원이 생성되었습니다.');
            refreshTree();
            loadNodeContent(window.currentNode);
            
        } catch (error) {
            showError('소단원 생성에 실패했습니다: ' + error.message);
        }
    },

    // 소단원 수정
    update: async function(subchapterId, formData) {
        try {
            const response = await submitForm(`/teacher/subchapters/${subchapterId}/edit/`, formData);
            
            showSuccess('소단원이 수정되었습니다.');
            refreshTree();
            loadNodeContent(window.currentNode);
            
        } catch (error) {
            showError('소단원 수정에 실패했습니다: ' + error.message);
        }
    },

    // 소단원 삭제
    delete: async function(subchapterId) {
        if (!confirm('정말 이 소단원을 삭제하시겠습니까?\n하위의 모든 차시도 함께 삭제됩니다.')) {
            return;
        }

        try {
            await apiRequest(`/teacher/subchapters/${subchapterId}/delete/`, {
                method: 'POST'
            });
            
            showSuccess('소단원이 삭제되었습니다.');
            refreshTree();
            loadNodeContent(window.currentNode);
            
        } catch (error) {
            showError('소단원 삭제에 실패했습니다: ' + error.message);
        }
    }
};

// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    // 소단원 생성 폼 제출
    $(document).on('submit', '#subchapterCreateForm', function(e) {
        e.preventDefault();
        const chapterId = $(this).data('chapter-id');
        const formData = new FormData(this);
        SubChapterManager.create(chapterId, formData);
    });

    // 소단원 수정 폼 제출 (상세 페이지)
    $(document).on('submit', '#subchapterEditForm', function(e) {
        e.preventDefault();
        const subchapterId = $(this).data('id');
        const formData = new FormData(this);
        SubChapterManager.update(subchapterId, formData);
    });

    // 소단원 수정 폼 제출 (인라인)
    $(document).on('submit', '.subchapterEditInlineForm', function(e) {
        e.preventDefault();
        const subchapterId = $(this).data('id');
        const formData = new FormData(this);
        SubChapterManager.update(subchapterId, formData);
    });
});