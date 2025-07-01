// static/js/cp_agent/content.js - 향상된 콘텐츠 관리 함수들

/* ========== 콘텐츠 CRUD 작업 ========== */

/**
 * AI 요청 (개선된 버전)
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
    
    // 템플릿 선택 시 템플릿 정보 미리 로드
    if (formData.template_id) {
        loadTemplatePreview(formData.template_id);
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
            
            // 정답 체크 기능 추가
            setTimeout(() => {
                CPAgent.AnswerChecker.addCheckButton();
                addInteractiveFeatures();
            }, 100);
            
            timer.end();
            CPAgent.UI.hideLoadingModal();
            showToast('AI 문항 생성이 완료되었습니다!', 'success');
            
            // 렌더링 탭으로 자동 전환
            switchPreviewTab('render');
            
            // 생성 후 자동 검증
            validateGeneratedContent();
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
 * 템플릿 미리보기 로드
 */
function loadTemplatePreview(templateId) {
    if (!templateId) return;
    
    $.get(`/cp/api/templates/${templateId}/`)
        .done(function(template) {
            debugLog('CONTENT', '템플릿 미리보기 로드', template);
            
            // 템플릿 정보를 프롬프트에 추가
            const currentPrompt = $('#prompt_content').val();
            if (!currentPrompt.includes('템플릿 기반')) {
                const templateInfo = `
[템플릿 기반 생성]
- 템플릿: ${template.title}
- 구조: ${template.page ? '사용자 정의 HTML 구조' : '기본 구조'}

${currentPrompt}`;
                $('#prompt_content').val(templateInfo);
            }
            
            showToast(`템플릿 "${template.title}"이 적용되었습니다`, 'info');
        })
        .fail(function() {
            showToast('템플릿을 불러오는 중 오류가 발생했습니다', 'warning');
        });
}

/**
 * 생성된 콘텐츠 검증
 */
function validateGeneratedContent() {
    debugLog('CONTENT', '생성된 콘텐츠 검증 시작');
    
    const html = htmlEditorInstance.getValue();
    const answer = answerEditor.getValue();
    
    const validation = {
        hasContent: html.trim().length > 0,
        hasAnswer: answer.trim().length > 0 && answer !== '{}',
        hasQuestionElements: false,
        hasAnswerElements: false,
        issues: []
    };
    
    if (html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // 문항 요소 확인
        const questionElements = tempDiv.querySelectorAll('h1, h2, h3, .question, .problem');
        validation.hasQuestionElements = questionElements.length > 0;
        
        // 답안 입력 요소 확인
        const inputElements = tempDiv.querySelectorAll('input, textarea, select');
        validation.hasAnswerElements = inputElements.length > 0;
        
        // 이미지 확인
        const images = tempDiv.querySelectorAll('img');
        images.forEach(img => {
            if (!img.src || img.src.includes('placeholder')) {
                validation.issues.push('placeholder 이미지가 포함되어 있습니다');
            }
        });
        
        // 텍스트 내용 확인
        const textContent = tempDiv.textContent.trim();
        if (textContent.length < 20) {
            validation.issues.push('콘텐츠가 너무 짧습니다');
        }
    }
    
    // 답안 데이터 검증
    try {
        const answerData = JSON.parse(answer);
        if (!answerData.correct) {
            validation.issues.push('정답 정보가 없습니다');
        }
    } catch (e) {
        validation.issues.push('답안 JSON 형식이 올바르지 않습니다');
    }
    
    // 검증 결과 표시
    displayValidationResult(validation);
    
    return validation;
}

/**
 * 검증 결과 표시
 */
function displayValidationResult(validation) {
    const $container = $('#previewContent');
    
    // 기존 검증 결과 제거
    $container.find('.validation-result').remove();
    
    if (validation.issues.length === 0) {
        showToast('문항이 성공적으로 생성되었습니다', 'success');
        return;
    }
    
    // 검증 결과 HTML 생성
    const issuesHtml = validation.issues.map(issue => 
        `<li class="text-sm text-yellow-700">${issue}</li>`
    ).join('');
    
    const validationHtml = `
        <div class="validation-result mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div class="flex items-start">
                <i class="fas fa-exclamation-triangle text-yellow-600 mt-1 mr-2"></i>
                <div>
                    <h4 class="text-sm font-medium text-yellow-800">검증 결과</h4>
                    <ul class="mt-1 list-disc list-inside">
                        ${issuesHtml}
                    </ul>
                    <p class="mt-2 text-xs text-yellow-600">
                        위 사항들을 확인하고 필요시 수정해주세요.
                    </p>
                </div>
            </div>
        </div>
    `;
    
    $container.prepend(validationHtml);
}

/**
 * 대화형 기능 추가
 */
function addInteractiveFeatures() {
    const $container = $('#previewContent');
    
    // 문항 타입 감지
    const hasRadio = $container.find('input[type="radio"]').length > 0;
    const hasCheckbox = $container.find('input[type="checkbox"]').length > 0;
    const hasText = $container.find('input[type="text"], textarea').length > 0;
    
    // 라디오 버튼 그룹 스타일링
    if (hasRadio) {
        $container.find('input[type="radio"]').each(function() {
            const $input = $(this);
            const $label = $input.closest('label');
            
            $input.on('change', function() {
                // 같은 그룹의 다른 라벨 스타일 초기화
                $(`input[name="${this.name}"]`).closest('label').removeClass('selected-choice');
                // 선택된 라벨 스타일 적용
                $label.addClass('selected-choice');
                
                // 자동 체크가 활성화되어 있으면 즉시 검사
                if ($container.data('auto-check') === 'true') {
                    CPAgent.AnswerChecker.checkAnswer($container[0]);
                }
            });
        });
    }
    
    // 체크박스 스타일링
    if (hasCheckbox) {
        $container.find('input[type="checkbox"]').on('change', function() {
            const $label = $(this).closest('label');
            if (this.checked) {
                $label.addClass('selected-choice');
            } else {
                $label.removeClass('selected-choice');
            }
        });
    }
    
    // 텍스트 입력 실시간 검증
    if (hasText) {
        $container.find('input[type="text"], textarea').on('input', function() {
            const $input = $(this);
            const value = $input.val().trim();
            
            // 입력값 표시
            if (value.length > 0) {
                $input.addClass('has-content');
            } else {
                $input.removeClass('has-content');
            }
        });
    }
    
    // CSS 스타일 추가
    addInteractiveStyles();
}

/**
 * 대화형 CSS 스타일 추가
 */
function addInteractiveStyles() {
    const styleId = 'interactive-question-styles';
    
    // 기존 스타일 제거
    $(`#${styleId}`).remove();
    
    const styles = `
        <style id="${styleId}">
            .selected-choice {
                background-color: #EBF4FF !important;
                border-color: #3B82F6 !important;
                border-width: 2px !important;
            }
            
            .has-content {
                border-color: #10B981 !important;
                background-color: #F0FDF4 !important;
            }
            
            .check-answer-btn {
                transition: all 0.2s ease-in-out;
            }
            
            .check-answer-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            }
            
            .answer-result {
                animation: slideIn 0.3s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .validation-result {
                animation: fadeIn 0.2s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        </style>
    `;
    
    $('head').append(styles);
}

/**
 * 미리보기 업데이트 (개선된 버전)
 */
function updatePreview() {
    const html = htmlEditorInstance.getValue();
    
    // 렌더링 탭 업데이트
    $('#previewContent').html(html);
    
    // 대화형 기능 추가
    addInteractiveFeatures();
    
    // 정답 체크 버튼 추가
    CPAgent.AnswerChecker.addCheckButton();
    
    // 텍스트 편집 탭 업데이트
    CPAgent.TextEditing.updateEditableContent(html);
    
    // 이벤트 바인딩
    setTimeout(() => {
        CPAgent.TextEditing.bindTextEditingEvents();
    }, 50);
    
    debugLog('CONTENT', '미리보기 업데이트 완료');
}

/**
 * 템플릿 적용
 */
function applyTemplate(templateId) {
    if (!templateId) return;
    
    debugLog('CONTENT', '템플릿 적용', templateId);
    
    $.get(`/cp/api/templates/${templateId}/`)
        .done(function(template) {
            // HTML 구조 적용
            if (template.page) {
                htmlEditorInstance.setValue(template.page);
            }
            
            // 답안 구조 적용
            if (template.answer) {
                answerEditor.setValue(template.answer);
                answerInputEditor.setValue(template.answer);
            }
            
            // 메타데이터 적용
            if (template.meta_data) {
                metaEditor.setValue(JSON.stringify(template.meta_data, null, 2));
            }
            
            // 태그 적용 (JavaScript 코드 포함)
            if (template.tags) {
                tagsEditor.setValue(JSON.stringify(template.tags, null, 2));
            }
            
            // 미리보기 업데이트
            updatePreview();
            
            showToast(`템플릿 "${template.title}"이 적용되었습니다`, 'success');
        })
        .fail(function() {
            showToast('템플릿을 적용하는 중 오류가 발생했습니다', 'error');
        });
}

// 기존 함수들 유지...
// loadContent, saveContent, createNewContent 등

/* ========== 전역 콘텐츠 네임스페이스 (확장) ========== */
window.CPAgent.Content = {
    loadContent,
    requestAI,
    saveContent,
    createNewContent,
    updatePreview,
    updatePreviewFromHtml,
    resetTextColors,
    loadTemplatePreview,
    validateGeneratedContent,
    addInteractiveFeatures,
    applyTemplate
};