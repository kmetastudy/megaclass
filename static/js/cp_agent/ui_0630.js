// static/js/cp_agent/ui.js - UI 컨트롤 함수들 (수정됨)

/* ========== 패널 관리 ========== */

/**
 * 패널 토글
 */
function togglePanel(panel) {
    debugLog('UI', `패널 토글: ${panel}`);
    
    const $panel = $(`#${panel}Panel`);
    const $toggleBtn = $(`#${panel}ToggleBtn`);
    const $middlePanel = $('#middlePanel');
    const $rightPanel = $('#rightPanel');
    
    if ($panel.hasClass('panel-collapsed')) {
        // 패널 열기
        $panel.removeClass('panel-collapsed');
        $toggleBtn.hide();
        $middlePanel.removeClass('w-1/2').addClass('w-1/3');
        $rightPanel.removeClass('w-1/2').addClass('w-1/3');
        
        debugLog('UI', `${panel} 패널 열림`);
    } else {
        // 패널 닫기
        $panel.addClass('panel-collapsed');
        $toggleBtn.show();
        $middlePanel.removeClass('w-1/3').addClass('w-1/2');
        $rightPanel.removeClass('w-1/3').addClass('w-1/2');
        
        debugLog('UI', `${panel} 패널 닫힘`);
    }
    
    // 에디터 크기 조정
    setTimeout(() => {
        if (window.CPAgent && CPAgent.Editor && typeof CPAgent.Editor.resize === 'function') {
            CPAgent.Editor.resize();
        }
    }, 300);
}

/* ========== 탭 관리 ========== */

/**
 * 메인 탭 전환 (문항/템플릿)
 */
function switchTab(tab) {
    debugLog('UI', `메인 탭 전환: ${tab}`);
    
    $('.tab-btn').removeClass('border-orange-400 bg-white text-gray-700')
                 .addClass('border-transparent text-gray-600');
    $(`.tab-btn[data-tab="${tab}"]`)
                 .removeClass('border-transparent text-gray-600')
                 .addClass('border-orange-400 bg-white text-gray-700');
    
    $('.tab-content').removeClass('active').hide();
    $(`#${tab}Tab`).addClass('active').show();
    
    // 탭별 추가 작업
    if (tab === 'contents') {
        // 콘텐츠 탭 활성화 시 검색 실행
        if (window.CPAgent && CPAgent.Data && typeof CPAgent.Data.searchContents === 'function') {
            CPAgent.Data.searchContents();
        }
    } else if (tab === 'templates') {
        // 템플릿 탭 활성화 시 검색 실행
        if (window.CPAgent && CPAgent.Data && typeof CPAgent.Data.searchTemplates === 'function') {
            CPAgent.Data.searchTemplates();
        }
    }
}

/**
 * 미리보기 탭 전환
 */
function switchPreviewTab(tab) {
    debugLog('UI', `미리보기 탭 전환: ${tab}`);
    
    // 모든 탭 버튼 스타일 초기화
    $('.preview-tab-btn').removeClass('border-gray-600 bg-white text-gray-700')
                         .addClass('border-transparent text-gray-600');
    
    // 선택된 탭 버튼 활성화
    $(`.preview-tab-btn[data-tab="${tab}"]`)
                         .removeClass('border-transparent text-gray-600')
                         .addClass('border-gray-600 bg-white text-gray-700');
    
    // 모든 탭 콘텐츠 숨기기
    $('.preview-tab-content').removeClass('active').hide();
    
    // 선택된 탭 콘텐츠 보이기
    $(`#${tab}Tab`).addClass('active').show();
    
    // 탭별 특별 처리
    setTimeout(() => {
        if (tab === 'html') {
            // HTML 에디터 리프레시 - window 참조로 수정
            if (window.htmlEditorInstance && typeof window.htmlEditorInstance.refresh === 'function') {
                window.htmlEditorInstance.refresh();
            }
            if (window.answerEditor && typeof window.answerEditor.refresh === 'function') {
                window.answerEditor.refresh();
            }
            if (window.metaEditorInstance_html && typeof window.metaEditorInstance_html.refresh === 'function') {
                window.metaEditorInstance_html.refresh();
            }
            if (window.tagsEditorInstance_html && typeof window.tagsEditorInstance_html.refresh === 'function') {
                window.tagsEditorInstance_html.refresh();
            }
            
            // HTML탭 아코디언 초기화
            if (typeof initializeHtmlTabAccordions === 'function') {
                initializeHtmlTabAccordions();
            }
        } else if (tab === 'text') {
            // 텍스트 편집 탭 활성화 시 이벤트 바인딩
            if (window.CPAgent && CPAgent.TextEditing && typeof CPAgent.TextEditing.bindTextEditingEvents === 'function') {
                CPAgent.TextEditing.bindTextEditingEvents();
            }
        }
    }, 100);
}

/* ========== 아코디언 관리 ========== */

/**
 * 아코디언 토글
 */
function toggleAccordion(header) {
    debugLog('UI', '아코디언 토글');
    
    const content = header.nextElementSibling;
    const icon = header.querySelector('i');
    
    content.classList.toggle('active');
    icon.classList.toggle('fa-chevron-down');
    icon.classList.toggle('fa-chevron-up');
    
    // 아코디언 열릴 때 에디터 리프레시
    if (content.classList.contains('active')) {
        setTimeout(() => {
            const editors = content.querySelectorAll('.CodeMirror');
            editors.forEach(editorElement => {
                if (editorElement.CodeMirror) {
                    editorElement.CodeMirror.refresh();
                }
            });
        }, 300);
    }
}

/* ========== 모달 관리 ========== */

/**
 * 템플릿 모달 열기
 */
function openTemplateModal() {
    debugLog('UI', '템플릿 모달 열기');
    
    $('#templateModal').removeClass('hidden').addClass('fade-in');
    
    // 폼 초기화
    $('#templateForm')[0].reset();
    $('#templateFormCategory').val('');
    $('#templateFormType').val('').prop('disabled', true);
    $('#templateName').val('');
    $('#templateHtml').val('');
    $('#templateAnswer').val('{}');
    $('#templateMeta').val('{}');
    $('#templateJs').val('');
    
    // 유효성 검사 스타일 초기화
    $('.border-red-300, .border-green-300').removeClass('border-red-300 border-green-300');
    $('.error-message').remove();
    
    // 폼 포커스
    setTimeout(() => {
        $('#templateName').focus();
    }, 300);
}

/**
 * 템플릿 모달 닫기
 */
function closeTemplateModal() {
    debugLog('UI', '템플릿 모달 닫기');
    
    $('#templateModal').addClass('hidden').removeClass('fade-in');
    
    // 폼 데이터 정리
    setTimeout(() => {
        $('#templateForm')[0].reset();
        $('.border-red-300, .border-green-300').removeClass('border-red-300 border-green-300');
        $('.error-message').remove();
    }, 300);
}

/**
 * 로딩 모달 표시
 */
function showLoadingModal(message = 'AI가 문항을 생성하고 있습니다...') {
    debugLog('UI', '로딩 모달 표시', message);
    
    $('#loadingModal .text-gray-700').text(message);
    $('#loadingModal').removeClass('hidden').addClass('fade-in');
}

/**
 * 로딩 모달 숨기기
 */
function hideLoadingModal() {
    debugLog('UI', '로딩 모달 숨기기');
    
    $('#loadingModal').addClass('hidden').removeClass('fade-in');
}

/* ========== 리스트 아이템 관리 ========== */

/**
 * 콘텐츠 리스트 아이템 생성
 */
function createContentListItem(content) {
    const previewText = content.preview ? 
        `<div class="text-xs text-gray-400 mt-1 truncate" title="${content.preview}">${content.preview}</div>` : '';
    
    const createdDate = content.created_at ? new Date(content.created_at).toLocaleDateString() : '';
    
    return $(`
        <div class="card card-clickable slide-up" onclick="loadContent(${content.id})" data-content-id="${content.id}">
            <h4 class="font-medium text-gray-800 mb-1" title="${content.title}">${content.title}</h4>
            <div class="flex items-center text-xs text-gray-500 mt-1 mb-1">
                <span class="badge badge-secondary mr-2">
                    ${content.content_type_name || '타입 없음'}
                </span>
                <span>${createdDate}</span>
            </div>
            ${previewText}
            <div class="mt-2 flex justify-between items-center">
                <div class="text-xs text-gray-400">
                    <i class="fas fa-eye mr-1"></i>클릭하여 로드
                </div>
                <div class="text-xs text-gray-400">
                    ID: ${content.id}
                </div>
            </div>
        </div>
    `);
}

/**
 * 템플릿 리스트 아이템 생성
 */
function createTemplateListItem(template) {
    const categoryName = template.category_name || '카테고리 없음';
    const typeName = template.content_type_name || '타입 없음';
    const createdDate = template.created_at ? new Date(template.created_at).toLocaleDateString() : '';
    
    return $(`
        <div class="card card-clickable slide-up" onclick="selectTemplateFromList(${template.id})" data-template-id="${template.id}">
            <h4 class="font-medium text-gray-800 mb-1" title="${template.title}">${template.title}</h4>
            <div class="flex items-center text-xs text-gray-500 mt-1 mb-1">
                <span class="badge badge-primary mr-2">
                    ${categoryName}
                </span>
                <span class="badge badge-secondary mr-2">
                    ${typeName}
                </span>
                <span>${createdDate}</span>
            </div>
            <div class="mt-2 flex justify-between items-center">
                <div class="text-xs text-gray-400">
                    <i class="fas fa-mouse-pointer mr-1"></i>클릭하여 적용
                </div>
                <div class="text-xs text-gray-400">
                    ID: ${template.id}
                </div>
            </div>
        </div>
    `);
}

/* ========== 상태 표시 관리 ========== */

/**
 * 로딩 상태 표시
 */
function showLoadingState($container, message = '로딩 중...') {
    debugLog('UI', '로딩 상태 표시', message);
    
    $container.html(`
        <div class="status-indicator status-loading flex items-center justify-center py-8">
            <i class="fas fa-spinner fa-spin mr-2 text-blue-500"></i>
            <span class="text-gray-600">${message}</span>
        </div>
    `);
}

/**
 * 에러 상태 표시
 */
function showErrorState($container, message = '오류가 발생했습니다') {
    debugLog('UI', '에러 상태 표시', message);
    
    $container.html(`
        <div class="status-indicator status-error flex items-center justify-center py-8">
            <i class="fas fa-exclamation-triangle mr-2 text-red-500"></i>
            <span class="text-red-600">${message}</span>
        </div>
    `);
}

/**
 * 빈 상태 표시
 */
function showEmptyState($container, message = '결과가 없습니다', icon = 'fas fa-inbox') {
    debugLog('UI', '빈 상태 표시', message);
    
    $container.html(`
        <div class="text-center text-gray-400 py-8">
            <i class="${icon} text-6xl mb-4"></i>
            <p class="text-lg mb-2">${message}</p>
            <p class="text-sm">검색 조건을 변경해보세요</p>
        </div>
    `);
}

/* ========== 편집 컨트롤 관리 ========== */

/**
 * 편집 컨트롤 UI 업데이트
 */
function updateEditControls() {
    const changedTexts = $('.text-changed').length;
    const changedImages = $('.editable-image[data-changed="true"]').length;
    const totalChanges = changedTexts + changedImages;
    
    debugLog('UI', '편집 컨트롤 업데이트', { changedTexts, changedImages, totalChanges });
    
    const $editControls = $('#editControls');
    
    if (totalChanges > 0) {
        $editControls.removeClass('hidden').addClass('slide-up');
        
        // 변경사항 수 표시
        const changeText = `변경사항: 텍스트 ${changedTexts}개, 이미지 ${changedImages}개`;
        $editControls.find('.changes-count').remove();
        $editControls.prepend(`<div class="changes-count text-xs text-blue-600 mb-2">${changeText}</div>`);
    } else {
        $editControls.addClass('hidden').removeClass('slide-up');
        $editControls.find('.changes-count').remove();
    }
}

/**
 * 편집 상태 표시 업데이트
 */
function updateEditStatus() {
    const editableWordCount = $('.editable-word').length;
    const editableImageCount = $('.editable-image').length;
    
    debugLog('UI', '편집 상태 업데이트', { editableWordCount, editableImageCount });
    
    const $editStatus = $('#editStatus');
    
    if (editableWordCount > 0 || editableImageCount > 0) {
        $editStatus.removeClass('hidden').addClass('slide-up');
        $('#editStatusText').text(`편집 가능한 요소: 텍스트 ${editableWordCount}개, 이미지 ${editableImageCount}개`);
    } else {
        $editStatus.addClass('hidden').removeClass('slide-up');
    }
}

/* ========== 알림 및 피드백 ========== */

/**
 * 진행률 표시기 표시
 */
function showProgressIndicator(message, progress = 0) {
    debugLog('UI', '진행률 표시기', { message, progress });
    
    const $indicator = $('#progressIndicator');
    if ($indicator.length === 0) {
        $('body').append(`
            <div id="progressIndicator" class="fixed bottom-4 left-4 bg-white border border-gray-300 rounded-lg p-3 shadow-lg z-50">
                <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                    <div>
                        <div class="text-sm font-medium text-gray-800" id="progressMessage">${message}</div>
                        <div class="w-48 bg-gray-200 rounded-full h-2 mt-1">
                            <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" id="progressBar" style="width: ${progress}%"></div>
                        </div>
                    </div>
                    <button onclick="hideProgressIndicator()" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `);
    } else {
        $('#progressMessage').text(message);
        $('#progressBar').css('width', progress + '%');
    }
}

/**
 * 진행률 표시기 숨기기
 */
function hideProgressIndicator() {
    debugLog('UI', '진행률 표시기 숨기기');
    
    $('#progressIndicator').fadeOut(300, function() {
        $(this).remove();
    });
}

/**
 * 렌더링 상태 표시
 */
function showRenderStatus(message, type = 'info') {
    debugLog('UI', '렌더링 상태 표시', { message, type });
    
    const $renderStatus = $('#renderStatus');
    const $renderStatusText = $('#renderStatusText');
    
    const iconClass = type === 'success' ? 'fa-check-circle text-green-600' :
                     type === 'warning' ? 'fa-exclamation-triangle text-yellow-600' :
                     'fa-info-circle text-blue-600';
    
    $renderStatusText.html(`<i class="fas ${iconClass} mr-1"></i>${message}`);
    $renderStatus.removeClass('hidden');
    
    // 3초 후 자동 숨기기 (info인 경우)
    if (type === 'info') {
        setTimeout(() => {
            $renderStatus.addClass('hidden');
        }, 3000);
    }
}

/* ========== 유틸리티 함수들 ========== */

/**
 * 카드 애니메이션 적용
 */
function animateCards($container) {
    debugLog('UI', '카드 애니메이션 적용');
    
    $container.find('.card').each(function(index) {
        const $card = $(this);
        $card.css({
            'opacity': '0',
            'transform': 'translateY(20px)'
        });
        
        setTimeout(() => {
            $card.css({
                'opacity': '1',
                'transform': 'translateY(0)',
                'transition': 'all 0.3s ease-out'
            });
        }, index * 50);
    });
}

/**
 * 활성 탭 확인
 */
function getActiveTab() {
    const activeMainTab = $('.tab-btn.border-orange-400').data('tab') || 'contents';
    const activePreviewTab = $('.preview-tab-btn.border-gray-600').data('tab') || 'render';
    
    return {
        main: activeMainTab,
        preview: activePreviewTab
    };
}

/**
 * UI 상태 초기화
 */
function resetUIState() {
    debugLog('UI', 'UI 상태 초기화');
    
    // 모든 모달 숨기기
    $('.modal').addClass('hidden').removeClass('fade-in');
    
    // 편집 컨트롤 숨기기
    $('#editControls').addClass('hidden');
    $('#editStatus').addClass('hidden');
    
    // 진행률 표시기 숨기기
    hideProgressIndicator();
    
    // 렌더링 상태 숨기기
    $('#renderStatus').addClass('hidden');
    
    // 토스트 메시지 제거
    $('.toast-notification').remove();
    
    // 기본 탭으로 전환
    switchTab('contents');
    switchPreviewTab('render');
}

/* ========== 전역 UI 네임스페이스 ========== */
window.CPAgent.UI = {
    togglePanel,
    switchTab,
    switchPreviewTab,
    toggleAccordion,
    openTemplateModal,
    closeTemplateModal,
    showLoadingModal,
    hideLoadingModal,
    createContentListItem,
    createTemplateListItem,
    showLoadingState,
    showErrorState,
    showEmptyState,
    updateEditControls,
    updateEditStatus,
    showProgressIndicator,
    hideProgressIndicator,
    showRenderStatus,
    animateCards,
    getActiveTab,
    resetUIState
};