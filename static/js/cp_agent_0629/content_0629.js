// static/js/cp_agent/content.js - 콘텐츠 관리 함수들

/* ========== 콘텐츠 CRUD 작업 ========== */

/**
 * 문항 로드
 */
function loadContent(contentId) {
    debugLog('CONTENT', '문항 로드 시작', contentId);
    
    const timer = new PerformanceTimer('문항 로드');
    
    $.get(`/cp/api/contents/${contentId}/`)
        .done(function(data) {
            debugLog('CONTENT', '문항 로드 완료', data);
            
            // 기본 정보 설정
            $('#title').val(data.title);
            $('#content_type').val(data.content_type);
            
            // 프롬프트 설정
            if (data.prompt) {
                $('#prompt_content').val(data.prompt);
            }
            
            // HTML 콘텐츠 설정
            if (data.page) {
                htmlEditorInstance.setValue(data.page);
                updatePreview();
            }
            
            // 답안 설정
            answerInputEditor.setValue(data.answer || '{}');
            answerEditor.setValue(data.answer || '{}');
            
            // 메타데이터와 태그 설정
            metaEditor.setValue(JSON.stringify(data.meta_data || {}, null, 2));
            tagsEditor.setValue(JSON.stringify(data.tags || {}, null, 2));
            
            // 전역 변수 업데이트
            currentContent = data;
            
            timer.end();
            showToast('문항을 불러왔습니다', 'success');
        })
        .fail(function(xhr) {
            debugLog('CONTENT', '문항 로드 실패', xhr);
            showToast('문항을 불러오는 중 오류가 발생했습니다', 'error');
        });
}

/**
 * AI 요청
 */
function requestAI() {
    debugLog('CONTENT', 'AI 요청 시작');
    
    const formData = {
        title: $('#title').val(),
        content_type: $('#content_type').val(),
        template_id: $('#template_select').val(),
        prompt: $('#prompt_content').val(),
        answer_input: answerInputEditor.getValue(),
        meta_data: metaEditor.getValue(),
        tags: tagsEditor.getValue()
    };
    
    // 유효성 검사
    if (!formData.title || !formData.content_type) {
        showToast('제목과 컨텐츠 타입은 필수입니다', 'error');
        return;
    }
    
    if (!formData.prompt.trim()) {
        showToast('문항 생성 지시사항을 입력해주세요', 'error');
        return;
    }
    
    debugLog('CONTENT', 'AI 요청 데이터', formData);
    
    CPAgent.UI.showLoadingModal();
    
    const timer = new PerformanceTimer('AI 문항 생성');
    
    $.ajax({
        url: '/cp/api/generate-content/',
        method: 'POST',
        data: JSON.stringify(formData),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(data) {
            debugLog('CONTENT', 'AI 요청 성공', data);
            
            // 생성된 콘텐츠 설정
            htmlEditorInstance.setValue(data.page || '');
            answerEditor.setValue(data.answer || '{}');
            metaEditor.setValue(data.meta_data || '{}');
            tagsEditor.setValue(data.tags || '{}');
            
            // 미리보기 업데이트
            updatePreview();
            
            timer.end();
            CPAgent.UI.hideLoadingModal();
            showToast('AI 문항 생성이 완료되었습니다!', 'success');
            
            // 렌더링 탭으로 자동 전환
            switchPreviewTab('render');
        },
        error: function(xhr) {
            debugLog('CONTENT', 'AI 요청 실패', xhr);
            
            let errorMsg = 'AI 요청 중 오류가 발생했습니다.';
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    errorMsg = response.error;
                }
            } catch (e) {
                debugLog('CONTENT', '에러 응답 파싱 실패', e);
            }
            
            CPAgent.UI.hideLoadingModal();
            showToast(errorMsg, 'error');
        }
    });
}

/**
 * 콘텐츠 저장
 */
function saveContent() {
    debugLog('CONTENT', '콘텐츠 저장 시작');
    
    // 1. 저장 전 이미지 자동 검증 및 정리
    CPAgent.Image.validateAndCleanupBeforeSave();
    
    // 2. 변경된 텍스트 색상 초기화
    resetTextColors();
    
    // 3. HTML 에디터의 내용을 최신 상태로 업데이트
    updatePreviewFromHtml();
    
    const formData = {
        title: $('#title').val(),
        content_type: $('#content_type').val(),
        page: htmlEditorInstance.getValue(),
        answer: answerEditor.getValue(),
        meta_data: metaEditor.getValue(),
        tags: tagsEditor.getValue(),
        prompt: $('#prompt_content').val()
    };
    
    debugLog('CONTENT', '저장할 데이터', {
        title: formData.title,
        content_type: formData.content_type,
        page_length: formData.page.length,
        has_answer: !!formData.answer,
        has_prompt: !!formData.prompt
    });
    
    // 유효성 검사
    if (!formData.title || !formData.content_type || !formData.page) {
        showToast('제목, 컨텐츠 타입, 페이지 내용은 필수입니다', 'error');
        return;
    }
    
    // 저장 전 최종 이미지 src 검증
    const finalValidation = CPAgent.Image.validateAllImages();
    if (finalValidation.corrupted > 0) {
        debugLog('CONTENT', '손상된 이미지 발견', finalValidation.corrupted);
        if (!confirm('일부 이미지 경로에 문제가 있을 수 있습니다. 계속 저장하시겠습니까?')) {
            return;
        }
    }
    
    // 로딩 상태 표시
    const $saveBtn = $('button[onclick="saveContent()"]');
    const originalText = $saveBtn.html();
    $saveBtn.html('<i class="fas fa-spinner fa-spin mr-2"></i>저장 중...').prop('disabled', true);
    
    const timer = new PerformanceTimer('콘텐츠 저장');
    
    const url = currentContent ? 
        `/cp/api/contents/${currentContent.id}/update/` : 
        '/cp/api/contents/create/';
    const method = currentContent ? 'PUT' : 'POST';
    
    $.ajax({
        url: url,
        method: method,
        data: JSON.stringify(formData),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(data) {
            debugLog('CONTENT', '콘텐츠 저장 성공', data);
            
            // 저장 완료 후 버튼 복원
            $saveBtn.html(originalText).prop('disabled', false);
            
            showToast('저장되었습니다!', 'success');
            currentContent = data;
            
            // 임시 업로드 목록 초기화 (저장되었으므로)
            temporaryUploads = [];
            
            // 변경된 모든 요소의 표시 제거
            $('[data-changed="true"]').removeAttr('data-changed');
            
            // 편집 컨트롤 업데이트
            CPAgent.UI.updateEditControls();
            
            // 리스트 새로고침
            CPAgent.Data.searchContents();
            
            timer.end();
            
            // 저장 후 다시 한 번 이미지 검증 (선택사항)
            setTimeout(() => {
                const postSaveValidation = CPAgent.Image.validateAllImages();
                if (postSaveValidation.corrupted === 0 && postSaveValidation.missing === 0) {
                    debugLog('CONTENT', '저장 후 검증: 모든 이미지 정상');
                } else {
                    debugLog('CONTENT', '저장 후 검증: 일부 이미지 문제 있음', postSaveValidation);
                }
            }, 1000);
        },
        error: function(xhr) {
            debugLog('CONTENT', '콘텐츠 저장 실패', xhr);
            
            // 에러 시 버튼 복원
            $saveBtn.html(originalText).prop('disabled', false);
            
            let errorMsg = '저장 중 오류가 발생했습니다.';
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    errorMsg = response.error;
                }
            } catch (e) {
                debugLog('CONTENT', '에러 응답 파싱 실패', e);
            }
            
            showToast(errorMsg, 'error');
        }
    });
}

/**
 * 새 콘텐츠 생성 시 초기화
 */
function createNewContent() {
    debugLog('CONTENT', '새 콘텐츠 생성');
    
    // 임시 파일 정리
    if (temporaryUploads.length > 0) {
        cleanupTemporaryUploads();
    }
    
    // 이미지 변경사항 취소
    CPAgent.Image.cancelImageChanges();
    
    // 폼 초기화
    $('#title').val('');
    $('#content_type').val('');
    $('#template_select').val('');
    $('#prompt_content').val('');
    
    // 에디터 초기화
    answerInputEditor.setValue('{}');
    answerEditor.setValue('{}');
    metaEditor.setValue('{}');
    tagsEditor.setValue('{}');
    htmlEditorInstance.setValue('');
    
    // 미리보기 초기화
    $('#previewContent').html(`
        <div class="text-center text-gray-400 py-8">
            <i class="fas fa-eye text-6xl mb-4"></i>
            <p>AI로 문항을 생성하면 여기에 표시됩니다</p>
        </div>
    `);
    
    $('#editableContent').html(`
        <p class="text-gray-400 text-center py-8">
            <i class="fas fa-edit text-4xl mb-2 block"></i>
            AI로 문항을 생성하면 편집 가능한 텍스트가 여기에 표시됩니다
        </p>
    `);
    
    // 현재 콘텐츠 초기화
    currentContent = null;
    
    // 편집 컨트롤 업데이트
    CPAgent.UI.updateEditControls();
    
    showToast('새 콘텐츠 작성을 시작합니다', 'success');
    
    // 제목 입력란에 포커스
    setTimeout(() => {
        $('#title').focus();
    }, 100);
}

/* ========== 미리보기 관리 ========== */

/**
 * 미리보기 업데이트
 */
function updatePreview() {
    const html = htmlEditorInstance.getValue();
    
    // 렌더링 탭 업데이트
    $('#previewContent').html(html);
    
    // 텍스트 편집 탭 업데이트
    CPAgent.TextEditing.updateEditableContent(html);
    
    // 이벤트 바인딩
    setTimeout(() => {
        CPAgent.TextEditing.bindTextEditingEvents();
    }, 50);
}

/**
 * HTML 편집기에서 미리보기 업데이트
 */
function updatePreviewFromHtml() {
    const html = htmlEditorInstance.getValue();
    $('#previewContent').html(html);
    CPAgent.TextEditing.updateEditableContent(html);
}

/**
 * 변경된 텍스트 색상 초기화
 */
function resetTextColors() {
    $('.text-changed').removeClass('text-changed').css('color', '');
    $('.editable-word[data-changed="true"]').removeAttr('data-changed');
    $('.editable-image[data-changed="true"]').removeAttr('data-changed');
    debugLog('CONTENT', '텍스트 색상 초기화 완료');
}

/* ========== 전역 콘텐츠 네임스페이스 ========== */
window.CPAgent.Content = {
    loadContent,
    requestAI,
    saveContent,
    createNewContent,
    updatePreview,
    updatePreviewFromHtml,
    resetTextColors
};