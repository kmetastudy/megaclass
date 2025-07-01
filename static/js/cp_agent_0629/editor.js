// static/js/cp_agent/editor.js - 에디터 초기화 및 관리 (완전 수정 버전)

/* ========== 에디터 초기화 ========== */

/**
 * 모든 에디터 초기화 (순서 및 참조 오류 수정)
 */
function initializeEditors() {
    debugLog('EDITOR', '에디터 초기화 시작');
    
    const timer = new PerformanceTimer('에디터 초기화');
    
    try {
        // 1단계: 메인 에디터들 먼저 초기화
        initializeAnswerInputEditor();
        initializeMetaEditor();
        initializeTagsEditor();
        initializeHtmlEditor();
        initializeAnswerEditor();
        
        // 2단계: HTML탭 에디터들은 지연 초기화 (메인 에디터들이 준비된 후)
        setTimeout(() => {
            initializeHtmlTabMetaEditor();
            initializeHtmlTabTagsEditor();
            debugLog('EDITOR', 'HTML탭 에디터 지연 초기화 완료');
        }, 200);
        
        timer.end();
        debugLog('EDITOR', '모든 에디터 초기화 시작 완료');
        
    } catch (error) {
        debugLog('EDITOR', '에디터 초기화 실패', error);
        showToast('에디터 초기화 중 오류가 발생했습니다', 'error');
        throw error;
    }
}

/**
 * HTML탭 메타데이터 에디터 초기화 (에러 수정 버전)
 */
function initializeHtmlTabMetaEditor() {
    const container = document.getElementById('metaEditorContainer');
    if (!container) {
        debugLog('EDITOR', 'HTML탭 메타데이터 에디터 컨테이너를 찾을 수 없음');
        return;
    }
    
    // 기존 에디터 제거
    if (window.metaEditorInstance_html) {
        try {
            window.metaEditorInstance_html.toTextArea();
        } catch (e) {
            console.warn('기존 메타데이터 에디터 제거 실패:', e);
        }
    }
    
    // 컨테이너 초기화
    container.innerHTML = '';
    
    window.metaEditorInstance_html = CodeMirror(container, {
        value: '{\n  "difficulty": "중",\n  "estimated_time": 300,\n  "subject": "",\n  "chapter": ""\n}',
        mode: 'javascript',
        theme: 'material',
        lineNumbers: true,
        lineWrapping: true,
        viewportMargin: Infinity,
        autoCloseBrackets: true,
        matchBrackets: true,
        foldGutter: true,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"]
    });
    
    window.metaEditorInstance_html.setSize(null, '100%');
    
    // 실시간 동기화 (중앙 패널과) - 수정된 부분
    window.metaEditorInstance_html.on('change', function() {
        const value = window.metaEditorInstance_html.getValue();
        // 전역 변수 metaEditor 참조 (window.metaEditor 아님)
        if (typeof metaEditor !== 'undefined' && metaEditor && typeof metaEditor.setValue === 'function') {
            try {
                metaEditor.setValue(value);
            } catch (e) {
                console.warn('메타데이터 동기화 실패:', e);
            }
        }
    });
    
    debugLog('EDITOR', 'HTML탭 메타데이터 에디터 초기화 완료');
}

/**
 * HTML탭 태그 에디터 초기화 (에러 수정 버전)
 */
function initializeHtmlTabTagsEditor() {
    const container = document.getElementById('tagsEditorContainer');
    if (!container) {
        debugLog('EDITOR', 'HTML탭 태그 에디터 컨테이너를 찾을 수 없음');
        return;
    }
    
    // 기존 에디터 제거
    if (window.tagsEditorInstance_html) {
        try {
            window.tagsEditorInstance_html.toTextArea();
        } catch (e) {
            console.warn('기존 태그 에디터 제거 실패:', e);
        }
    }
    
    // 컨테이너 초기화
    container.innerHTML = '';
    
    window.tagsEditorInstance_html = CodeMirror(container, {
        value: '{\n  "competency": "수리능력",\n  "sub_competency": "도표분석능력",\n  "difficulty": "중",\n  "question_type": "multiple-choice",\n  "order": 1\n}',
        mode: 'javascript',
        theme: 'material',
        lineNumbers: true,
        lineWrapping: true,
        viewportMargin: Infinity,
        autoCloseBrackets: true,
        matchBrackets: true,
        foldGutter: true,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"]
    });
    
    window.tagsEditorInstance_html.setSize(null, '100%');
    
    // 실시간 동기화 (중앙 패널과) - 수정된 부분
    window.tagsEditorInstance_html.on('change', function() {
        const value = window.tagsEditorInstance_html.getValue();
        // 전역 변수 tagsEditor 참조 (window.tagsEditor 아님)
        if (typeof tagsEditor !== 'undefined' && tagsEditor && typeof tagsEditor.setValue === 'function') {
            try {
                tagsEditor.setValue(value);
            } catch (e) {
                console.warn('태그 동기화 실패:', e);
            }
        }
    });
    
    debugLog('EDITOR', 'HTML탭 태그 에디터 초기화 완료');
}

/**
 * 답안 입력 JSON 에디터 초기화
 */
function initializeAnswerInputEditor() {
    const container = document.getElementById('answerInputEditor');
    if (!container) {
        throw new Error('answerInputEditor 컨테이너를 찾을 수 없습니다');
    }
    
    answerInputEditor = CodeMirror(container, {
        value: '{}',
        mode: 'javascript',
        theme: 'material',
        lineNumbers: true,
        lineWrapping: true,
        viewportMargin: Infinity,
        autoCloseBrackets: true,
        matchBrackets: true,
        foldGutter: true,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"]
    });
    
    answerInputEditor.setSize(null, 200);
    
    // 변경 이벤트 핸들러
    answerInputEditor.on('change', function() {
        $('#answer_input').val(answerInputEditor.getValue());
    });
    
    debugLog('EDITOR', '답안 입력 에디터 초기화 완료');
}

/**
 * 메타데이터 JSON 에디터 초기화
 */
function initializeMetaEditor() {
    const container = document.getElementById('metaEditor');
    if (!container) {
        throw new Error('metaEditor 컨테이너를 찾을 수 없습니다');
    }
    
    metaEditor = CodeMirror(container, {
        value: '{}',
        mode: 'javascript',
        theme: 'material',
        lineNumbers: true,
        lineWrapping: true,
        viewportMargin: Infinity,
        autoCloseBrackets: true,
        matchBrackets: true,
        foldGutter: true,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"]
    });
    
    metaEditor.setSize(null, 150);
    
    // 변경 이벤트 핸들러 (HTML탭과 동기화 포함)
    metaEditor.on('change', function() {
        $('#meta_content').val(metaEditor.getValue());
        
        // HTML탭 에디터와 동기화
        if (window.metaEditorInstance_html && typeof window.metaEditorInstance_html.setValue === 'function') {
            try {
                const currentValue = window.metaEditorInstance_html.getValue();
                const newValue = metaEditor.getValue();
                if (currentValue !== newValue) {
                    window.metaEditorInstance_html.setValue(newValue);
                }
            } catch (e) {
                console.warn('메타데이터 역동기화 실패:', e);
            }
        }
    });
    
    debugLog('EDITOR', '메타데이터 에디터 초기화 완료');
}

/**
 * 태그 JSON 에디터 초기화
 */
function initializeTagsEditor() {
    const container = document.getElementById('tagsEditor');
    if (!container) {
        throw new Error('tagsEditor 컨테이너를 찾을 수 없습니다');
    }
    
    tagsEditor = CodeMirror(container, {
        value: '{}',
        mode: 'javascript',
        theme: 'material',
        lineNumbers: true,
        lineWrapping: true,
        viewportMargin: Infinity,
        autoCloseBrackets: true,
        matchBrackets: true,
        foldGutter: true,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"]
    });
    
    tagsEditor.setSize(null, 150);
    
    // 변경 이벤트 핸들러 (HTML탭과 동기화 포함)
    tagsEditor.on('change', function() {
        $('#tags_content').val(tagsEditor.getValue());
        
        // HTML탭 에디터와 동기화
        if (window.tagsEditorInstance_html && typeof window.tagsEditorInstance_html.setValue === 'function') {
            try {
                const currentValue = window.tagsEditorInstance_html.getValue();
                const newValue = tagsEditor.getValue();
                if (currentValue !== newValue) {
                    window.tagsEditorInstance_html.setValue(newValue);
                }
            } catch (e) {
                console.warn('태그 역동기화 실패:', e);
            }
        }
    });
    
    debugLog('EDITOR', '태그 에디터 초기화 완료');
}

/**
 * HTML 편집 에디터 초기화
 */
function initializeHtmlEditor() {
    const container = document.getElementById('htmlEditorContainer');
    if (!container) {
        throw new Error('htmlEditorContainer 컨테이너를 찾을 수 없습니다');
    }
    
    htmlEditorInstance = CodeMirror(container, {
        mode: 'xml',
        theme: 'material',
        lineNumbers: true,
        lineWrapping: true,
        viewportMargin: Infinity,
        autoCloseTags: true,
        autoCloseBrackets: true,
        matchBrackets: true,
        matchTags: true,
        foldGutter: true,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
        extraKeys: {
            "Ctrl-Space": "autocomplete",
            "F11": function(cm) {
                cm.setOption("fullScreen", !cm.getOption("fullScreen"));
            },
            "Esc": function(cm) {
                if (cm.getOption("fullScreen")) cm.setOption("fullScreen", false);
            }
        }
    });
    
    htmlEditorInstance.setSize(null, '100%');
    
    // 변경 이벤트 핸들러 (디바운스 적용)
    let htmlChangeTimeout;
    htmlEditorInstance.on('change', function() {
        clearTimeout(htmlChangeTimeout);
        htmlChangeTimeout = setTimeout(() => {
            if (window.CPAgent && CPAgent.Content) {
                CPAgent.Content.updatePreviewFromHtml();
            }
        }, 500);
    });
    
    debugLog('EDITOR', 'HTML 에디터 초기화 완료');
}

/**
 * 정답 JSON 에디터 초기화
 */
function initializeAnswerEditor() {
    const container = document.getElementById('answerEditorContainer');
    if (!container) {
        throw new Error('answerEditorContainer 컨테이너를 찾을 수 없습니다');
    }
    
    answerEditor = CodeMirror(container, {
        value: '{}',
        mode: 'javascript',
        theme: 'material',
        lineNumbers: true,
        lineWrapping: true,
        viewportMargin: Infinity,
        autoCloseBrackets: true,
        matchBrackets: true,
        foldGutter: true,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"]
    });
    
    answerEditor.setSize(null, '100%');
    
    debugLog('EDITOR', '정답 에디터 초기화 완료');
}

/**
 * HTML탭 에디터들 강제 재초기화
 */
function forceReinitializeHtmlTabEditors() {
    debugLog('EDITOR', 'HTML탭 에디터들 강제 재초기화 시작');
    
    try {
        // 기존 에디터 제거
        if (window.metaEditorInstance_html) {
            try {
                window.metaEditorInstance_html.toTextArea();
                window.metaEditorInstance_html = null;
            } catch (e) {
                console.warn('메타데이터 에디터 제거 실패:', e);
            }
        }
        
        if (window.tagsEditorInstance_html) {
            try {
                window.tagsEditorInstance_html.toTextArea();
                window.tagsEditorInstance_html = null;
            } catch (e) {
                console.warn('태그 에디터 제거 실패:', e);
            }
        }
        
        // 재초기화
        setTimeout(() => {
            initializeHtmlTabMetaEditor();
            initializeHtmlTabTagsEditor();
            debugLog('EDITOR', 'HTML탭 에디터들 강제 재초기화 완료');
            showToast('HTML탭 에디터가 재초기화되었습니다', 'success');
        }, 100);
        
    } catch (error) {
        debugLog('EDITOR', 'HTML탭 에디터 강제 재초기화 실패', error);
        showToast('HTML탭 에디터 재초기화 중 오류가 발생했습니다', 'error');
    }
}

/* ========== 에디터 유틸리티 함수들 ========== */

/**
 * 모든 에디터 새로고침
 */
function refreshAllEditors() {
    debugLog('EDITOR', '모든 에디터 새로고침');
    
    const editors = [
        answerInputEditor,
        metaEditor, 
        tagsEditor,
        htmlEditorInstance,
        answerEditor,
        window.metaEditorInstance_html,
        window.tagsEditorInstance_html
    ];
    
    editors.forEach((editor, index) => {
        if (editor && typeof editor.refresh === 'function') {
            try {
                editor.refresh();
                debugLog('EDITOR', `에디터 ${index} 새로고침 완료`);
            } catch (error) {
                debugLog('EDITOR', `에디터 ${index} 새로고침 실패`, error);
            }
        }
    });
}

/**
 * 에디터 크기 조정
 */
function resizeEditors() {
    debugLog('EDITOR', '에디터 크기 조정');
    
    if ($('#htmlTab').hasClass('active') && htmlEditorInstance) {
        setTimeout(() => {
            htmlEditorInstance.refresh();
            
            // HTML탭 에디터들도 리프레시
            if (window.metaEditorInstance_html) {
                window.metaEditorInstance_html.refresh();
            }
            if (window.tagsEditorInstance_html) {
                window.tagsEditorInstance_html.refresh();
            }
        }, 100);
    }
}

/**
 * JSON 유효성 검사
 */
function validateJsonEditor(editor, editorName) {
    try {
        const content = editor.getValue().trim();
        if (content && content !== '{}') {
            JSON.parse(content);
        }
        return { valid: true };
    } catch (error) {
        return { 
            valid: false, 
            error: `${editorName}의 JSON 형식이 올바르지 않습니다: ${error.message}` 
        };
    }
}

/**
 * 모든 JSON 에디터 유효성 검사
 */
function validateAllJsonEditors() {
    const editors = [
        { editor: answerInputEditor, name: '답안 입력' },
        { editor: metaEditor, name: '메타데이터' },
        { editor: tagsEditor, name: '태그' },
        { editor: answerEditor, name: '정답' },
        { editor: window.metaEditorInstance_html, name: 'HTML탭 메타데이터' },
        { editor: window.tagsEditorInstance_html, name: 'HTML탭 태그' }
    ];
    
    for (const { editor, name } of editors) {
        if (editor) {
            const result = validateJsonEditor(editor, name);
            if (!result.valid) {
                showToast(result.error, 'error');
                editor.focus();
                return false;
            }
        }
    }
    
    return true;
}

/**
 * 모든 에디터 내용 초기화
 */
function resetAllEditors() {
    debugLog('EDITOR', '모든 에디터 내용 초기화');
    
    if (answerInputEditor) answerInputEditor.setValue('{}');
    if (metaEditor) metaEditor.setValue('{}');
    if (tagsEditor) tagsEditor.setValue('{}');
    if (htmlEditorInstance) htmlEditorInstance.setValue('');
    if (answerEditor) answerEditor.setValue('{}');
    
    // HTML탭 에디터들도 초기화
    if (window.metaEditorInstance_html) {
        window.metaEditorInstance_html.setValue('{\n  "difficulty": "중",\n  "estimated_time": 300,\n  "subject": "",\n  "chapter": ""\n}');
    }
    if (window.tagsEditorInstance_html) {
        window.tagsEditorInstance_html.setValue('{\n  "competency": "수리능력",\n  "sub_competency": "도표분석능력",\n  "difficulty": "중",\n  "question_type": "multiple-choice",\n  "order": 1\n}');
    }
}

/**
 * 에디터 테마 변경
 */
function changeEditorTheme(theme = 'material') {
    debugLog('EDITOR', '에디터 테마 변경', theme);
    
    const editors = [
        answerInputEditor,
        metaEditor,
        tagsEditor,
        htmlEditorInstance,
        answerEditor,
        window.metaEditorInstance_html,
        window.tagsEditorInstance_html
    ];
    
    editors.forEach(editor => {
        if (editor && typeof editor.setOption === 'function') {
            editor.setOption('theme', theme);
        }
    });
}

/* ========== 전역 에디터 네임스페이스 ========== */
window.CPAgent.Editor = {
    initialize: initializeEditors,
    refreshAll: refreshAllEditors,
    resize: resizeEditors,
    validateAllJson: validateAllJsonEditors,
    resetAll: resetAllEditors,
    changeTheme: changeEditorTheme,
    forceReinitializeHtmlTab: forceReinitializeHtmlTabEditors,
    
    // 개별 에디터 접근
    get answerInput() { return answerInputEditor; },
    get meta() { return metaEditor; },
    get tags() { return tagsEditor; },
    get html() { return htmlEditorInstance; },
    get answer() { return answerEditor; },
    get htmlTabMeta() { return window.metaEditorInstance_html; },
    get htmlTabTags() { return window.tagsEditorInstance_html; }
};