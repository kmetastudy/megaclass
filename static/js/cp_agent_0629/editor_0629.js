// static/js/cp_agent/editor.js - 에디터 초기화 및 관리

/* ========== 에디터 초기화 ========== */

/**
 * 모든 에디터 초기화
 */

/**
 * 모든 에디터 초기화 (HTML탭 에디터 포함)
 */
function initializeEditors() {
    debugLog('EDITOR', '에디터 초기화 시작');
    
    const timer = new PerformanceTimer('에디터 초기화');
    
    try {
        // 기존 에디터들 초기화
        initializeAnswerInputEditor();
        initializeMetaEditor();
        initializeTagsEditor();
        initializeHtmlEditor();
        initializeAnswerEditor();
        
        // HTML탭 전용 에디터들 초기화 (새로 추가)
        initializeHtmlTabMetaEditor();
        initializeHtmlTabTagsEditor();
        
        timer.end();
        debugLog('EDITOR', '모든 에디터 초기화 완료');
        
    } catch (error) {
        debugLog('EDITOR', '에디터 초기화 실패', error);
        showToast('에디터 초기화 중 오류가 발생했습니다', 'error');
        throw error;
    }
}


/**
 * HTML탭 메타데이터 에디터 초기화 (새로 추가)
 */
function initializeHtmlTabMetaEditor() {
    const container = document.getElementById('metaEditorContainer');
    if (!container) {
        debugLog('EDITOR', 'HTML탭 메타데이터 에디터 컨테이너를 찾을 수 없음');
        return;
    }
    
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
    
    // 실시간 동기화 (중앙 패널과)
    window.metaEditorInstance_html.on('change', function() {
        const value = window.metaEditorInstance_html.getValue();
        if (window.metaEditor) {
            window.metaEditor.setValue(value);
        }
    });
    
    debugLog('EDITOR', 'HTML탭 메타데이터 에디터 초기화 완료');
}

/**
 * HTML탭 태그 에디터 초기화 (새로 추가)
 */
function initializeHtmlTabTagsEditor() {
    const container = document.getElementById('tagsEditorContainer');
    if (!container) {
        debugLog('EDITOR', 'HTML탭 태그 에디터 컨테이너를 찾을 수 없음');
        return;
    }
    
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
    
    // 실시간 동기화 (중앙 패널과)
    window.tagsEditorInstance_html.on('change', function() {
        const value = window.tagsEditorInstance_html.getValue();
        if (window.tagsEditor) {
            window.tagsEditor.setValue(value);
        }
    });
    
    debugLog('EDITOR', 'HTML탭 태그 에디터 초기화 완료');
}

function initializeEditors_0629() {
    debugLog('EDITOR', '에디터 초기화 시작');
    
    const timer = new PerformanceTimer('에디터 초기화');
    
    try {
        // 답안 입력 JSON 에디터
        initializeAnswerInputEditor();
        
        // 메타데이터 JSON 에디터
        initializeMetaEditor();
        
        // 태그 JSON 에디터
        initializeTagsEditor();
        
        // HTML 편집 에디터
        initializeHtmlEditor();
        
        // 정답 JSON 에디터
        initializeAnswerEditor();
        
        timer.end();
        debugLog('EDITOR', '모든 에디터 초기화 완료');
        
    } catch (error) {
        debugLog('EDITOR', '에디터 초기화 실패', error);
        showToast('에디터 초기화 중 오류가 발생했습니다', 'error');
        throw error;
    }
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
    
    // 포커스 이벤트
    answerInputEditor.on('focus', function() {
        debugLog('EDITOR', '답안 입력 에디터 포커스');
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
    
    // 변경 이벤트 핸들러
    metaEditor.on('change', function() {
        $('#meta_content').val(metaEditor.getValue());
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
    
    // 변경 이벤트 핸들러
    tagsEditor.on('change', function() {
        $('#tags_content').val(tagsEditor.getValue());
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
            CPAgent.Content.updatePreviewFromHtml();
        }, 500); // 500ms 디바운스
    });
    
    // 커서 위치 변경 시 상태바 업데이트 (선택사항)
    htmlEditorInstance.on('cursorActivity', function() {
        const cursor = htmlEditorInstance.getCursor();
        debugLog('EDITOR', `HTML 에디터 커서 위치: 줄 ${cursor.line + 1}, 열 ${cursor.ch + 1}`);
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
    
    // 변경 이벤트는 자동 저장이 아니므로 로그만
    answerEditor.on('change', function() {
        debugLog('EDITOR', '정답 에디터 변경됨');
    });
    
    debugLog('EDITOR', '정답 에디터 초기화 완료');
}

/* ========== 에디터 유틸리티 함수들 ========== */
// 기존 refreshAllEditors 함수에도 추가
function refreshAllEditors() {
    debugLog('EDITOR', '모든 에디터 새로고침');
    
    const editors = [
        answerInputEditor,
        metaEditor, 
        tagsEditor,
        htmlEditorInstance,
        answerEditor,
        window.metaEditorInstance_html,  // 새로 추가
        window.tagsEditorInstance_html   // 새로 추가
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
 * 모든 에디터 새로고침
 */
function refreshAllEditors_0629() {
    debugLog('EDITOR', '모든 에디터 새로고침');
    
    const editors = [
        answerInputEditor,
        metaEditor, 
        tagsEditor,
        htmlEditorInstance,
        answerEditor
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
    
    // 현재 탭이 HTML 탭인 경우에만 HTML 에디터 크기 조정
    if ($('#htmlTab').hasClass('active') && htmlEditorInstance) {
        setTimeout(() => {
            htmlEditorInstance.refresh();
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
        { editor: window.metaEditorInstance_html, name: 'HTML탭 메타데이터' },  // 새로 추가
        { editor: window.tagsEditorInstance_html, name: 'HTML탭 태그' }        // 새로 추가
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

// 기존 resetAllEditors 함수에도 추가
function resetAllEditors() {
    debugLog('EDITOR', '모든 에디터 내용 초기화');
    
    if (answerInputEditor) answerInputEditor.setValue('{}');
    if (metaEditor) metaEditor.setValue('{}');
    if (tagsEditor) tagsEditor.setValue('{}');
    if (htmlEditorInstance) htmlEditorInstance.setValue('');
    if (answerEditor) answerEditor.setValue('{}');
    
    // HTML탭 에디터들도 초기화 (새로 추가)
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

// 기존 changeEditorTheme 함수에도 추가
function changeEditorTheme(theme = 'material') {
    debugLog('EDITOR', '에디터 테마 변경', theme);
    
    const editors = [
        answerInputEditor,
        metaEditor,
        tagsEditor,
        htmlEditorInstance,
        answerEditor,
        window.metaEditorInstance_html,  // 새로 추가
        window.tagsEditorInstance_html   // 새로 추가
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
    
    // 개별 에디터 접근
    get answerInput() { return answerInputEditor; },
    get meta() { return metaEditor; },
    get tags() { return tagsEditor; },
    get html() { return htmlEditorInstance; },
    get answer() { return answerEditor; }
};