// /static/js/teacher/course/sliders.js
// 슬라이드(Slider) 관련 기능

window.SlideManager = {
    sortableInstances: {},
    // 선택된 콘텐츠 ID들을 추적하는 변수 추가
    selectedContentIds: new Set(),

    // 차시 콘텐츠 로드 (슬라이드 관련)
    loadChasiContent: function(chasiId) {
        this.loadContents(chasiId);
        this.loadSlides(chasiId);
    },

   // sliders.js - loadContents 함수를 다음과 같이 수정

 // 콘텐츠 로드 (초기 로드)
 loadContents_0622: async function(chasiId) {
    try {
        const data = await apiRequest(`/teacher/api/contents/list/?chasi_id=${chasiId}`);
        const container = document.getElementById(`content-list-${chasiId}`);
        
        if (data.contents && data.contents.length > 0) {
            container.innerHTML = data.contents.map(content => {
                const context = `chasi_${chasiId}`;
                const isSelected = window.ContentSelectionManager.isSelected(content.id, context);
                
                return `
                    <div class="content-item p-3 border-b border-gray-200 last:border-b-0 hover:bg-gray-50 cursor-pointer" 
                         onclick="SlideManager.selectContent(${chasiId}, ${content.id}, '${escapeHtml(content.title)}')">
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
                    </div>
                `;
            }).join('');
        } else {
            showEmptyState(container, 'fa-file-alt', '사용 가능한 콘텐츠가 없습니다.');
        }
    } catch (error) {
        showError('콘텐츠 로드 중 오류가 발생했습니다.');
    }
},
loadContents: async function(chasiId) {
    try {
        const data = await apiRequest(`/teacher/api/contents/list/?chasi_id=${chasiId}`);
        const container = document.getElementById(`content-list-${chasiId}`);
        
        if (data.contents && data.contents.length > 0) {
            // 선택된 콘텐츠와 선택되지 않은 콘텐츠 분리
            const selectedContents = [];
            const unselectedContents = [];
            
            data.contents.forEach(content => {
                if (window.selectedContentIds && window.selectedContentIds.has(content.id)) {
                    selectedContents.push(content);
                } else {
                    unselectedContents.push(content);
                }
            });
            
            // 선택된 것을 먼저, 그 다음 선택되지 않은 것 배치
            const sortedContents = [...selectedContents, ...unselectedContents];
            
            container.innerHTML = sortedContents.map(content => {
                const isSelected = window.selectedContentIds && window.selectedContentIds.has(content.id);
                
                return `
                    <div class="content-item p-3 border-b border-gray-200 last:border-b-0 hover:bg-gray-50 cursor-pointer ${isSelected ? 'selected bg-purple-50' : ''}" 
                         onclick="SlideManager.selectContent(${chasiId}, ${content.id}, '${escapeHtml(content.title)}')"
                         data-content-id="${content.id}">
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
                    </div>
                `;
            }).join('');
        } else {
            showEmptyState(container, 'fa-file-alt', '사용 가능한 콘텐츠가 없습니다.');
        }
    } catch (error) {
        showError('콘텐츠 로드 중 오류가 발생했습니다.');
    }
},
    // 슬라이드 목록 로드
    loadSlides: async function(chasiId) {
        try {
            const data = await apiRequest(`/teacher/api/chasis/${chasiId}/slides/`);
            const container = document.getElementById(`slides-${chasiId}`);
            
            if (data.slides && data.slides.length > 0) {
                container.innerHTML = data.slides.map(slide => this.renderSlideCard(slide, chasiId)).join('');
                
                // Sortable 초기화
                this.initializeSortable(chasiId);
            } else {
                showEmptyState(
                    container,
                    'fa-images',
                    '아직 슬라이드가 없습니다.'
                );
            }
            
            // 슬라이드 개수 업데이트
            const countEl = document.getElementById(`slide-count-${chasiId}`);
            if (countEl) {
                countEl.textContent = data.slides ? data.slides.length : 0;
            }
        } catch (error) {
            showError('슬라이드 로드 중 오류가 발생했습니다.');
        }
    },

    // 슬라이드 카드 렌더링
    renderSlideCard: function(slide, chasiId) {
        return `
            <div class="content-card slide-card" 
                 id="slide-${slide.id}" 
                 data-slide-id="${slide.id}">
                <div class="flex items-center justify-between">
                    <div class="flex items-center flex-1">
                        <div class="drag-handle mr-3 text-gray-400 hover:text-gray-600 cursor-move">
                            <i class="fas fa-grip-vertical"></i>
                        </div>
                        <div class="flex-1">
                            <div class="flex items-center mb-2">
                                <span class="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs font-medium slide-number">
                                    슬라이드 ${slide.slide_number}
                                </span>
                                <h6 class="ml-3 font-medium text-gray-800">${escapeHtml(slide.content_title)}</h6>
                            </div>
                            ${slide.slide_title ? `<p class="text-sm text-gray-600 mb-2">${escapeHtml(slide.slide_title)}</p>` : ''}
                            <div class="flex items-center space-x-3 text-xs text-gray-500">
                                <span><i class="fas fa-tag mr-1"></i>${escapeHtml(slide.content_type)}</span>
                                <span><i class="fas fa-clock mr-1"></i>${slide.estimated_time}분</span>
                            </div>
                            ${slide.instructor_notes ? `
                                <div class="mt-2 p-2 bg-yellow-50 rounded text-xs text-yellow-700">
                                    <i class="fas fa-sticky-note mr-1"></i>${escapeHtml(slide.instructor_notes)}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    <div class="ml-4 flex items-center space-x-2">
                        <button onclick="SlideManager.editSlide(${slide.id}, ${chasiId})" 
                                class="text-blue-600 hover:text-blue-800 p-2">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="SlideManager.deleteSlide(${slide.id}, ${chasiId})" 
                                class="text-red-600 hover:text-red-800 p-2">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    // Sortable 초기화
    initializeSortable: function(chasiId) {
        const container = document.getElementById(`slides-${chasiId}`);
        
        if (!container) return;
        
        // 기존 인스턴스 제거
        if (this.sortableInstances[chasiId]) {
            this.sortableInstances[chasiId].destroy();
        }
        
        this.sortableInstances[chasiId] = new Sortable(container, {
            animation: 150,
            handle: '.drag-handle',
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            dragClass: 'sortable-drag',
            
            onStart: function(evt) {
                evt.item.classList.add('dragging');
            },
            
            onEnd: (evt) => {
                evt.item.classList.remove('dragging');
                
                // 새로운 순서 계산
                const slides = container.querySelectorAll('.slide-card');
                const slideOrders = [];
                
                slides.forEach((slide, index) => {
                    const slideId = slide.dataset.slideId;
                    slideOrders.push({
                        slide_id: parseInt(slideId),
                        order: index + 1
                    });
                    
                    // 슬라이드 번호 즉시 업데이트
                    const numberEl = slide.querySelector('.slide-number');
                    if (numberEl) {
                        numberEl.textContent = `슬라이드 ${index + 1}`;
                    }
                });
                
                // 서버로 순서 변경 요청
                this.updateSlideOrder(chasiId, slideOrders);
            }
        });
    },

    // 슬라이드 순서 업데이트
    updateSlideOrder: async function(chasiId, slideOrders) {
        try {
            const data = await apiRequest(`/teacher/api/chasis/${chasiId}/slides/reorder/`, {
                method: 'POST',
                body: JSON.stringify({
                    slide_orders: slideOrders
                })
            });
            
            if (data.success) {
                showSuccess('슬라이드 순서가 변경되었습니다.');
            }
        } catch (error) {
            showError('순서 변경 중 오류가 발생했습니다.');
            this.loadSlides(chasiId);
        }
    },

    // 콘텐츠 선택
    selectContent: function(chasiId, contentId, title) {
        const radio = document.querySelector(`input[name="content_id_${chasiId}"][value="${contentId}"]`);
        if (radio) {
            radio.checked = true;
            document.getElementById(`add-slide-btn-${chasiId}`).disabled = false;
            
            // 선택 효과
            document.querySelectorAll(`#content-list-${chasiId} .content-item`).forEach(item => {
                item.classList.remove('bg-purple-50', 'border-purple-300');
            });
            radio.closest('.content-item').classList.add('bg-purple-50', 'border-purple-300');
        }
    },

    // 슬라이드 추가
    addSlide: async function(chasiId) {
        const form = document.getElementById(`slide-form-${chasiId}`);
        const formData = new FormData(form);
        const selectedContent = document.querySelector(`input[name="content_id_${chasiId}"]:checked`);
        
        if (!selectedContent) {
            showError('콘텐츠를 선택해주세요.');
            return;
        }
        
        formData.append('content_id', selectedContent.value);
        
        // 버튼 비활성화
        const btn = document.getElementById(`add-slide-btn-${chasiId}`);
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>추가 중...';
        
        try {
            const response = await submitForm(`/teacher/api/chasis/${chasiId}/slides/add/`, formData);
            
            if (response.success) {
                showSuccess('슬라이드가 추가되었습니다.');
                
                // 폼 초기화
                form.reset();
                document.querySelectorAll(`input[name="content_id_${chasiId}"]`).forEach(radio => {
                    radio.checked = false;
                });
                document.querySelectorAll(`#content-list-${chasiId} .content-item`).forEach(item => {
                    item.classList.remove('bg-purple-50', 'border-purple-300');
                });
                
                // 슬라이드 목록 다시 로드
                this.loadSlides(chasiId);
                
                // 트리 새로고침 (슬라이드 개수 업데이트)
                refreshTree();
            }
        } catch (error) {
            showError(error.message || '슬라이드 추가 중 오류가 발생했습니다.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-plus mr-2"></i>슬라이드 추가';
        }
    },

    // 슬라이드 삭제
    deleteSlide: async function(slideId, chasiId) {
        if (!confirm('정말 이 슬라이드를 삭제하시겠습니까?')) {
            return;
        }
        
        try {
            const response = await apiRequest(`/teacher/api/slides/${slideId}/delete/`, {
                method: 'POST',
                body: JSON.stringify({ chasi_id: chasiId })
            });
            
            if (response.success) {
                showSuccess('슬라이드가 삭제되었습니다.');
                
                // 슬라이드 요소 제거 애니메이션
                const slideElement = document.getElementById(`slide-${slideId}`);
                if (slideElement) {
                    slideElement.style.opacity = '0';
                    slideElement.style.transform = 'translateX(-100%)';
                    slideElement.style.transition = 'all 0.3s ease';
                    setTimeout(() => {
                        this.loadSlides(chasiId);
                        refreshTree(); // 트리 새로고침
                    }, 300);
                }
            }
        } catch (error) {
            showError(error.message || '삭제 중 오류가 발생했습니다.');
        }
    },

    // 슬라이드 수정
    editSlide: function(slideId, chasiId) {
        // 새 창에서 수정 페이지 열기
        window.open(`/teacher/slides/${slideId}/edit/`, '_blank');
    },

    // 드롭존 설정
    setupDropZone: function(chasiId) {
        const slidesContainer = document.getElementById(`slides-${chasiId}`);
        if (!slidesContainer) return;
        
        // 빈 상태일 때 드롭존 추가
        if (slidesContainer.children.length === 0) {
            slidesContainer.innerHTML = `
                <div class="slide-drop-zone" data-chasi-id="${chasiId}">
                    <i class="fas fa-layer-group mr-2"></i>
                    여기에 콘텐츠를 드래그하여 슬라이드 추가
                </div>
            `;
        }
        
        // 드롭 이벤트 설정
        slidesContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            
            // 드롭존 표시
            if (!slidesContainer.querySelector('.slide-drop-zone')) {
                const dropZone = document.createElement('div');
                dropZone.className = 'slide-drop-zone';
                dropZone.innerHTML = '<i class="fas fa-plus"></i> 여기에 놓기';
                slidesContainer.appendChild(dropZone);
            }
        });
        
        slidesContainer.addEventListener('drop', async (e) => {
            e.preventDefault();
            
            const contentId = e.dataTransfer.getData('contentId');
            const contentTitle = e.dataTransfer.getData('contentTitle');
            
            if (contentId) {
                // 슬라이드 추가
                const formData = new FormData();
                formData.append('content_id', contentId);
                formData.append('slide_title', '');
                formData.append('estimated_time', '5');
                
                try {
                    const response = await submitForm(
                        `/teacher/api/chasis/${chasiId}/slides/add/`, 
                        formData
                    );
                    
                    if (response.success) {
                        showSuccess(`"${contentTitle}" 슬라이드가 추가되었습니다.`);
                        this.loadSlides(chasiId);
                        refreshTree();
                    }
                } catch (error) {
                    showError('슬라이드 추가 중 오류가 발생했습니다.');
                }
            }
            
            // 임시 드롭존 제거
            const tempDropZone = slidesContainer.querySelector('.slide-drop-zone');
            if (tempDropZone && slidesContainer.children.length > 1) {
                tempDropZone.remove();
            }
        });
        
        slidesContainer.addEventListener('dragleave', (e) => {
            // 임시 드롭존 제거
            if (e.target.classList.contains('slide-drop-zone')) {
                const tempDropZone = slidesContainer.querySelector('.slide-drop-zone');
                if (tempDropZone && slidesContainer.children.length > 1) {
                    tempDropZone.remove();
                }
            }
        });
    },

    // sliders.js의 SlideManager 객체에 추가할 메서드

    // 선택된 콘텐츠를 리스트 상단으로 이동
// sliders.js의 SlideManager 객체에 추가

// 선택된 콘텐츠를 리스트 상단으로 이동
// 선택된 콘텐츠를 리스트 상단으로 이동
moveContentToTop: function(chasiId, contentId) {
    console.log('=== SlideManager.moveContentToTop 시작 ===');
    console.log('chasiId:', chasiId, 'contentId:', contentId);
    
    const container = document.getElementById(`content-list-${chasiId}`);
    console.log('컨테이너:', container);
    
    if (!container) {
        console.error('컨테이너를 찾을 수 없음');
        return;
    }
    
    const contentElement = container.querySelector(`[data-content-id="${contentId}"]`);
    console.log('이동할 콘텐츠 엘리먼트:', contentElement);
    
    if (!contentElement) {
        console.error('콘텐츠 엘리먼트를 찾을 수 없음');
        return;
    }
    
    // draggable 속성이 없으면 추가
    if (!contentElement.hasAttribute('draggable')) {
        contentElement.setAttribute('draggable', 'true');
        console.log('draggable 속성 추가');
    }
    
    // 애니메이션 효과를 위한 클래스 추가
    contentElement.style.transition = 'all 0.3s ease';
    contentElement.style.backgroundColor = '#f3e8ff';
    console.log('애니메이션 스타일 적용');
    
    // 맨 위로 이동
    container.insertBefore(contentElement, container.firstChild);
    console.log('엘리먼트 이동 완료');
    
    // 선택 스타일 추가
    contentElement.classList.add('selected', 'bg-purple-50');
    console.log('선택 스타일 추가');
    
    // 애니메이션 후 원래 배경색으로
    setTimeout(() => {
        contentElement.style.backgroundColor = '';
        console.log('배경색 원복');
    }, 300);
    
    console.log('=== SlideManager.moveContentToTop 종료 ===');
},


moveContentToTop_0622: function(chasiId, contentId) {
    console.log('=== SlideManager.moveContentToTop 시작 ===');
    console.log('chasiId:', chasiId, 'contentId:', contentId);
    
    const container = document.getElementById(`content-list-${chasiId}`);
    console.log('컨테이너:', container);
    
    if (!container) {
        console.error('컨테이너를 찾을 수 없음');
        return;
    }
    
    const contentElement = container.querySelector(`[data-content-id="${contentId}"]`);
    console.log('이동할 콘텐츠 엘리먼트:', contentElement);
    
    if (!contentElement) {
        console.error('콘텐츠 엘리먼트를 찾을 수 없음');
        return;
    }
    
    // 애니메이션 효과를 위한 클래스 추가
    contentElement.style.transition = 'all 0.3s ease';
    contentElement.style.backgroundColor = '#f3e8ff';
    console.log('애니메이션 스타일 적용');
    
    // 맨 위로 이동
    container.insertBefore(contentElement, container.firstChild);
    console.log('엘리먼트 이동 완료');
    
    // 선택 스타일 추가
    contentElement.classList.add('selected', 'bg-purple-50');
    console.log('선택 스타일 추가');
    
    // 애니메이션 후 원래 배경색으로
    setTimeout(() => {
        contentElement.style.backgroundColor = '';
        console.log('배경색 원복');
    }, 300);
    
    console.log('=== SlideManager.moveContentToTop 종료 ===');
},

// 선택 해제 시 원래 위치로 (옵션)
moveContentToOriginalPosition: function(chasiId, contentId) {
    // 전체 리스트를 다시 로드하거나
    // 또는 원래 순서를 기억해두었다가 복원
    this.loadContents(chasiId);
}

// sliders.js의 SlideManager 객체 안에 추가




// window에 전역 함수로 등록 (onclick에서 호출하기 위해)

};






