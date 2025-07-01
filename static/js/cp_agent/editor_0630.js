// static/js/cp_agent/editor.js - 에디터 초기화 및 관리 (수정됨)

/* ========== 에디터 초기화 ========== */

/**
 * 모든 에디터 초기화
 */
function initializeAllEditors() {
    debugLog('EDITOR', '모든 에디터 초기화 시작');
    
    try {
        const timer = new window.PerformanceTimer('에디터 초기화');
        
        // 순차적으로 에디터 초기화
        initializeAnswerInputEditor();
        initializeMetaEditor();
        initializeTagsEditor();
        initializeHtmlEditor();
        initializeAnswerEditor();
        
        // HTML탭 에디터들은 지연 초기화
        setTimeout(() => {
            initializeHtmlTabEditors();
        }, 300);
        
        timer.end();
        debugLog('EDITOR', '모든 에디터 초기화 완료');
        
        return true;
    } catch (error) {
        debugLog('EDITOR', '에디터 초기화 실패', error);
        return false;
    }
}

/**
 * 답안 입력 에디터 초기화
 */
function initializeAnswerInputEditor() {
    try {
        const container = document.getElementById('answerInputEditor');
        if (!container) {
            console.warn('answerInputEditor 컨테이너를 찾을 수 없음');
            return false;
        }
        
        window.answerInputEditor = CodeMirror(container, {
            value: '{}',
            mode: 'javascript',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            viewportMargin: Infinity,
            autoCloseBrackets: true,
            matchBrackets: true
        });
        
        window.answerInputEditor.setSize(null, 150);
        debugLog('EDITOR', 'answerInputEditor 초기화 완료');
        return true;
    } catch (error) {
        console.error('answerInputEditor 초기화 실패:', error);
        return false;
    }
}

/**
 * 메타데이터 에디터 초기화
 */
function initializeMetaEditor() {
    try {
        const container = document.getElementById('metaEditor');
        if (!container) {
            console.warn('metaEditor 컨테이너를 찾을 수 없음');
            return false;
        }
        
        window.metaEditor = CodeMirror(container, {
            value: '{}',
            mode: 'javascript',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            viewportMargin: Infinity,
            autoCloseBrackets: true,
            matchBrackets: true
        });
        
        window.metaEditor.setSize(null, 150);
        debugLog('EDITOR', 'metaEditor 초기화 완료');
        return true;
    } catch (error) {
        console.error('metaEditor 초기화 실패:', error);
        return false;
    }
}

/**
 * 태그 에디터 초기화
 */
function initializeTagsEditor() {
    try {
        const container = document.getElementById('tagsEditor');
        if (!container) {
            console.warn('tagsEditor 컨테이너를 찾을 수 없음');
            return false;
        }
        
        window.tagsEditor = CodeMirror(container, {
            value: '{}',
            mode: 'javascript',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            viewportMargin: Infinity,
            autoCloseBrackets: true,
            matchBrackets: true
        });
        
        window.tagsEditor.setSize(null, 150);
        debugLog('EDITOR', 'tagsEditor 초기화 완료');
        return true;
    } catch (error) {
        console.error('tagsEditor 초기화 실패:', error);
        return false;
    }
}

/**
 * HTML 에디터 초기화
 */
function initializeHtmlEditor() {
    try {
        const container = document.getElementById('htmlEditorContainer');
        if (!container) {
            console.warn('htmlEditorContainer를 찾을 수 없음');
            return false;
        }
        
        window.htmlEditorInstance = CodeMirror(container, {
            value: '',
            mode: 'xml',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            viewportMargin: Infinity,
            autoCloseBrackets: true,
            matchBrackets: true,
            autoCloseTags: true
        });
        
        window.htmlEditorInstance.setSize(null, '100%');
        debugLog('EDITOR', 'htmlEditorInstance 초기화 완료');
        return true;
    } catch (error) {
        console.error('htmlEditorInstance 초기화 실패:', error);
        return false;
    }
}

/**
 * 답안 에디터 초기화 (HTML탭)
 */
function initializeAnswerEditor() {
    try {
        const container = document.getElementById('answerEditorContainer');
        if (!container) {
            console.warn('answerEditorContainer를 찾을 수 없음');
            return false;
        }
        
        window.answerEditor = CodeMirror(container, {
            value: '{}',
            mode: 'javascript',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            viewportMargin: Infinity,
            autoCloseBrackets: true,
            matchBrackets: true
        });
        
        window.answerEditor.setSize(null, '100%');
        debugLog('EDITOR', 'answerEditor 초기화 완료');
        return true;
    } catch (error) {
        console.error('answerEditor 초기화 실패:', error);
        return false;
    }
}

/**
 * HTML탭 에디터들 초기화
 */
function initializeHtmlTabEditors() {
    debugLog('EDITOR', 'HTML탭 에디터 초기화 시작');
    
    try {
        // 메타데이터 에디터 (HTML탭)
        const metaContainer = document.getElementById('metaEditorContainer');
        if (metaContainer) {
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
            debugLog('EDITOR', 'metaEditorInstance_html 초기화 완료');
        }
        
        // 태그 에디터 (HTML탭)
        const tagsContainer = document.getElementById('tagsEditorContainer');
        if (tagsContainer) {
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
            debugLog('EDITOR', 'tagsEditorInstance_html 초기화 완료');
        }
        
        return true;
    } catch (error) {
        console.error('HTML탭 에디터 초기화 실패:', error);
        return false;
    }
}

/* ========== 에디터 관리 함수들 ========== */

/**
 * 모든 에디터 새로고침
 */
function refreshAllEditors() {
    debugLog('EDITOR', '모든 에디터 새로고침');
    
    const editors = [
        window.answerInputEditor,
        window.metaEditor,
        window.tagsEditor,
        window.htmlEditorInstance,
        window.answerEditor,
        window.metaEditorInstance_html,
        window.tagsEditorInstance_html
    ];
    
    editors.forEach((editor, index) => {
        if (editor && typeof editor.refresh === 'function') {
            try {
                editor.refresh();
                debugLog('EDITOR', `에디터 ${index} 새로고침 완료`);
            } catch (e) {
                console.warn(`에디터 ${index} 새로고침 실패:`, e);
            }
        }
    });
}

/**
 * 에디터 크기 조정
 */
function resizeAllEditors() {
    debugLog('EDITOR', '모든 에디터 크기 조정');
    
    const editors = [
        { editor: window.answerInputEditor, height: 150 },
        { editor: window.metaEditor, height: 150 },
        { editor: window.tagsEditor, height: 150 },
        { editor: window.htmlEditorInstance, height: '100%' },
        { editor: window.answerEditor, height: '100%' },
        { editor: window.metaEditorInstance_html, height: '100%' },
        { editor: window.tagsEditorInstance_html, height: '100%' }
    ];
    
    editors.forEach(({ editor, height }) => {
        if (editor && typeof editor.setSize === 'function') {
            try {
                editor.setSize(null, height);
            } catch (e) {
                console.warn('에디터 크기 조정 실패:', e);
            }
        }
    });
}

/**
 * 에디터 테마 변경
 */
function changeEditorTheme(theme = 'material') {
    debugLog('EDITOR', '에디터 테마 변경', theme);
    
    const editors = [
        window.answerInputEditor,
        window.metaEditor,
        window.tagsEditor,
        window.htmlEditorInstance,
        window.answerEditor,
        window.metaEditorInstance_html,
        window.tagsEditorInstance_html
    ];
    
    editors.forEach(editor => {
        if (editor && typeof editor.setOption === 'function') {
            try {
                editor.setOption('theme', theme);
            } catch (e) {
                console.warn('테마 변경 실패:', e);
            }
        }
    });
    
    // 테마 설정 저장
    localStorage.setItem('cp_agent_theme', theme);
}

/**
 * 모든 JSON 에디터 유효성 검사
 */
function validateAllJsonEditors() {
    debugLog('EDITOR', '모든 JSON 에디터 유효성 검사');
    
    const jsonEditors = [
        { name: 'answerInputEditor', editor: window.answerInputEditor },
        { name: 'metaEditor', editor: window.metaEditor },
        { name: 'tagsEditor', editor: window.tagsEditor },
        { name: 'answerEditor', editor: window.answerEditor },
        { name: 'metaEditorInstance_html', editor: window.metaEditorInstance_html },
        { name: 'tagsEditorInstance_html', editor: window.tagsEditorInstance_html }
    ];
    
    const results = [];
    
    jsonEditors.forEach(({ name, editor }) => {
        if (editor && typeof editor.getValue === 'function') {
            try {
                const value = editor.getValue().trim();
                if (value && value !== '{}') {
                    JSON.parse(value);
                }
                results.push({ name, valid: true, error: null });
            } catch (error) {
                results.push({ name, valid: false, error: error.message });
                console.warn(`${name} JSON 유효성 검사 실패:`, error);
            }
        } else {
            results.push({ name, valid: false, error: '에디터가 없음' });
        }
    });
    
    debugLog('EDITOR', 'JSON 유효성 검사 결과', results);
    return results;
}

/**
 * HTML탭 에디터 강제 재초기화
 */
function forceReinitializeHtmlTabEditors() {
    debugLog('EDITOR', 'HTML탭 에디터 강제 재초기화');
    
    try {
        // 기존 에디터 정리
        if (window.metaEditorInstance_html) {
            try {
                window.metaEditorInstance_html.toTextArea();
            } catch (e) {}
            window.metaEditorInstance_html = null;
        }
        
        if (window.tagsEditorInstance_html) {
            try {
                window.tagsEditorInstance_html.toTextArea();
            } catch (e) {}
            window.tagsEditorInstance_html = null;
        }
        
        // 컨테이너 초기화
        const metaContainer = document.getElementById('metaEditorContainer');
        const tagsContainer = document.getElementById('tagsEditorContainer');
        
        if (metaContainer) {
            metaContainer.innerHTML = '';
        }
        if (tagsContainer) {
            tagsContainer.innerHTML = '';
        }
        
        // 재초기화
        setTimeout(() => {
            initializeHtmlTabEditors();
            debugLog('EDITOR', 'HTML탭 에디터 재초기화 완료');
        }, 100);
        
        return true;
    } catch (error) {
        console.error('HTML탭 에디터 재초기화 실패:', error);
        return false;
    }
}

/**
 * 모든 에디터 리셋
 */
function resetAllEditors() {
    debugLog('EDITOR', '모든 에디터 리셋');
    
    try {
        if (window.answerInputEditor) window.answerInputEditor.setValue('{}');
        if (window.metaEditor) window.metaEditor.setValue('{}');
        if (window.tagsEditor) window.tagsEditor.setValue('{}');
        if (window.htmlEditorInstance) window.htmlEditorInstance.setValue('');
        if (window.answerEditor) window.answerEditor.setValue('{}');
        if (window.metaEditorInstance_html) {
            window.metaEditorInstance_html.setValue('{\n  "difficulty": "중",\n  "estimated_time": 300\n}');
        }
        if (window.tagsEditorInstance_html) {
            window.tagsEditorInstance_html.setValue('{\n  "competency": "수리능력",\n  "question_type": "multiple-choice"\n}');
        }
        
        debugLog('EDITOR', '모든 에디터 리셋 완료');
        return true;
    } catch (error) {
        console.error('에디터 리셋 실패:', error);
        return false;
    }
}

/* ========== 전역 에디터 네임스페이스 ========== */
window.CPAgent.Editor = {
    initialize: initializeAllEditors,
    refresh: refreshAllEditors,
    refreshAll: refreshAllEditors,
    resize: resizeAllEditors,
    changeTheme: changeEditorTheme,
    validateAllJson: validateAllJsonEditors,
    forceReinitializeHtmlTab: forceReinitializeHtmlTabEditors,
    resetAll: resetAllEditors,
    
    // 개별 초기화 함수들
    initializeAnswerInput: initializeAnswerInputEditor,
    initializeMeta: initializeMetaEditor,
    initializeTags: initializeTagsEditor,
    initializeHtml: initializeHtmlEditor,
    initializeAnswer: initializeAnswerEditor,
    initializeHtmlTab: initializeHtmlTabEditors
};