// static/js/cp_agent/events.js - 이벤트 바인딩 시스템

/* ========== 메인 이벤트 바인딩 ========== */

/**
 * 모든 이벤트 바인딩
 */
function bindEvents() {
    debugLog('EVENTS', '이벤트 바인딩 시작');
    
    try {
        // 기존 이벤트 모두 제거 (중복 방지)
        unbindAllEvents();
        
        // 각 영역별 이벤트 바인딩
        bindContentSearchEvents();
        bindTemplateSearchEvents();
        bindFormEvents();
        bindImageEvents();
        bindTemplateFormEvents();
        bindKeyboardEvents();
        bindWindowEvents();
        
        debugLog('EVENTS', '모든 이벤트 바인딩 완료');
        
    } catch (error) {
        debugLog('EVENTS', '이벤트 바인딩 실패', error);
        showToast('이벤트 바인딩 중 오류가 발생했습니다', 'error');
    }
}

/**
 * 모든 이벤트 언바인딩
 */
function unbindAllEvents() {
    debugLog('EVENTS', '기존 이벤트 제거');
    
    // 검색 관련 이벤트 제거
    $('#contentCategory').off('change');
    $('#contentType').off('change');
    $('#contentCourse').off('change');
    $('#contentChapter').off('change');
    $('#contentSearch').off('keypress');
    
    // 템플릿 관련 이벤트 제거
    $('#template_select').off('change');
    $('#templateCategory').off('change');
    $('#templateType').off('change');
    $('#templateSearch').off('keypress');
    
    // 이미지 관련 이벤트 제거
    $('#imageUpload').off('change');
    
    // 폼 관련 이벤트 제거
    $('#contentForm').off('submit');
    $('#templateForm').off('submit');
}

/* ========== 콘텐츠 검색 이벤트 ========== */

/**
 * 콘텐츠 검색 관련 이벤트 바인딩
 */
function bindContentSearchEvents() {
    debugLog('EVENTS', '콘텐츠 검색 이벤트 바인딩');
    
    // 카테고리 선택 시 해당 카테고리의 타입만 표시
    $('#contentCategory').on('change.contentSearch', function() {
        const categoryId = $(this).val();
        debugLog('EVENTS', '컨텐츠 카테고리 변경', categoryId);
        
        if (categoryId) {
            CPAgent.Data.loadContentTypesByCategory(categoryId, ['#contentType', '#content_type']);
        } else {
            CPAgent.Data.loadAllContentTypes();
        }
        
        $('#contentType').val('');
        CPAgent.Data.searchContents();
    });
    
    // 컨텐츠 타입 변경 시 검색
    $('#contentType').on('change.contentSearch', function() {
        debugLog('EVENTS', '컨텐츠 타입 변경', $(this).val());
        CPAgent.Data.searchContents();
    });
    
    // 코스 선택 시 챕터 로드
    $('#contentCourse').on('change.contentSearch', function() {
        const courseId = $(this).val();
        debugLog('EVENTS', '코스 변경', courseId);
        
        if (courseId) {
            CPAgent.Data.loadChaptersByCourse(courseId)
                .then(() => {
                    bindChapterChangeEvent();
                })
                .catch(error => {
                    debugLog('EVENTS', '챕터 로드 실패', error);
                });
        } else {
            const $chapterSelect = $('#contentChapter');
            $chapterSelect.empty().append('<option value="">대단원 선택</option>');
            $chapterSelect.prop('disabled', true);
        }
        
        CPAgent.Data.searchContents();
    });
    
    // 검색어 입력 시 엔터키로 검색
    $('#contentSearch').on('keypress.contentSearch', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            CPAgent.Data.searchContents();
        }
    });
    
    // 실시간 검색 (디바운스 적용)
    let searchTimeout;
    $('#contentSearch').on('input.contentSearch', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            CPAgent.Data.searchContents();
        }, 500);
    });
}

/**
 * 챕터 변경 이벤트 바인딩
 */
function bindChapterChangeEvent() {
    $('#contentChapter').off('change.chapter').on('change.chapter', function() {
        debugLog('EVENTS', '챕터 변경', $(this).val());
        CPAgent.Data.searchContents();
    });
}

/* ========== 템플릿 검색 이벤트 ========== */

/**
 * 템플릿 검색 관련 이벤트 바인딩
 */
function bindTemplateSearchEvents() {
    debugLog('EVENTS', '템플릿 검색 이벤트 바인딩');
    
    // 템플릿 선택 시 내용 적용 (재귀 방지)
    $('#template_select').on('change.templateSelect', function() {
        const templateId = $(this).val();
        debugLog('EVENTS', '템플릿 select 변경', templateId);
        
        if (templateId) {
            CPAgent.Template.applyTemplateData(templateId);
        }
    });
    
    // 템플릿 검색 카테고리 변경 시
    $('#templateCategory').on('change.templateSearch', function() {
        const categoryId = $(this).val();
        debugLog('EVENTS', '템플릿 카테고리 변경', categoryId);
        
        if (categoryId) {
            CPAgent.Data.loadContentTypesByCategory(categoryId, ['#templateType'])
                .then(() => {
                    CPAgent.Data.searchTemplates();
                });
        } else {
            CPAgent.Data.loadAllContentTypes();
            CPAgent.Data.searchTemplates();
        }
    });
    
    $('#templateType').on('change.templateSearch', function() {
        debugLog('EVENTS', '템플릿 타입 변경', $(this).val());
        CPAgent.Data.searchTemplates();
    });
    
    // 템플릿 검색어 엔터키
    $('#templateSearch').on('keypress.templateSearch', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            CPAgent.Data.searchTemplates();
        }
    });
    
    // 실시간 템플릿 검색 (디바운스 적용)
    let templateSearchTimeout;
    $('#templateSearch').on('input.templateSearch', function() {
        clearTimeout(templateSearchTimeout);
        templateSearchTimeout = setTimeout(() => {
            CPAgent.Data.searchTemplates();
        }, 500);
    });
}

/* ========== 폼 이벤트 ========== */

/**
 * 폼 관련 이벤트 바인딩
 */
function bindFormEvents() {
    debugLog('EVENTS', '폼 이벤트 바인딩');
    
    // 콘텐츠 폼 제출 방지
    $('#contentForm').on('submit.preventSubmit', function(e) {
        e.preventDefault();
        debugLog('EVENTS', '콘텐츠 폼 제출 차단');
    });
    
    // 템플릿 폼 제출 방지
    $('#templateForm').on('submit.preventSubmit', function(e) {
        e.preventDefault();
        debugLog('EVENTS', '템플릿 폼 제출 차단');
    });
    
    // 필수 필드 실시간 유효성 검사
    $('#title').on('input.validation', function() {
        validateRequiredField($(this), '제목을 입력하세요');
    });
    
    $('#content_type').on('change.validation', function() {
        validateRequiredField($(this), '콘텐츠 타입을 선택하세요');
    });
    
    $('#prompt_content').on('input.validation', function() {
        validateRequiredField($(this), '문항 생성 지시사항을 입력하세요');
    });
}

/**
 * 필수 필드 유효성 검사
 */
function validateRequiredField($field, message) {
    const value = $field.val().trim();
    
    if (value.length > 0) {
        $field.removeClass('border-red-300').addClass('border-green-300');
        $field.next('.error-message').remove();
    } else {
        $field.removeClass('border-green-300').addClass('border-red-300');
        
        if (!$field.next('.error-message').length) {
            $field.after(`<div class="error-message text-red-500 text-xs mt-1">${message}</div>`);
        }
    }
}

/* ========== 이미지 이벤트 ========== */

/**
 * 이미지 관련 이벤트 바인딩
 */
function bindImageEvents() {
    debugLog('EVENTS', '이미지 이벤트 바인딩');
    
    // 이미지 업로드 이벤트
    $('#imageUpload').on('change.imageUpload', function(e) {
        const file = e.target.files[0];
        debugLog('EVENTS', '이미지 파일 선택', file?.name);
        
        if (file && currentEditingImage) {
            CPAgent.Image.uploadImage(file, currentEditingImage);
        }
        
        // 파일 입력 초기화
        $(this).val('');
    });
    
    // 드래그 앤 드롭 이벤트 (향후 구현)
    bindDragDropEvents();
}

/**
 * 드래그 앤 드롭 이벤트 바인딩
 */
function bindDragDropEvents() {
    debugLog('EVENTS', '드래그 앤 드롭 이벤트 바인딩');
    
    // 전체 화면에서 기본 드래그 이벤트 방지
    $(document).on('dragover.preventDefault', function(e) {
        e.preventDefault();
    });
    
    $(document).on('drop.preventDefault', function(e) {
        e.preventDefault();
    });
    
    // 편집 영역에서의 드래그 앤 드롭
    $('#editableContent').on('dragover.imageDrop', function(e) {
        e.preventDefault();
        $(this).addClass('drag-over');
    });
    
    $('#editableContent').on('dragleave.imageDrop', function(e) {
        e.preventDefault();
        $(this).removeClass('drag-over');
    });
    
    $('#editableContent').on('drop.imageDrop', function(e) {
        e.preventDefault();
        $(this).removeClass('drag-over');
        
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
            debugLog('EVENTS', '드래그 앤 드롭 이미지 감지', files[0].name);
            // 향후 구현: 새 이미지 추가 기능
            showToast('드래그 앤 드롭 이미지 추가 기능은 준비 중입니다', 'warning');
        }
    });
}

/* ========== 템플릿 폼 이벤트 ========== */

/**
 * 템플릿 폼 관련 이벤트 바인딩
 */
function bindTemplateFormEvents() {
    debugLog('EVENTS', '템플릿 폼 이벤트 바인딩');
    
    // 템플릿 폼 이벤트는 CPAgent.Template.bindTemplateEvents()에서 처리
    CPAgent.Template.bindTemplateEvents();
}

/* ========== 키보드 이벤트 ========== */

/**
 * 글로벌 키보드 이벤트 바인딩
 */
function bindKeyboardEvents() {
    debugLog('EVENTS', '키보드 이벤트 바인딩');
    
    // 글로벌 키보드 단축키
    $(document).on('keydown.globalShortcuts', function(e) {
        // Ctrl/Cmd + S: 저장
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            CPAgent.Content.saveContent();
            return false;
        }
        
        // Ctrl/Cmd + Enter: AI 생성
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            CPAgent.Content.requestAI();
            return false;
        }
        
        // F1: 도움말 (향후 구현)
        if (e.key === 'F1') {
            e.preventDefault();
            showToast('도움말 기능은 준비 중입니다', 'warning');
            return false;
        }
        
        // ESC: 모달 닫기
        if (e.key === 'Escape') {
            if ($('#templateModal').is(':visible')) {
                CPAgent.UI.closeTemplateModal();
            }
            if ($('#loadingModal').is(':visible')) {
                // 로딩 모달은 ESC로 닫지 않음
            }
        }
    });
    
    // 텍스트 에디터 키보드 이벤트
    $('#prompt_content').on('keydown.textareaShortcuts', function(e) {
        // Ctrl/Cmd + Enter: AI 생성
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            CPAgent.Content.requestAI();
        }
        
        // Tab 키로 들여쓰기
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = this.selectionStart;
            const end = this.selectionEnd;
            const value = $(this).val();
            
            $(this).val(value.substring(0, start) + '\t' + value.substring(end));
            this.selectionStart = this.selectionEnd = start + 1;
        }
    });
}

/* ========== 윈도우 이벤트 ========== */

/**
 * 윈도우 관련 이벤트 바인딩
 */
function bindWindowEvents() {
    debugLog('EVENTS', '윈도우 이벤트 바인딩');
    
    // 페이지 이탈 시 임시 파일 정리
    $(window).on('beforeunload.cleanup', function() {
        if (temporaryUploads.length > 0) {
            cleanupTemporaryUploads();
        }
    });
    
    // 윈도우 리사이즈 시 에디터 크기 조정
    let resizeTimeout;
    $(window).on('resize.editorResize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            CPAgent.Editor.resize();
        }, 250);
    });
    
    // 윈도우 포커스 이벤트
    $(window).on('focus.windowFocus', function() {
        debugLog('EVENTS', '윈도우 포커스');
        // 필요시 데이터 새로고침 등
    });
    
    $(window).on('blur.windowBlur', function() {
        debugLog('EVENTS', '윈도우 블러');
        // 자동 저장 등 (향후 구현)
    });
}

/* ========== 동적 이벤트 관리 ========== */

/**
 * 동적으로 생성되는 요소들에 대한 이벤트 바인딩
 */
function bindDynamicEvents() {
    debugLog('EVENTS', '동적 이벤트 바인딩');
    
    // 텍스트 편집 이벤트는 CPAgent.TextEditing에서 처리
    CPAgent.TextEditing.bindTextEditingEvents();
}

/**
 * 특정 영역의 이벤트 다시 바인딩
 */
function rebindEventsForElement($element) {
    debugLog('EVENTS', '특정 요소 이벤트 재바인딩');
    
    // 해당 요소 내의 편집 관련 이벤트만 다시 바인딩
    $element.find('.editable-word').off('dblclick mouseenter mouseleave');
    $element.find('.editable-image').off('click');
    
    // 호버 효과 다시 적용
    $element.find('.editable-word').on('mouseenter', function() {
        if (!$(this).hasClass('text-changed')) {
            $(this).css({
                'background-color': '#dbeafe',
                'border-color': '#93c5fd'
            });
        }
    }).on('mouseleave', function() {
        if (!$(this).hasClass('text-changed')) {
            $(this).css({
                'background-color': 'transparent',
                'border-color': 'transparent'
            });
        }
    });
}

/* ========== 이벤트 상태 확인 ========== */

/**
 * 이벤트 바인딩 상태 확인 (디버깅용)
 */
function checkEventBindings() {
    debugLog('EVENTS', '이벤트 바인딩 상태 확인');
    
    const elements = [
        '#contentCategory',
        '#contentType', 
        '#contentCourse',
        '#contentChapter',
        '#contentSearch',
        '#template_select',
        '#templateCategory',
        '#templateType',
        '#templateSearch',
        '#imageUpload'
    ];
    
    elements.forEach(selector => {
        const $el = $(selector);
        if ($el.length > 0) {
            const events = $._data($el[0], 'events');
            debugLog('EVENTS', `${selector} 이벤트`, events || 'None');
        } else {
            debugLog('EVENTS', `${selector} 요소 없음`);
        }
    });
}

/**
 * 특정 요소의 이벤트 제거
 */
function unbindElementEvents(selector) {
    debugLog('EVENTS', '특정 요소 이벤트 제거', selector);
    $(selector).off();
}

/* ========== 전역 이벤트 네임스페이스 ========== */
window.CPAgent.Events = {
    bind: bindEvents,
    unbindAll: unbindAllEvents,
    bindDynamic: bindDynamicEvents,
    rebindForElement: rebindEventsForElement,
    checkBindings: checkEventBindings,
    unbindElement: unbindElementEvents
};