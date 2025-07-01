// static/js/cp_agent/ui.js - UI 컨트롤 함수들

/* ========== 패널 관리 ========== */

/**
 * 패널 토글
 */
function togglePanel(panel) {
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
    } else {
        // 패널 닫기
        $panel.addClass('panel-collapsed');
        $toggleBtn.show();
        $middlePanel.removeClass('w-1/3').addClass('w-1/2');
        $rightPanel.removeClass('w-1/3').addClass('w-1/2');
    }
}

/* ========== 탭 관리 ========== */

/**
 * 메인 탭 전환 (문항/템플릿)
 */
function switchTab(tab) {
    $('.tab-btn').removeClass('border-orange-400 bg-white text-gray-700')
                 .addClass('border-transparent text-gray-600');
    $(`.tab-btn[data-tab="${tab}"]`)
                 .removeClass('border-transparent text-gray-600')
                 .addClass('border-orange-400 bg-white text-gray-700');
    
    $('.tab-content').removeClass('active');
    $(`#${tab}Tab`).addClass('active');
}

/**
 * 미리보기 탭 전환
 */
function switchPreviewTab(tab) {
    debugLog('UI', '탭 전환:', tab);
    
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
    
    // 특별한 경우 처리
    if (tab === 'html' && htmlEditorInstance) {
        // HTML 에디터 리프레시
        setTimeout(() => {
            htmlEditorInstance.refresh();
        }, 100);
    }
}

/* ========== 아코디언 관리 ========== */

/**
 * 아코디언 토글
 */
function toggleAccordion(header) {
    const content = header.nextElementSibling;
    const icon = header.querySelector('i');
    
    content.classList.toggle('active');
    icon.classList.toggle('fa-chevron-down');
    icon.classList.toggle('fa-chevron-up');
}

/* ========== 모달 관리 ========== */

/**
 * 템플릿 모달 열기
 */
function openTemplateModal() {
    $('#templateModal').removeClass('hidden').addClass('fade-in');
    
    // 폼 초기화
    $('#templateForm')[0].reset();
    $('#templateFormCategory').val('');
    $('#templateFormType').val('');
    $('#templateName').val('');
    $('#templateHtml').val('');
    $('#templateAnswer').val('{}');
    $('#templateMeta').val('{}');
    $('#templateJs').val('');
    
    // 폼 포커스
    setTimeout(() => {
        $('#templateName').focus();
    }, 300);
}

/**
 * 템플릿 모달 닫기
 */
function closeTemplateModal() {
    $('#templateModal').addClass('hidden').removeClass('fade-in');
}

/**
 * 로딩 모달 표시
 */
function showLoadingModal(message = 'AI가 문항을 생성하고 있습니다...') {
    $('#loadingModal .text-gray-700').text(message);
    $('#loadingModal').removeClass('hidden').addClass('fade-in');
}

/**
 * 로딩 모달 숨기기
 */
function hideLoadingModal() {
    $('#loadingModal').addClass('hidden').removeClass('fade-in');
}

/* ========== 리스트 아이템 관리 ========== */

/**
 * 콘텐츠 리스트 아이템 생성
 */
function createContentListItem(content) {
    const previewText = content.preview ? 
        `<div class="text-xs text-gray-400 mt-1 truncate">${content.preview}</div>` : '';
    
    return $(`
        <div class="card card-clickable slide-up" onclick="loadContent(${content.id})">
            <h4 class="font-medium text-gray-800">${content.title}</h4>
            <div class="flex items-center text-xs text-gray-500 mt-1">
                <span class="badge badge-secondary mr-2">
                    ${content.content_type_name}
                </span>
                <span>${content.created_at}</span>
            </div>
            ${previewText}
        </div>
    `);
}

/**
 * 템플릿 리스트 아이템 생성
 */
function createTemplateListItem(template) {
    const categoryName = template.category_name || '카테고리 없음';
    const typeName = template.content_type_name || '타입 없음';
    
    return $(`
        <div class="card card-clickable slide-up" onclick="selectTemplateFromList(${template.id})">
            <h4 class="font-medium text-gray-800">${template.title}</h4>
            <div class="flex items-center text-xs text-gray-500 mt-1">
                <span class="badge badge-primary mr-2">
                    ${categoryName}
                </span>
                <span class="badge badge-secondary mr-2">
                    ${typeName}
                </span>
                <span>${template.created_at}</span>
            </div>
        </div>
    `);
}

/* ========== 상태 표시 관리 ========== */

/**
 * 로딩 상태 표시
 */
function showLoadingState($container, message = '로딩 중...') {
    $container.html(`
        <div class="status-indicator status-loading">
            <i class="fas fa-spinner fa-spin"></i>
            ${message}
        </div>
    `);
}

/**
 * 에러 상태 표시
 */
function showErrorState($container, message = '오류가 발생했습니다') {
    $container.html(`
        <div class="status-indicator status-error">
            <i class="fas fa-exclamation-triangle"></i>
            ${message}
        </div>
    `);
}

/**
 * 빈 상태 표시
 */
function showEmptyState($container, message = '결과가 없습니다', icon = 'fas fa-inbox') {
    $container.html(`
        <div class="text-center text-gray-400 py-8">
            <i class="${icon} text-6xl mb-4"></i>
            <p>${message}</p>
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
    
    if (totalChanges > 0) {
        $('#editControls').removeClass('hidden').addClass('slide-up');
    } else {
        $('#editControls').addClass('hidden').removeClass('slide-up');
    }
}

/**
 * 편집 상태 표시 업데이트
 */
function updateEditStatus() {
    const editableWordCount = $('.editable-word').length;
    const editableImageCount = $('.editable-image').length;
    
    if (editableWordCount > 0 || editableImageCount > 0) {
        $('#editStatus').removeClass('hidden').addClass('slide-up');
        $('#editStatusText').text(`편집 가능한 텍스트: ${editableWordCount}개, 이미지: ${editableImageCount}개`);
    } else {
        $('#editStatus').addClass('hidden').removeClass('slide-up');
    }
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
    updateEditStatus
};