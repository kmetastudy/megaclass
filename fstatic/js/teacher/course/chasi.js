// /static/js/teacher/course/chasi.js
// 차시(Chasi) 관련 기능

window.ChasiManager = {
    // 차시 상세 렌더링
    renderDetail: function(data) {
        return `
            <div>
                <div class="content-card mb-6">
                    <h3 class="font-semibold text-gray-800 mb-4">차시 정보</h3>
                    <form id="chasiEditForm" data-id="${data.id}">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">제목 *</label>
                            <input type="text" name="chasi_title" value="${data.chasi_title}" 
                                   class="form-input" required>
                        </div>
                        <div class="grid grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">순서 *</label>
                                <input type="number" name="chasi_order" value="${data.chasi_order}" 
                                       class="form-input" required min="1">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">수업시간(분) *</label>
                                <input type="number" name="duration_minutes" value="${data.duration_minutes}" 
                                       class="form-input" required min="5">
                            </div>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">학습목표</label>
                            <textarea name="learning_objectives" rows="3" class="form-input">${data.learning_objectives || ''}</textarea>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">설명</label>
                            <textarea name="description" rows="3" class="form-input">${data.description || ''}</textarea>
                        </div>
                        <div class="flex gap-3">
                            <button type="submit" class="btn-modern btn-primary">
                                <i class="fas fa-save"></i> 저장
                            </button>
                            <button type="button" onclick="ChasiManager.delete(${data.id})" class="btn-modern btn-danger">
                                <i class="fas fa-trash"></i> 삭제
                            </button>
                        </div>
                    </form>
                </div>

                <!-- 슬라이드 관리 섹션 -->
                <div class="mt-8">
                    <h3 class="text-lg font-semibold text-gray-800 mb-4">
                        <i class="fas fa-images mr-2"></i>슬라이드 관리
                        <span class="text-sm text-gray-500 ml-2">
                            <span id="slide-count-${data.id}">${data.slides ? data.slides.length : 0}</span>개 슬라이드
                        </span>
                    </h3>
                    
                    <!-- 슬라이드 추가 폼 -->
                    <div class="accordion-form active mb-6">
                        <h4 class="font-semibold text-gray-800 mb-4">
                            <i class="fas fa-plus-circle mr-2"></i>새 슬라이드 추가
                        </h4>
                        
                        <form id="slide-form-${data.id}" class="space-y-4" onsubmit="return false;">
                            <input type="hidden" name="chasi_id" value="${data.id}">
                            
                            <!-- 콘텐츠 선택 -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">콘텐츠 선택 *</label>
                                <div class="border border-gray-300 rounded-lg max-h-64 overflow-y-auto bg-white">
                                    <div id="content-list-${data.id}">
                                        <div class="p-4 text-center text-gray-500">
                                            <i class="fas fa-spinner fa-spin mr-2"></i>콘텐츠 로딩 중...
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 슬라이드 정보 -->
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">슬라이드 제목</label>
                                    <input type="text" name="slide_title" 
                                           class="form-input"
                                           placeholder="슬라이드 제목 (선택사항)">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">예상 시간(분)</label>
                                    <input type="number" name="estimated_time" value="5" min="1" max="60"
                                           class="form-input">
                                </div>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">교사 메모</label>
                                <textarea name="instructor_notes" rows="2"
                                          class="form-input"
                                          placeholder="수업 진행 시 참고사항"></textarea>
                            </div>
                            
                            <div class="flex items-center justify-between">
                                <button type="button" onclick="SlideManager.addSlide(${data.id})" 
                                        class="btn-modern btn-primary"
                                        id="add-slide-btn-${data.id}" disabled>
                                    <i class="fas fa-plus mr-2"></i>슬라이드 추가
                                </button>
                                <a href="${window.courseConfig.urls.contentsCreate}?from_chasi=${data.id}" 
                                   target="_blank"
                                   class="text-blue-600 hover:text-blue-800 text-sm">
                                    새 콘텐츠 만들기 →
                                </a>
                            </div>
                        </form>
                    </div>
                    
                    <!-- 슬라이드 목록 -->
                    <div>
                        <h4 class="font-semibold text-gray-800 mb-3">
                            슬라이드 목록
                            <span class="text-sm text-gray-500 ml-2">(드래그하여 순서 변경)</span>
                        </h4>
                        <div id="slides-${data.id}" class="space-y-3" data-chasi-id="${data.id}">
                            <!-- 슬라이드가 여기에 로드됩니다 -->
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    // 차시 추가 폼 표시
    showCreateForm: function(subchapterId) {
        const formHtml = `
            <div class="new-item-card" id="new-chasi-card">
                <h4 class="font-semibold text-gray-800 mb-4">
                    <i class="fas fa-plus-circle mr-2"></i>새 차시 추가
                </h4>
                <form id="chasiCreateForm" data-subchapter-id="${subchapterId}">
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">차시명 *</label>
                        <input type="text" name="chasi_title" class="form-input" 
                               placeholder="예: 서정 문학의 이해" required>
                    </div>
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">순서 *</label>
                            <input type="number" name="chasi_order" class="form-input" 
                                   value="1" required min="1">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">수업시간(분) *</label>
                            <input type="number" name="duration_minutes" class="form-input" 
                                   value="45" required min="5">
                        </div>
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">학습목표</label>
                        <textarea name="learning_objectives" rows="3" class="form-input" 
                                  placeholder="학습목표를 입력하세요..."></textarea>
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">설명</label>
                        <textarea name="description" rows="3" class="form-input" 
                                  placeholder="차시에 대한 설명을 입력하세요..."></textarea>
                    </div>
                    <div class="flex gap-3">
                        <button type="submit" class="btn-modern btn-primary">
                            <i class="fas fa-save"></i> 저장
                        </button>
                        <button type="button" onclick="cancelForm('new-chasi-card')" class="btn-modern btn-secondary">
                            <i class="fas fa-times"></i> 취소
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        const container = document.getElementById('chasis-container');
        container.insertAdjacentHTML('afterbegin', formHtml);
        document.querySelector('#new-chasi-card input[name="chasi_title"]').focus();
    },

    // 차시 수정 토글
    toggleEdit: async function(chasiId) {
        const editDiv = document.getElementById(`chasi-edit-${chasiId}`);
        
        if (editDiv.classList.contains('hidden')) {
            try {
                const data = await apiRequest(`/teacher/api/chasi/${chasiId}/detail/`);
                const formHtml = `
                    <form class="chasiEditInlineForm" data-id="${chasiId}">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">제목 *</label>
                            <input type="text" name="chasi_title" value="${data.chasi_title}" 
                                   class="form-input" required>
                        </div>
                        <div class="grid grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">순서 *</label>
                                <input type="number" name="chasi_order" value="${data.chasi_order}" 
                                       class="form-input" required min="1">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">수업시간(분) *</label>
                                <input type="number" name="duration_minutes" value="${data.duration_minutes}" 
                                       class="form-input" required min="5">
                            </div>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">학습목표</label>
                            <textarea name="learning_objectives" rows="3" class="form-input">${data.learning_objectives || ''}</textarea>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">설명</label>
                            <textarea name="description" rows="3" class="form-input">${data.description || ''}</textarea>
                        </div>
                        <div class="flex gap-3">
                            <button type="submit" class="btn-modern btn-primary">
                                <i class="fas fa-save"></i> 저장
                            </button>
                            <button type="button" onclick="ChasiManager.toggleEdit(${chasiId})" 
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
                showError('차시 정보를 불러올 수 없습니다.');
            }
        } else {
            editDiv.classList.add('hidden');
            editDiv.classList.remove('active');
        }
    },

    // 차시 생성
    create: async function(subchapterId, formData) {
        try {
            const response = await submitForm(`/teacher/subchapters/${subchapterId}/chasis/create/`, formData);
            
            showSuccess('차시가 생성되었습니다.');
            refreshTree();
            loadNodeContent(window.currentNode);
            
        } catch (error) {
            showError('차시 생성에 실패했습니다: ' + error.message);
        }
    },

    // 차시 수정
    update: async function(chasiId, formData) {
        try {
            const response = await submitForm(`/teacher/chasis/${chasiId}/edit/`, formData);
            
            showSuccess('차시가 수정되었습니다.');
            refreshTree();
            loadNodeContent(window.currentNode);
            
        } catch (error) {
            showError('차시 수정에 실패했습니다: ' + error.message);
        }
    },

    // 차시 삭제
    delete: async function(chasiId) {
        if (!confirm('정말 이 차시를 삭제하시겠습니까?\n모든 슬라이드도 함께 삭제됩니다.')) {
            return;
        }

        try {
            await apiRequest(`/teacher/chasis/${chasiId}/delete/`, {
                method: 'POST'
            });
            
            showSuccess('차시가 삭제되었습니다.');
            refreshTree();
            loadNodeContent(window.currentNode);
            
        } catch (error) {
            showError('차시 삭제에 실패했습니다: ' + error.message);
        }
    }
};

// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    // 차시 생성 폼 제출
    $(document).on('submit', '#chasiCreateForm', function(e) {
        e.preventDefault();
        const subchapterId = $(this).data('subchapter-id');
        const formData = new FormData(this);
        ChasiManager.create(subchapterId, formData);
    });

    // 차시 수정 폼 제출 (상세 페이지)
    $(document).on('submit', '#chasiEditForm', function(e) {
        e.preventDefault();
        const chasiId = $(this).data('id');
        const formData = new FormData(this);
        ChasiManager.update(chasiId, formData);
    });

    // 차시 수정 폼 제출 (인라인)
    $(document).on('submit', '.chasiEditInlineForm', function(e) {
        e.preventDefault();
        const chasiId = $(this).data('id');
        const formData = new FormData(this);
        ChasiManager.update(chasiId, formData);
    });
});