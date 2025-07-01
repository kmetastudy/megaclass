// static/js/cp_agent/content.js - 향상된 콘텐츠 관리 함수들

/* ========== 콘텐츠 CRUD 작업 ========== */

/**
 * AI 요청 (개선된 버전)
 */

/* ========== 간단한 템플릿 태그 생성 ========== */
function generateSimpleTemplateFormatTags() {
    // 기본 템플릿 형식만 제공
    return {
        "competency": "수리능력",
        "sub_competency": "도표분석능력", 
        "difficulty": "중",
        "question_type": "multiple-choice",
        "order": 1
    };
}


/**
 * HTML탭 에디터들에 값 안전하게 설정 (기존 함수 개선)
 */
function setHtmlTabEditorsValue(metaData, tagsData) {
    return setHtmlTabEditorsWithRetry(metaData, tagsData, 0);
}

// 전역 함수로 등록
window.setHtmlTabEditorsWithRetry = setHtmlTabEditorsWithRetry;
window.setHtmlTabEditorsValue = setHtmlTabEditorsValue;


/**
 * AI 요청 (간소화된 버전)
 */
function requestAI_062920() {
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
    
    // 강제 로딩 스피너 표시
    showLoadingSpinner();
    console.log('로딩 스피너 강제 표시 완료');
    
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
            console.log('AI 응답 받음, 로딩 스피너 숨기기');
            
            // 생성된 콘텐츠 설정
            htmlEditorInstance.setValue(data.page || '');
            
            // 답안 유니코드 디코딩 후 설정
            const decodedAnswer = decodeUnicodeString(data.answer || '{}');
            answerEditor.setValue(decodedAnswer);
            
            // answerEditorContainer에도 답안 설정
            setAnswerToContainer(decodedAnswer);
            
            // 메타데이터와 태그 설정 (유니코드 디코딩)
            const decodedMetaData = decodeUnicodeString(data.meta_data || '{}');
            const decodedTags = decodeUnicodeString(data.tags || '{}');
            
            // 중앙 패널 에디터들 설정
            metaEditor.setValue(decodedMetaData);
            tagsEditor.setValue(decodedTags);
            
            // HTML탭 에디터들에도 설정
            if (window.metaEditorInstance_html) {
                window.metaEditorInstance_html.setValue(decodedMetaData);
            }
            if (window.tagsEditorInstance_html) {
                window.tagsEditorInstance_html.setValue(decodedTags);
            }
            
            // 미리보기 업데이트
            updatePreview();
            
            // 정답 체크 기능 추가
            setTimeout(() => {
                if (window.CPAgent && CPAgent.AnswerChecker) {
                    CPAgent.AnswerChecker.addCheckButton();
                }
                addInteractiveFeatures();
            }, 100);
            
            timer.end();
            
            // 로딩 스피너 숨기기
            hideLoadingSpinner();
            console.log('로딩 스피너 숨김 완료');
            
            showToast('AI 문항 생성이 완료되었습니다!', 'success');
            
            // 렌더링 탭으로 자동 전환
            switchPreviewTab('render');
            
            // 생성 후 자동 검증
            validateGeneratedContent();
        },
        error: function(xhr) {
            debugLog('CONTENT', 'AI 요청 실패', xhr);
            console.log('AI 요청 실패, 로딩 스피너 숨기기');
            
            let errorMsg = 'AI 요청 중 오류가 발생했습니다.';
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    errorMsg = response.error;
                }
            } catch (e) {
                debugLog('CONTENT', '에러 응답 파싱 실패', e);
            }
            
            // 로딩 스피너 숨기기
            hideLoadingSpinner();
            
            showToast(errorMsg, 'error');
        }
    });
}

/**
 * AI 요청 (에러 핸들링 강화 버전)
 */
/**
 * AI 요청 (에러 핸들링 강화 버전)
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
    
    // 강제 로딩 스피너 표시
    showLoadingSpinner();
    console.log('로딩 스피너 강제 표시 완료');
    
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
            try {
                debugLog('CONTENT', 'AI 요청 성공', data);
                console.log('AI 응답 받음, 처리 시작');
                
                // 에디터 상태 체크
                console.log('1. 에디터 상태 체크');
                checkAllEditorsStatus();
                
                // 2. AI 응답 데이터를 에디터에 안전하게 설정
                console.log('2. AI 응답 데이터를 에디터에 설정');
                const editorSetSuccess = safelySetAIResponseToEditors(data);
                
                if (!editorSetSuccess) {
                    console.warn('일부 에디터 설정이 실패했지만 계속 진행');
                }
                
                // 3. 미리보기 업데이트
                console.log('3. 미리보기 업데이트 시작');
                try {
                    updatePreview();
                    console.log('미리보기 업데이트 완료');
                } catch (e) {
                    console.warn('미리보기 업데이트 실패:', e);
                }
                
                // 4. 정답 체크 기능 추가 (비동기)
                console.log('4. 대화형 기능 추가 시작');
                setTimeout(() => {
                    try {
                        if (window.CPAgent && CPAgent.AnswerChecker) {
                            CPAgent.AnswerChecker.addCheckButton();
                            console.log('정답 체크 버튼 추가 완료');
                        }
                        addInteractiveFeatures();
                        console.log('대화형 기능 추가 완료');
                    } catch (e) {
                        console.warn('대화형 기능 추가 실패:', e);
                    }
                }, 100);
                
                timer.end();
                
                // 성공 메시지 및 탭 전환
                showToast('AI 문항 생성이 완료되었습니다!', 'success');
                
                // 렌더링 탭으로 자동 전환
                try {
                    switchPreviewTab('render');
                    console.log('렌더링 탭 전환 완료');
                } catch (e) {
                    console.warn('탭 전환 실패:', e);
                }
                
                // 생성 후 자동 검증
                try {
                    validateGeneratedContent();
                    console.log('콘텐츠 검증 완료');
                } catch (e) {
                    console.warn('콘텐츠 검증 실패:', e);
                }
                
                console.log('AI 응답 처리 완료');
                
            } catch (error) {
                console.error('AI 응답 처리 중 에러:', error);
                console.error('에러 스택:', error.stack);
                showToast('AI 응답 처리 중 오류가 발생했습니다', 'error');
            } finally {
                // 반드시 로딩 스피너 숨기기
                console.log('로딩 스피너 숨기기 (finally)');
                hideLoadingSpinner();
            }
        },
        error: function(xhr, status, errorThrown) {
            try {
                debugLog('CONTENT', 'AI 요청 실패', {xhr, status, errorThrown});
                console.log('AI 요청 실패, 로딩 스피너 숨기기');
                
                let errorMsg = 'AI 요청 중 오류가 발생했습니다.';
                try {
                    if (xhr.responseText) {
                        const response = JSON.parse(xhr.responseText);
                        if (response.error) {
                            errorMsg = response.error;
                        }
                    }
                } catch (e) {
                    debugLog('CONTENT', '에러 응답 파싱 실패', e);
                    errorMsg += ` (상태: ${status}, 오류: ${errorThrown})`;
                }
                
                showToast(errorMsg, 'error');
                
            } catch (e) {
                console.error('에러 처리 중 추가 에러:', e);
                showToast('예상치 못한 오류가 발생했습니다', 'error');
            } finally {
                // 반드시 로딩 스피너 숨기기
                console.log('로딩 스피너 숨기기 (error finally)');
                hideLoadingSpinner();
            }
        },
        complete: function() {
            // AJAX 완료 시 (성공/실패 관계없이)
            console.log('AJAX 요청 완료');
            // 혹시 모를 경우를 대비해 다시 한번 스피너 숨기기
            setTimeout(() => {
                if ($('#ai-loading-spinner').length > 0) {
                    console.log('완료 후 남은 스피너 강제 제거');
                    hideLoadingSpinner();
                }
            }, 1000);
        }
    });
}

/**
 * 안전한 에디터 접근 및 설정 함수들
 */

/**
 * 에디터 존재 여부 확인 및 안전한 값 설정
 */
function safeSetEditorValue(editorName, value, fallbackMessage) {
    try {
        let editor = null;
        let editorDisplayName = '';
        
        // 에디터 참조 가져오기
        switch (editorName) {
            case 'htmlEditor':
                editor = window.htmlEditorInstance;
                editorDisplayName = 'HTML 에디터';
                break;
            case 'answerEditor':
                editor = window.answerEditor;
                editorDisplayName = '정답 에디터';
                break;
            case 'metaEditor':
                editor = window.metaEditor;
                editorDisplayName = '메타데이터 에디터';
                break;
            case 'tagsEditor':
                editor = window.tagsEditor;
                editorDisplayName = '태그 에디터';
                break;
            case 'metaEditorHtml':
                editor = window.metaEditorInstance_html;
                editorDisplayName = 'HTML탭 메타데이터 에디터';
                break;
            case 'tagsEditorHtml':
                editor = window.tagsEditorInstance_html;
                editorDisplayName = 'HTML탭 태그 에디터';
                break;
            case 'answerInputEditor':
                editor = window.answerInputEditor;
                editorDisplayName = '답안 입력 에디터';
                break;
        }
        
        if (!editor) {
            console.warn(`${editorDisplayName}가 초기화되지 않았습니다`);
            if (fallbackMessage) {
                console.warn(fallbackMessage);
            }
            return false;
        }
        
        if (typeof editor.setValue !== 'function') {
            console.warn(`${editorDisplayName}에 setValue 메서드가 없습니다`);
            return false;
        }
        
        editor.setValue(value);
        console.log(`${editorDisplayName} 값 설정 완료`);
        return true;
        
    } catch (error) {
        console.error(`${editorName} 설정 중 오류:`, error);
        return false;
    }
}

/**
 * 모든 에디터 상태 확인
 */
function checkAllEditorsStatus() {
    const editors = {
        'htmlEditorInstance': window.htmlEditorInstance,
        'answerEditor': window.answerEditor,
        'metaEditor': window.metaEditor,
        'tagsEditor': window.tagsEditor,
        'answerInputEditor': window.answerInputEditor,
        'metaEditorInstance_html': window.metaEditorInstance_html,
        'tagsEditorInstance_html': window.tagsEditorInstance_html
    };
    
    const status = {};
    
    Object.keys(editors).forEach(name => {
        const editor = editors[name];
        status[name] = {
            exists: !!editor,
            hasSetValue: editor && typeof editor.setValue === 'function',
            hasGetValue: editor && typeof editor.getValue === 'function'
        };
    });
    
    console.log('에디터 상태 체크:', status);
    return status;
}

/**
 * HTML탭 에디터 재초기화 시도
 */
function reinitializeHtmlTabEditors() {
    console.log('HTML탭 에디터 재초기화 시도');
    
    try {
        // 메타데이터 에디터 재초기화
        if (!window.metaEditorInstance_html) {
            const metaContainer = document.getElementById('metaEditorContainer');
            if (metaContainer) {
                console.log('HTML탭 메타데이터 에디터 재생성 시도');
                try {
                    window.metaEditorInstance_html = CodeMirror(metaContainer, {
                        value: '{\n  "difficulty": "중",\n  "estimated_time": 300,\n  "subject": "",\n  "chapter": ""\n}',
                        mode: 'javascript',
                        theme: 'material',
                        lineNumbers: true,
                        lineWrapping: true,
                        viewportMargin: Infinity,
                        autoCloseBrackets: true,
                        matchBrackets: true
                    });
                    window.metaEditorInstance_html.setSize(null, '100%');
                    console.log('HTML탭 메타데이터 에디터 재생성 완료');
                } catch (e) {
                    console.error('HTML탭 메타데이터 에디터 재생성 실패:', e);
                }
            } else {
                console.warn('metaEditorContainer DOM 요소를 찾을 수 없음');
            }
        }
        
        // 태그 에디터 재초기화
        if (!window.tagsEditorInstance_html) {
            const tagsContainer = document.getElementById('tagsEditorContainer');
            if (tagsContainer) {
                console.log('HTML탭 태그 에디터 재생성 시도');
                try {
                    window.tagsEditorInstance_html = CodeMirror(tagsContainer, {
                        value: '{\n  "competency": "수리능력",\n  "sub_competency": "도표분석능력",\n  "difficulty": "중",\n  "question_type": "multiple-choice",\n  "order": 1\n}',
                        mode: 'javascript',
                        theme: 'material',
                        lineNumbers: true,
                        lineWrapping: true,
                        viewportMargin: Infinity,
                        autoCloseBrackets: true,
                        matchBrackets: true
                    });
                    window.tagsEditorInstance_html.setSize(null, '100%');
                    console.log('HTML탭 태그 에디터 재생성 완료');
                } catch (e) {
                    console.error('HTML탭 태그 에디터 재생성 실패:', e);
                }
            } else {
                console.warn('tagsEditorContainer DOM 요소를 찾을 수 없음');
            }
        }
        
    } catch (error) {
        console.error('HTML탭 에디터 재초기화 실패:', error);
    }
}

/**
 * AI 응답 데이터를 안전하게 에디터에 설정
 */
function safelySetAIResponseToEditors(data) {
    console.log('AI 응답 데이터를 에디터에 안전하게 설정 시작');
    
    try {
        // 1. HTML 콘텐츠 설정
        if (data.page) {
            safeSetEditorValue('htmlEditor', data.page, 'HTML 콘텐츠를 설정할 수 없습니다');
        }
        
        // 2. 답안 설정
        if (data.answer) {
            const decodedAnswer = decodeUnicodeString(data.answer);
            safeSetEditorValue('answerEditor', decodedAnswer, '정답 에디터를 설정할 수 없습니다');
            safeSetEditorValue('answerInputEditor', decodedAnswer, '답안 입력 에디터를 설정할 수 없습니다');
            
            // answerEditorContainer에도 안전하게 설정
            try {
                setAnswerToContainer(decodedAnswer);
            } catch (e) {
                console.warn('answerEditorContainer 설정 실패:', e);
            }
        }
        
        // 3. 메타데이터와 태그 설정
        const decodedMetaData = decodeUnicodeString(data.meta_data || '{}');
        const decodedTags = decodeUnicodeString(data.tags || '{}');
        
        // 중앙 패널 에디터들
        safeSetEditorValue('metaEditor', decodedMetaData, '중앙 패널 메타데이터 에디터를 설정할 수 없습니다');
        safeSetEditorValue('tagsEditor', decodedTags, '중앙 패널 태그 에디터를 설정할 수 없습니다');
        
        // HTML탭 에디터들 (재초기화 시도 후 설정)
        if (!window.metaEditorInstance_html || !window.tagsEditorInstance_html) {
            console.log('HTML탭 에디터가 없어서 재초기화 시도');
            reinitializeHtmlTabEditors();
        }
        
        safeSetEditorValue('metaEditorHtml', decodedMetaData, 'HTML탭 메타데이터 에디터를 설정할 수 없습니다');
        safeSetEditorValue('tagsEditorHtml', decodedTags, 'HTML탭 태그 에디터를 설정할 수 없습니다');
        
        console.log('AI 응답 데이터 에디터 설정 완료');
        return true;
        
    } catch (error) {
        console.error('AI 응답 데이터 에디터 설정 중 오류:', error);
        return false;
    }
}

// 전역 함수로 등록
window.safeSetEditorValue = safeSetEditorValue;
window.checkAllEditorsStatus = checkAllEditorsStatus;
window.reinitializeHtmlTabEditors = reinitializeHtmlTabEditors;
window.safelySetAIResponseToEditors = safelySetAIResponseToEditors;


/**
 * 유니코드 문자열 디코딩
 */
function decodeUnicodeString(str) {
    try {
        // 유니코드 이스케이프 시퀀스를 실제 문자로 변환
        return str.replace(/\\u[\dA-F]{4}/gi, function (match) {
            return String.fromCharCode(parseInt(match.replace(/\\u/g, ''), 16));
        });
    } catch (e) {
        console.warn('유니코드 디코딩 실패:', e);
        return str;
    }
}

/**
 * 답안을 answerEditorContainer에 설정
 */
function setAnswerToContainer(answerData) {
    try {
        // 전역 answerEditorInstance 확인
        if (window.answerEditorInstance) {
            answerEditorInstance.setValue(answerData);
            console.log('answerEditorInstance에 답안 설정 완료');
            return;
        }
        
        // answerEditorContainer의 CodeMirror 인스턴스 확인
        const answerContainer = document.getElementById('answerEditorContainer');
        if (answerContainer) {
            // CodeMirror 인스턴스가 있는지 확인
            if (answerContainer.CodeMirror) {
                answerContainer.CodeMirror.setValue(answerData);
                console.log('answerEditorContainer CodeMirror에 답안 설정 완료');
                return;
            }
            
            // CodeMirror 인스턴스가 없으면 직접 생성하거나 textarea에 설정
            const textarea = answerContainer.querySelector('textarea');
            if (textarea) {
                textarea.value = answerData;
                console.log('answerEditorContainer textarea에 답안 설정 완료');
                return;
            }
        }
        
        console.warn('answerEditorContainer를 찾을 수 없습니다');
    } catch (e) {
        console.error('답안 설정 중 오류:', e);
    }
}

/**
 * 로딩 스피너 표시 (강화된 버전)
 */
/**
 * 로딩 스피너 표시 (강화된 버전)
 */
function showLoadingSpinner() {
    console.log('showLoadingSpinner 호출됨');
    
    try {
        // 기존 로딩 제거
        $('#ai-loading-spinner').remove();
        $('.loading-spinner').remove(); // 다른 스피너도 제거
        
        const loadingHtml = `
            <div id="ai-loading-spinner" class="loading-spinner fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center" style="z-index: 999999 !important; position: fixed !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important;">
                <div class="bg-white rounded-lg p-8 text-center shadow-2xl max-w-md mx-4">
                    <div class="inline-block animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mb-4"></div>
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">AI 문항 생성 중</h3>
                    <p class="text-gray-600 mb-1">잠시만 기다려주세요...</p>
                    <p class="text-sm text-gray-500">보통 5-10초 정도 소요됩니다</p>
                    <div class="mt-4 bg-gray-100 rounded-full h-1 overflow-hidden">
                        <div class="bg-blue-600 h-full rounded-full animate-pulse"></div>
                    </div>
                </div>
            </div>
        `;
        
        // DOM에 추가
        $('body').append(loadingHtml);
        console.log('로딩 스피너 DOM 추가 완료');
        
        // 스피너가 실제로 추가되었는지 확인
        const $spinner = $('#ai-loading-spinner');
        if ($spinner.length === 0) {
            console.error('로딩 스피너 추가 실패');
            return false;
        }
        
        // 강제로 스타일 적용 및 표시
        $spinner.css({
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100vw',
            'height': '100vh',
            'z-index': '999999',
            'display': 'flex',
            'background-color': 'rgba(0, 0, 0, 0.6)'
        }).show();
        
        console.log('로딩 스피너 표시 완료');
        return true;
        
    } catch (error) {
        console.error('로딩 스피너 표시 중 오류:', error);
        return false;
    }
}

/**
 * 로딩 스피너 숨기기 (강화된 버전)
 */
function hideLoadingSpinner() {
    console.log('hideLoadingSpinner 호출됨');
    
    try {
        const spinnerSelectors = ['#ai-loading-spinner', '.loading-spinner', '.spinner'];
        let removed = false;
        
        spinnerSelectors.forEach(selector => {
            const $spinners = $(selector);
            if ($spinners.length > 0) {
                console.log(`${selector} 스피너 ${$spinners.length}개 발견`);
                
                $spinners.each(function() {
                    const $spinner = $(this);
                    
                    // 페이드아웃 애니메이션
                    $spinner.fadeOut(200, function() {
                        $spinner.remove();
                        console.log(`${selector} 스피너 제거 완료`);
                    });
                    
                    // 3초 후 강제 제거 (페이드아웃이 실패할 경우 대비)
                    setTimeout(() => {
                        if ($spinner.length > 0) {
                            $spinner.remove();
                            console.log(`${selector} 스피너 강제 제거 완료`);
                        }
                    }, 3000);
                    
                    removed = true;
                });
            }
        });
        
        if (!removed) {
            console.log('제거할 스피너를 찾을 수 없음');
        }
        
        // DOM에서 완전히 제거되었는지 확인
        setTimeout(() => {
            const remainingSpinners = $('#ai-loading-spinner, .loading-spinner, .spinner').length;
            if (remainingSpinners > 0) {
                console.warn(`아직 ${remainingSpinners}개의 스피너가 남아있음, 강제 제거`);
                $('#ai-loading-spinner, .loading-spinner, .spinner').remove();
            }
        }, 1000);
        
        return true;
        
    } catch (error) {
        console.error('로딩 스피너 숨기기 중 오류:', error);
        
        // 오류 발생 시 강제로 모든 스피너 제거
        try {
            $('#ai-loading-spinner, .loading-spinner, .spinner').remove();
            console.log('오류 복구: 모든 스피너 강제 제거 완료');
        } catch (e) {
            console.error('강제 제거도 실패:', e);
        }
        
        return false;
    }
}

/**
 * 스피너 상태 확인 및 정리
 */
function checkAndCleanSpinners() {
    const spinnerCount = $('#ai-loading-spinner, .loading-spinner, .spinner').length;
    
    if (spinnerCount > 0) {
        console.log(`${spinnerCount}개의 스피너가 발견됨, 정리 시작`);
        hideLoadingSpinner();
        return false;
    }
    
    console.log('활성화된 스피너 없음');
    return true;
}

/**
 * 응급 스피너 제거 (전역 함수)
 */
window.emergencyRemoveSpinner = function() {
    console.log('응급 스피너 제거 실행');
    try {
        // jQuery로 제거
        $('#ai-loading-spinner, .loading-spinner, .spinner').remove();
        
        // 바닐라 JS로도 제거
        const spinners = document.querySelectorAll('#ai-loading-spinner, .loading-spinner, .spinner');
        spinners.forEach(spinner => {
            if (spinner && spinner.parentNode) {
                spinner.parentNode.removeChild(spinner);
            }
        });
        
        console.log('응급 스피너 제거 완료');
        showToast('스피너가 강제로 제거되었습니다', 'info');
        
    } catch (e) {
        console.error('응급 스피너 제거 실패:', e);
    }
};

// 전역적으로 스피너 정리 함수 등록
if (typeof window.CPAgent === 'undefined') {
    window.CPAgent = {};
}

window.CPAgent.Spinner = {
    show: showLoadingSpinner,
    hide: hideLoadingSpinner,
    check: checkAndCleanSpinners,
    emergency: window.emergencyRemoveSpinner
};


function showLoadingSpinner_0629() {
    console.log('showLoadingSpinner 호출됨');
    
    // 기존 로딩 제거
    $('#ai-loading-spinner').remove();
    
    const loadingHtml = `
        <div id="ai-loading-spinner" class="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50" style="z-index: 9999;">
            <div class="bg-white rounded-lg p-8 text-center shadow-2xl max-w-md mx-4">
                <div class="inline-block animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mb-4"></div>
                <h3 class="text-lg font-semibold text-gray-800 mb-2">AI 문항 생성 중</h3>
                <p class="text-gray-600 mb-1">잠시만 기다려주세요...</p>
                <p class="text-sm text-gray-500">보통 5-10초 정도 소요됩니다</p>
                <div class="mt-4 bg-gray-100 rounded-full h-1 overflow-hidden">
                    <div class="bg-blue-600 h-full rounded-full animate-pulse"></div>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(loadingHtml);
    console.log('로딩 스피너 DOM 추가 완료');
    
    // 강제로 스타일 적용
    $('#ai-loading-spinner').css({
        'position': 'fixed',
        'top': '0',
        'left': '0',
        'width': '100%',
        'height': '100%',
        'z-index': '9999',
        'display': 'flex'
    });
    
    console.log('로딩 스피너 스타일 강제 적용 완료');
}

/**
 * 로딩 스피너 숨기기 (강화된 버전)
 */
function hideLoadingSpinner() {
    console.log('hideLoadingSpinner 호출됨');
    
    const $spinner = $('#ai-loading-spinner');
    if ($spinner.length > 0) {
        $spinner.fadeOut(300, function() {
            $(this).remove();
            console.log('로딩 스피너 제거 완료');
        });
    } else {
        console.log('로딩 스피너를 찾을 수 없음');
    }
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
            
            // 답안 구조 적용 (유니코드 디코딩)
            if (template.answer) {
                const decodedAnswer = decodeUnicodeString(template.answer);
                answerEditor.setValue(decodedAnswer);
                answerInputEditor.setValue(decodedAnswer);
                
                // answerEditorContainer에도 답안 설정
                setAnswerToContainer(decodedAnswer);
            }
            
            // 메타데이터 적용 (유니코드 디코딩)
            if (template.meta_data) {
                const decodedMetaData = decodeUnicodeString(JSON.stringify(template.meta_data, null, 2));
                metaEditor.setValue(decodedMetaData);
                
                // HTML탭 메타 에디터에도 설정
                if (window.metaEditorInstance_html) {
                    window.metaEditorInstance_html.setValue(decodedMetaData);
                }
            }
            
            // 태그 적용 (유니코드 디코딩)
            if (template.tags) {
                const decodedTags = decodeUnicodeString(JSON.stringify(template.tags, null, 2));
                tagsEditor.setValue(decodedTags);
                
                // HTML탭 태그 에디터에도 설정
                if (window.tagsEditorInstance_html) {
                    window.tagsEditorInstance_html.setValue(decodedTags);
                }
            }
            
            // 미리보기 업데이트
            updatePreview();
            
            showToast(`템플릿 "${template.title}"이 적용되었습니다`, 'success');
        })
        .fail(function() {
            showToast('템플릿을 적용하는 중 오류가 발생했습니다', 'error');
        });
}


/* ========== 기본 CRUD 함수들 ========== */

/**
 * 문항 로드
 */
/**
 * 문항 로드 (HTML탭 메타데이터/태그 지원)
 */
/**
 * 문항 로드 (HTML탭 메타데이터/태그 지원 - 완전 수정 버전)
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
            
            // 답안 설정 (유니코드 디코딩)
            const decodedAnswer = decodeUnicodeString(data.answer || '{}');
            if (answerInputEditor) answerInputEditor.setValue(decodedAnswer);
            if (answerEditor) answerEditor.setValue(decodedAnswer);
            
            // answerEditorContainer에도 답안 설정
            setAnswerToContainer(decodedAnswer);
            
            // 메타데이터와 태그 설정 (유니코드 디코딩)
            const decodedMetaData = decodeUnicodeString(JSON.stringify(data.meta_data || {}, null, 2));
            const decodedTags = decodeUnicodeString(JSON.stringify(data.tags || {}, null, 2));
            
            console.log('로드된 메타데이터:', decodedMetaData);
            console.log('로드된 태그:', decodedTags);
            
            // 중앙 패널 에디터들 설정
            if (metaEditor) metaEditor.setValue(decodedMetaData);
            if (tagsEditor) tagsEditor.setValue(decodedTags);
            
            // HTML탭 에디터들에 안전하게 설정 (개선된 로직)
            setHtmlTabEditorsWithRetry(decodedMetaData, decodedTags, 0);
            
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
 * HTML탭 에디터들에 값 설정 (재시도 로직 포함)
 */
function setHtmlTabEditorsWithRetry(metaData, tagsData, retryCount) {
    const maxRetries = 3;
    const retryDelay = 300;
    
    console.log(`HTML탭 에디터 설정 시도 ${retryCount + 1}/${maxRetries + 1}`);
    
    try {
        let metaSuccess = false;
        let tagsSuccess = false;
        
        // 메타데이터 에디터 설정
        if (window.metaEditorInstance_html && typeof window.metaEditorInstance_html.setValue === 'function') {
            window.metaEditorInstance_html.setValue(metaData);
            console.log('HTML탭 메타데이터 설정 성공');
            metaSuccess = true;
        } else {
            console.warn('HTML탭 메타데이터 에디터를 찾을 수 없음');
        }
        
        // 태그 에디터 설정
        if (window.tagsEditorInstance_html && typeof window.tagsEditorInstance_html.setValue === 'function') {
            window.tagsEditorInstance_html.setValue(tagsData);
            console.log('HTML탭 태그 설정 성공');
            tagsSuccess = true;
        } else {
            console.warn('HTML탭 태그 에디터를 찾을 수 없음');
        }
        
        // 실패한 경우 재시도
        if ((!metaSuccess || !tagsSuccess) && retryCount < maxRetries) {
            console.log(`일부 에디터 설정 실패, ${retryDelay}ms 후 재시도`);
            
            // 에디터가 없으면 강제 재초기화
            if (!window.metaEditorInstance_html || !window.tagsEditorInstance_html) {
                console.log('HTML탭 에디터 재초기화 시도');
                forceReinitializeHtmlTabEditors();
            }
            
            setTimeout(() => {
                setHtmlTabEditorsWithRetry(metaData, tagsData, retryCount + 1);
            }, retryDelay);
        } else if (metaSuccess && tagsSuccess) {
            console.log('HTML탭 에디터 설정 완료');
        } else {
            console.warn('HTML탭 에디터 설정 최종 실패');
        }
        
    } catch (error) {
        console.error('HTML탭 에디터 설정 중 오류:', error);
        
        if (retryCount < maxRetries) {
            setTimeout(() => {
                setHtmlTabEditorsWithRetry(metaData, tagsData, retryCount + 1);
            }, retryDelay);
        }
    }
}




function loadContent_0629(contentId) {
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
            
            // 답안 설정 (유니코드 디코딩)
            const decodedAnswer = decodeUnicodeString(data.answer || '{}');
            answerInputEditor.setValue(decodedAnswer);
            answerEditor.setValue(decodedAnswer);
            
            // answerEditorContainer에도 답안 설정
            setAnswerToContainer(decodedAnswer);
            
            // 메타데이터와 태그 설정 (유니코드 디코딩)
            const decodedMetaData = decodeUnicodeString(JSON.stringify(data.meta_data || {}, null, 2));
            const decodedTags = decodeUnicodeString(JSON.stringify(data.tags || {}, null, 2));
            
            // 중앙 패널 에디터들 설정
            metaEditor.setValue(decodedMetaData);
            tagsEditor.setValue(decodedTags);
            
            // HTML탭 에디터들에도 설정
            if (window.metaEditorInstance_html) {
                window.metaEditorInstance_html.setValue(decodedMetaData);
            }
            if (window.tagsEditorInstance_html) {
                window.tagsEditorInstance_html.setValue(decodedTags);
            }
            
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
 * 콘텐츠 저장
 */
function saveContent() {
    debugLog('CONTENT', '콘텐츠 저장 시작');
    
    // 1. 저장 전 이미지 자동 검증 및 정리
    if (window.CPAgent && CPAgent.Image) {
        CPAgent.Image.validateAndCleanupBeforeSave();
    }
    
    // 2. 변경된 텍스트 색상 초기화
    resetTextColors();
    
    // 3. HTML 에디터의 내용을 최신 상태로 업데이트
    updatePreviewFromHtml();
    
    // 4. HTML탭의 메타데이터와 태그를 중앙 패널과 동기화
    if (window.metaEditorInstance_html) {
        metaEditor.setValue(window.metaEditorInstance_html.getValue());
    }
    if (window.tagsEditorInstance_html) {
        tagsEditor.setValue(window.tagsEditorInstance_html.getValue());
    }
    
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
    
    // 로딩 상태 표시
    const $saveBtn = $('button[onclick="CPAgent.Content.saveContent()"]');
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
            if (window.temporaryUploads) {
                temporaryUploads = [];
            }
            
            // 변경된 모든 요소의 표시 제거
            $('[data-changed="true"]').removeAttr('data-changed');
            
            // 편집 컨트롤 업데이트
            if (window.CPAgent && CPAgent.UI) {
                CPAgent.UI.updateEditControls();
            }
            
            // 리스트 새로고침
            if (window.CPAgent && CPAgent.Data) {
                CPAgent.Data.searchContents();
            }
            
            timer.end();
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
    if (window.temporaryUploads && temporaryUploads.length > 0) {
        cleanupTemporaryUploads();
    }
    
    // 이미지 변경사항 취소
    if (window.CPAgent && CPAgent.Image) {
        CPAgent.Image.cancelImageChanges();
    }
    
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
    
    // HTML탭 에디터들도 초기화
    if (window.metaEditorInstance_html) {
        window.metaEditorInstance_html.setValue('{\n  "difficulty": "중",\n  "estimated_time": 300,\n  "subject": "",\n  "chapter": ""\n}');
    }
    if (window.tagsEditorInstance_html) {
        const simpleTemplate = generateSimpleTemplateFormatTags();
        window.tagsEditorInstance_html.setValue(JSON.stringify(simpleTemplate, null, 2));
    }
    
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
    if (window.CPAgent && CPAgent.UI) {
        CPAgent.UI.updateEditControls();
    }
    
    showToast('새 콘텐츠 작성을 시작합니다', 'success');
    
    // 제목 입력란에 포커스
    setTimeout(() => {
        $('#title').focus();
    }, 100);
}

/**
 * HTML 편집기에서 미리보기 업데이트
 */
function updatePreviewFromHtml() {
    const html = htmlEditorInstance.getValue();
    $('#previewContent').html(html);
    if (window.CPAgent && CPAgent.TextEditing) {
        CPAgent.TextEditing.updateEditableContent(html);
    }
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