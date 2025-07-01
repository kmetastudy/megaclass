// static/js/cp_agent/template.js - 템플릿 관리 함수들

/* ========== 템플릿 선택 및 적용 (재귀 방지) ========== */

/**
 * 템플릿 리스트에서 클릭 시 호출되는 함수
 */
function selectTemplateFromList(templateId) {
    debugLog('TEMPLATE', '리스트에서 템플릿 선택', templateId);
    
    // UI 선택상태 업데이트 (이벤트 발생시키지 않음)
    $('#template_select').val(templateId);
    
    // 템플릿 데이터 적용
    applyTemplateData(templateId);
}

/**
 * 템플릿 데이터 적용 (재귀 방지용)
 */
function applyTemplateData(templateId) {
    debugLog('TEMPLATE', '템플릿 데이터 적용', templateId);
    
    // 템플릿 데이터 찾기
    const template = templates.find(t => t.id == templateId);
    if (!template) {
        debugLog('TEMPLATE', '템플릿을 찾을 수 없음', templateId);
        showToast('템플릿을 찾을 수 없습니다', 'error');
        return;
    }
    
    debugLog('TEMPLATE', '적용할 템플릿', template);
    
    try {
        const timer = new PerformanceTimer('템플릿 적용');
        
        // 폼에 템플릿 데이터 적용
        $('#prompt_content').val(template.page || '');
        
        // answer 처리
        if (template.answer) {
            answerInputEditor.setValue(template.answer);
        } else {
            answerInputEditor.setValue('{}');
        }
        
        // meta_data 처리
        if (template.meta_data) {
            if (typeof template.meta_data === 'string') {
                metaEditor.setValue(template.meta_data);
            } else {
                metaEditor.setValue(JSON.stringify(template.meta_data, null, 2));
            }
        } else {
            metaEditor.setValue('{}');
        }
        
        // tags 처리 (JavaScript 코드 포함 가능)
        if (template.tags) {
            if (typeof template.tags === 'object' && template.tags.javascript) {
                // JavaScript 코드가 tags.javascript에 저장된 경우
                tagsEditor.setValue(JSON.stringify(template.tags, null, 2));
            } else if (typeof template.tags === 'string') {
                tagsEditor.setValue(template.tags);
            } else {
                tagsEditor.setValue(JSON.stringify(template.tags, null, 2));
            }
        } else {
            tagsEditor.setValue('{}');
        }
        
        timer.end();
        showToast(`템플릿 "${template.title}"이 적용되었습니다`, 'success');
        
    } catch (error) {
        debugLog('TEMPLATE', '템플릿 적용 중 오류', error);
        showToast('템플릿 적용 중 오류가 발생했습니다', 'error');
    }
}

/* ========== 템플릿 CRUD 작업 ========== */

/**
 * 템플릿 테스트
 */
function testTemplate() {
    debugLog('TEMPLATE', '템플릿 테스트 시작');
    
    const html = $('#templateHtml').val();
    const js = $('#templateJs').val();
    
    if (!html.trim()) {
        showToast('HTML 템플릿을 입력해주세요', 'warning');
        return;
    }
    
    try {
        // HTML 미리보기에 표시
        $('#previewContent').html(html);
        
        // JavaScript 코드 실행 (있는 경우)
        if (js && js.trim()) {
            try {
                // 안전한 실행을 위해 새로운 함수로 감싸기
                const testFunction = new Function(js);
                testFunction();
            } catch (jsError) {
                debugLog('TEMPLATE', 'JavaScript 실행 오류', jsError);
                showToast('JavaScript 코드에 오류가 있습니다: ' + jsError.message, 'error');
                return;
            }
        }
        
        // 렌더링 탭으로 전환
        switchPreviewTab('render');
        showToast('템플릿 테스트가 완료되었습니다', 'success');
        
    } catch (error) {
        debugLog('TEMPLATE', '템플릿 테스트 오류', error);
        showToast('템플릿 테스트 중 오류가 발생했습니다', 'error');
    }
}

/**
 * 템플릿 저장
 */
function saveTemplate() {
    debugLog('TEMPLATE', '템플릿 저장 시작');
    
    // 폼 데이터 수집
    const formData = {
        title: $('#templateName').val().trim(),
        content_category: $('#templateFormCategory').val(),
        content_type: $('#templateFormType').val(),
        page: $('#templateHtml').val(),
        answer: $('#templateAnswer').val(),
        meta_data: $('#templateMeta').val(),
        tags: $('#templateJs').val(), // JavaScript 코드
        is_public: true
    };
    
    debugLog('TEMPLATE', '전송할 데이터', formData);
    
    // 유효성 검사
    const validation = validateTemplateForm(formData);
    if (!validation.valid) {
        showToast(validation.message, 'error');
        if (validation.field) {
            $(validation.field).focus();
        }
        return;
    }
    
    // 저장 버튼 로딩 상태
    const $saveBtn = $('button[onclick="saveTemplate()"]');
    const originalText = $saveBtn.html();
    $saveBtn.html('<i class="fas fa-spinner fa-spin mr-2"></i>저장 중...').prop('disabled', true);
    
    const timer = new PerformanceTimer('템플릿 저장');
    
    $.ajax({
        url: '/cp/api/templates/create/',
        method: 'POST',
        data: JSON.stringify(formData),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(data) {
            debugLog('TEMPLATE', '템플릿 저장 성공', data);
            
            // 버튼 복원
            $saveBtn.html(originalText).prop('disabled', false);
            
            showToast('템플릿이 저장되었습니다!', 'success');
            CPAgent.UI.closeTemplateModal();
            
            // 템플릿 리스트 새로고침
            CPAgent.Data.searchTemplates();
            
            timer.end();
        },
        error: function(xhr) {
            debugLog('TEMPLATE', '템플릿 저장 실패', xhr);
            
            // 버튼 복원
            $saveBtn.html(originalText).prop('disabled', false);
            
            let errorMsg = '템플릿 저장 중 오류가 발생했습니다.';
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    errorMsg = response.error;
                }
            } catch (e) {
                debugLog('TEMPLATE', '에러 응답 파싱 실패', e);
            }
            
            showToast(errorMsg, 'error');
        }
    });
}

/* ========== 템플릿 유효성 검사 ========== */

/**
 * 템플릿 폼 유효성 검사
 */
function validateTemplateForm(formData) {
    // 필수 필드 검증
    if (!formData.title) {
        return {
            valid: false,
            message: '템플릿 이름을 입력하세요',
            field: '#templateName'
        };
    }
    
    if (!formData.content_category) {
        return {
            valid: false,
            message: '카테고리를 선택하세요',
            field: '#templateFormCategory'
        };
    }
    
    if (!formData.content_type) {
        return {
            valid: false,
            message: '타입을 선택하세요',
            field: '#templateFormType'
        };
    }
    
    if (!formData.page.trim()) {
        return {
            valid: false,
            message: 'HTML 템플릿을 입력하세요',
            field: '#templateHtml'
        };
    }
    
    // JSON 필드 유효성 검사
    try {
        // answer 필드 검증
        const answerText = formData.answer.trim();
        if (answerText && answerText !== '{}') {
            if (answerText.startsWith('{')) {
                JSON.parse(answerText); // JSON 형식 검증
            }
        }
        
        // meta_data 필드 검증
        const metaText = formData.meta_data.trim();
        if (metaText && metaText !== '{}') {
            JSON.parse(metaText); // JSON 형식 검증
        }
    } catch (e) {
        return {
            valid: false,
            message: 'JSON 형식이 올바르지 않습니다: ' + e.message
        };
    }
    
    // HTML 기본 검증
    if (!formData.page.includes('<')) {
        return {
            valid: false,
            message: 'HTML 태그가 포함된 유효한 템플릿을 입력하세요',
            field: '#templateHtml'
        };
    }
    
    return { valid: true };
}

/* ========== 템플릿 이벤트 바인딩 ========== */

/**
 * 템플릿 관련 이벤트 바인딩
 */
function bindTemplateEvents() {
    debugLog('TEMPLATE', '템플릿 이벤트 바인딩');
    
    // 템플릿 폼 카테고리 변경 시
    $('#templateFormCategory').off('change.template').on('change.template', function() {
        const categoryId = $(this).val();
        const $typeSelect = $('#templateFormType');
        
        if (categoryId) {
            CPAgent.Data.loadContentTypesByCategory(categoryId, ['#templateFormType'])
                .then(() => {
                    $typeSelect.prop('disabled', false);
                })
                .catch(() => {
                    $typeSelect.empty().append('<option value="">타입 로드 실패</option>');
                });
        } else {
            $typeSelect.empty().append('<option value="">타입 선택</option>');
            $typeSelect.prop('disabled', true);
        }
    });
    
    // 템플릿 검색 카테고리 변경 시
    $('#templateCategory').off('change.templateSearch').on('change.templateSearch', function() {
        const categoryId = $(this).val();
        
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
    
    $('#templateType').off('change.templateSearch').on('change.templateSearch', function() {
        CPAgent.Data.searchTemplates();
    });
    
    // 템플릿 검색어 엔터키
    $('#templateSearch').off('keypress.templateSearch').on('keypress.templateSearch', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            CPAgent.Data.searchTemplates();
        }
    });
    
    // 템플릿 폼 필드 실시간 유효성 검사
    $('#templateName').off('input.validation').on('input.validation', function() {
        const value = $(this).val().trim();
        if (value.length > 0) {
            $(this).removeClass('border-red-300').addClass('border-green-300');
        } else {
            $(this).removeClass('border-green-300').addClass('border-red-300');
        }
    });
    
    $('#templateHtml').off('input.validation').on('input.validation', function() {
        const value = $(this).val().trim();
        if (value.length > 0 && value.includes('<')) {
            $(this).removeClass('border-red-300').addClass('border-green-300');
        } else {
            $(this).removeClass('border-green-300').addClass('border-red-300');
        }
    });
}

/* ========== 전역 템플릿 네임스페이스 ========== */
window.CPAgent.Template = {
    selectTemplateFromList,
    applyTemplateData,
    testTemplate,
    saveTemplate,
    validateTemplateForm,
    bindTemplateEvents
};