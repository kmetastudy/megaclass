// SlideManager 객체에 선택된 콘텐츠를 저장할 배열 추가
window.SlideManager = {
    sortableInstances: {},
    selectedContents: {}, // 차시별 선택된 콘텐츠 저장
    
    // 콘텐츠 목록 로드
    loadContents: async function(chasiId) {
        try {
            const data = await apiRequest(`/teacher/api/contents/list/?chasi_id=${chasiId}`);
            const container = document.getElementById(`content-list-${chasiId}`);
            
            if (data.contents && data.contents.length > 0) {
                // 선택된 콘텐츠 영역 추가
                let html = `
                    <div id="selected-contents-${chasiId}" class="selected-contents-area mb-3" style="display: none;">
                        <h6 class="text-sm font-semibold text-gray-700 mb-2">
                            <i class="fas fa-check-circle text-green-600 mr-1"></i>선택된 콘텐츠
                        </h6>
                        <div id="selected-contents-list-${chasiId}" class="space-y-2 mb-3">
                            <!-- 선택된 콘텐츠가 여기에 표시됩니다 -->
                        </div>
                        <div class="flex gap-2 mb-3">
                            <button onclick="SlideManager.addSelectedContents(${chasiId})" 
                                    class="btn-modern btn-primary btn-sm">
                                <i class="fas fa-plus mr-1"></i>선택한 콘텐츠 추가
                            </button>
                            <button onclick="SlideManager.clearSelectedContents(${chasiId})" 
                                    class="btn-modern btn-secondary btn-sm">
                                <i class="fas fa-times mr-1"></i>선택 취소
                            </button>
                        </div>
                        <hr class="my-3">
                    </div>
                `;
                
                // 전체 선택 체크박스
                html += `
                    <div class="p-3 bg-gray-50 border-b border-gray-200">
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" id="select-all-${chasiId}" 
                                   onchange="SlideManager.toggleSelectAll(${chasiId})"
                                   class="h-4 w-4 text-purple-600 rounded">
                            <span class="ml-2 text-sm font-medium text-gray-700">전체 선택</span>
                        </label>
                    </div>
                `;
                
                // 콘텐츠 목록
                html += data.contents.map(content => `
                    <div class="content-item p-3 border-b border-gray-200 last:border-b-0 hover:bg-gray-50" 
                         data-content-id="${content.id}">
                        <div class="flex items-center">
                            <input type="checkbox" 
                                   id="content-check-${chasiId}-${content.id}"
                                   class="content-checkbox h-4 w-4 text-purple-600 rounded mr-3"
                                   value="${content.id}"
                                   onchange="SlideManager.toggleContentSelection(${chasiId}, ${content.id}, '${escapeHtml(content.title)}', '${escapeHtml(content.content_type)}')">
                            <div class="flex-1 cursor-pointer" onclick="SlideManager.selectContent(${chasiId}, ${content.id}, '${escapeHtml(content.title)}')">
                                <h6 class="font-medium text-gray-800">${escapeHtml(content.title)}</h6>
                                <div class="flex items-center space-x-2 mt-1">
                                    <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                                        ${escapeHtml(content.content_type)}
                                    </span>
                                    <span class="text-gray-500 text-xs">${content.created_at}</span>
                                </div>
                                ${content.preview ? `<p class="text-sm text-gray-600 mt-1">${escapeHtml(content.preview)}</p>` : ''}
                            </div>
                            <input type="radio" name="content_id_${chasiId}" value="${content.id}" 
                                   class="h-4 w-4 text-purple-600 ml-3">
                        </div>
                    </div>
                `).join('');
                
                container.innerHTML = html;
                
                // 선택된 콘텐츠 배열 초기화
                if (!this.selectedContents[chasiId]) {
                    this.selectedContents[chasiId] = [];
                }
            } else {
                showEmptyState(
                    container,
                    'fa-file-alt',
                    '사용 가능한 콘텐츠가 없습니다.',
                    `<a href="${window.courseConfig.urls.contentsCreate}?from_chasi=${chasiId}" 
                        target="_blank"
                        class="text-blue-600 hover:text-blue-800 text-sm mt-2 inline-block">
                         새 콘텐츠 만들기 →
                     </a>`
                );
            }
        } catch (error) {
            showError('콘텐츠 로드 중 오류가 발생했습니다.');
        }
    },
    
    // 콘텐츠 선택/해제 토글
    toggleContentSelection: function(chasiId, contentId, title, contentType) {
        const checkbox = document.getElementById(`content-check-${chasiId}-${contentId}`);
        
        if (!this.selectedContents[chasiId]) {
            this.selectedContents[chasiId] = [];
        }
        
        if (checkbox.checked) {
            // 선택된 콘텐츠 추가
            if (!this.selectedContents[chasiId].find(c => c.id === contentId)) {
                this.selectedContents[chasiId].push({
                    id: contentId,
                    title: title,
                    content_type: contentType
                });
            }
        } else {
            // 선택 해제
            this.selectedContents[chasiId] = this.selectedContents[chasiId].filter(c => c.id !== contentId);
        }
        
        this.updateSelectedContentsDisplay(chasiId);
    },
    
    // 선택된 콘텐츠 표시 업데이트
    updateSelectedContentsDisplay: function(chasiId) {
        const selectedArea = document.getElementById(`selected-contents-${chasiId}`);
        const selectedList = document.getElementById(`selected-contents-list-${chasiId}`);
        
        if (this.selectedContents[chasiId].length > 0) {
            selectedArea.style.display = 'block';
            
            selectedList.innerHTML = this.selectedContents[chasiId].map(content => `
                <div class="content-item-wrapper content-item" data-content-id="${content.id}" draggable="true">
                    <div class="content-search-item bg-purple-50 border border-purple-200 rounded p-2">
                        <div class="content-item-header">
                            <h4 class="content-item-title text-sm">${content.title}</h4>
                            <span class="content-type-badge badge-gray text-xs">
                                ${content.content_type}
                            </span>
                        </div>
                        <div class="content-item-actions">
                            <button onclick="SlideManager.removeSelectedContent(${chasiId}, ${content.id})" 
                                    class="text-red-500 hover:text-red-700" title="제거">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
            
            // 드래그 가능하도록 설정
            this.selectedContents[chasiId].forEach(content => {
                const element = selectedList.querySelector(`[data-content-id="${content.id}"]`);
                if (element && window.makeContentItemDraggable) {
                    window.makeContentItemDraggable(element, content);
                }
            });
        } else {
            selectedArea.style.display = 'none';
        }
    },
    
    // 전체 선택/해제
    toggleSelectAll: function(chasiId) {
        const selectAllCheckbox = document.getElementById(`select-all-${chasiId}`);
        const checkboxes = document.querySelectorAll(`#content-list-${chasiId} .content-checkbox`);
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
            const contentItem = checkbox.closest('.content-item');
            const contentId = parseInt(checkbox.value);
            const title = contentItem.querySelector('.font-medium').textContent;
            const contentType = contentItem.querySelector('.bg-blue-100').textContent.trim();
            
            if (selectAllCheckbox.checked) {
                if (!this.selectedContents[chasiId]) {
                    this.selectedContents[chasiId] = [];
                }
                if (!this.selectedContents[chasiId].find(c => c.id === contentId)) {
                    this.selectedContents[chasiId].push({
                        id: contentId,
                        title: title,
                        content_type: contentType
                    });
                }
            }
        });
        
        if (!selectAllCheckbox.checked) {
            this.selectedContents[chasiId] = [];
        }
        
        this.updateSelectedContentsDisplay(chasiId);
    },
    
    // 선택된 콘텐츠 제거
    removeSelectedContent: function(chasiId, contentId) {
        this.selectedContents[chasiId] = this.selectedContents[chasiId].filter(c => c.id !== contentId);
        document.getElementById(`content-check-${chasiId}-${contentId}`).checked = false;
        this.updateSelectedContentsDisplay(chasiId);
    },
    
    // 선택 초기화
    clearSelectedContents: function(chasiId) {
        this.selectedContents[chasiId] = [];
        document.getElementById(`select-all-${chasiId}`).checked = false;
        document.querySelectorAll(`#content-list-${chasiId} .content-checkbox`).forEach(cb => {
            cb.checked = false;
        });
        this.updateSelectedContentsDisplay(chasiId);
    },
    
    // 선택된 콘텐츠들을 슬라이드로 추가
    addSelectedContents: async function(chasiId) {
        if (!this.selectedContents[chasiId] || this.selectedContents[chasiId].length === 0) {
            showError('선택된 콘텐츠가 없습니다.');
            return;
        }
        
        const btn = event.target.closest('button');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>추가 중...';
        
        try {
            for (const content of this.selectedContents[chasiId]) {
                const formData = new FormData();
                formData.append('content_id', content.id);
                formData.append('slide_title', '');
                formData.append('estimated_time', '5');
                
                await submitForm(`/teacher/api/chasis/${chasiId}/slides/add/`, formData);
            }
            
            showSuccess(`${this.selectedContents[chasiId].length}개의 슬라이드가 추가되었습니다.`);
            
            // 초기화
            this.clearSelectedContents(chasiId);
            
            // 슬라이드 목록 새로고침
            this.loadSlides(chasiId);
            refreshTree();
            
        } catch (error) {
            showError('슬라이드 추가 중 오류가 발생했습니다.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-plus mr-1"></i>선택한 콘텐츠 추가';
        }
    }
};