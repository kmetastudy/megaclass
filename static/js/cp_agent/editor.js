// static/js/cp_agent/editor.js - 에디터 초기화 및 관리 (수정됨 - HTML탭 단순화)

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
        
        // HTML탭 에디터들은 지연 초기화 (단순화됨)
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
 * HTML탭 에디터들 초기화 (단순화된 버전)
 */
function initializeHtmlTabEditors() {
    debugLog('EDITOR', 'HTML탭 에디터 초기화 시작 (단순화된 버전)');
    
    try {
        let successCount = 0;
        
        // 메타데이터 에디터 (HTML탭) - 단순화됨
        const metaContainer = document.getElementById('metaEditorContainer');
        if (metaContainer && !window.metaEditorInstance_html) {
            try {
                metaContainer.innerHTML = ''; // 컨테이너 초기화
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
                successCount++;
            } catch (e) {
                console.error('HTML탭 메타데이터 에디터 초기화 실패:', e);
            }
        } else if (window.metaEditorInstance_html) {
            debugLog('EDITOR', 'metaEditorInstance_html 이미 존재함');
            successCount++;
        } else {
            console.warn('metaEditorContainer DOM 요소를 찾을 수 없음');
        }
        
        // 태그 에디터 (HTML탭) - 단순화됨
        const tagsContainer = document.getElementById('tagsEditorContainer');
        if (tagsContainer && !window.tagsEditorInstance_html) {
            try {
                tagsContainer.innerHTML = ''; // 컨테이너 초기화
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
                successCount++;
            } catch (e) {
                console.error('HTML탭 태그 에디터 초기화 실패:', e);
            }
        } else if (window.tagsEditorInstance_html) {
            debugLog('EDITOR', 'tagsEditorInstance_html 이미 존재함');
            successCount++;
        } else {
            console.warn('tagsEditorContainer DOM 요소를 찾을 수 없음');
        }
        
        debugLog('EDITOR', `HTML탭 에디터 초기화 완료: ${successCount}/2개 성공`);
        return successCount === 2;
        
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
        { name: 'answerInputEditor', editor: window.answerInputEditor },
        { name: 'metaEditor', editor: window.metaEditor },
        { name: 'tagsEditor', editor: window.tagsEditor },
        { name: 'htmlEditorInstance', editor: window.htmlEditorInstance },
        { name: 'answerEditor', editor: window.answerEditor },
        { name: 'metaEditorInstance_html', editor: window.metaEditorInstance_html },
        { name: 'tagsEditorInstance_html', editor: window.tagsEditorInstance_html }
    ];
    
    let refreshedCount = 0;
    
    editors.forEach(({ name, editor }) => {
        if (editor && typeof editor.refresh === 'function') {
            try {
                editor.refresh();
                debugLog('EDITOR', `${name} 새로고침 완료`);
                refreshedCount++;
            } catch (e) {
                console.warn(`${name} 새로고침 실패:`, e);
            }
        } else {
            console.warn(`${name} 에디터가 없거나 refresh 함수가 없음`);
        }
    });
    
    debugLog('EDITOR', `총 ${refreshedCount}개 에디터 새로고침 완료`);
    return refreshedCount;
}

/**
 * 에디터 크기 조정
 */
function resizeAllEditors() {
    debugLog('EDITOR', '모든 에디터 크기 조정');
    
    const editors = [
        { name: 'answerInputEditor', editor: window.answerInputEditor, height: 150 },
        { name: 'metaEditor', editor: window.metaEditor, height: 150 },
        { name: 'tagsEditor', editor: window.tagsEditor, height: 150 },
        { name: 'htmlEditorInstance', editor: window.htmlEditorInstance, height: '100%' },
        { name: 'answerEditor', editor: window.answerEditor, height: '100%' },
        { name: 'metaEditorInstance_html', editor: window.metaEditorInstance_html, height: '100%' },
        { name: 'tagsEditorInstance_html', editor: window.tagsEditorInstance_html, height: '100%' }
    ];
    
    let resizedCount = 0;
    
    editors.forEach(({ name, editor, height }) => {
        if (editor && typeof editor.setSize === 'function') {
            try {
                editor.setSize(null, height);
                resizedCount++;
            } catch (e) {
                console.warn(`${name} 크기 조정 실패:`, e);
            }
        }
    });
    
    debugLog('EDITOR', `총 ${resizedCount}개 에디터 크기 조정 완료`);
    return resizedCount;
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
    
    let changedCount = 0;
    
    editors.forEach((editor, index) => {
        if (editor && typeof editor.setOption === 'function') {
            try {
                editor.setOption('theme', theme);
                changedCount++;
            } catch (e) {
                console.warn(`에디터 ${index} 테마 변경 실패:`, e);
            }
        }
    });
    
    // 테마 설정 저장
    localStorage.setItem('cp_agent_theme', theme);
    debugLog('EDITOR', `총 ${changedCount}개 에디터 테마 변경 완료`);
    
    return changedCount;
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
 * HTML탭 에디터 강제 재초기화 (단순화됨)
 */
function forceReinitializeHtmlTabEditors() {
    debugLog('EDITOR', 'HTML탭 에디터 강제 재초기화 (단순화됨)');
    
    try {
        // 기존 에디터 정리
        if (window.metaEditorInstance_html) {
            try {
                window.metaEditorInstance_html.toTextArea();
            } catch (e) {
                console.warn('metaEditorInstance_html 정리 실패:', e);
            }
            window.metaEditorInstance_html = null;
        }
        
        if (window.tagsEditorInstance_html) {
            try {
                window.tagsEditorInstance_html.toTextArea();
            } catch (e) {
                console.warn('tagsEditorInstance_html 정리 실패:', e);
            }
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
            const success = initializeHtmlTabEditors();
            if (success) {
                debugLog('EDITOR', 'HTML탭 에디터 재초기화 완료');
                showToast('HTML탭 에디터가 재초기화되었습니다', 'success');
            } else {
                console.error('HTML탭 에디터 재초기화 부분적 실패');
                showToast('HTML탭 에디터 재초기화 중 일부 오류 발생', 'warning');
            }
        }, 100);
        
        return true;
    } catch (error) {
        console.error('HTML탭 에디터 재초기화 실패:', error);
        showToast('HTML탭 에디터 재초기화 실패', 'error');
        return false;
    }
}

/**
 * 모든 에디터 리셋
 */
function resetAllEditors() {
    debugLog('EDITOR', '모든 에디터 리셋');
    
    try {
        const resetValues = {
            answerInputEditor: '{}',
            metaEditor: '{}',
            tagsEditor: '{}',
            htmlEditorInstance: '',
            answerEditor: '{}',
            metaEditorInstance_html: '{\n  "difficulty": "중",\n  "estimated_time": 300,\n  "subject": "",\n  "chapter": ""\n}',
            tagsEditorInstance_html: '{\n  "competency": "수리능력",\n  "sub_competency": "도표분석능력",\n  "difficulty": "중",\n  "question_type": "multiple-choice",\n  "order": 1\n}'
        };
        
        let resetCount = 0;
        
        Object.keys(resetValues).forEach(editorName => {
            const editor = window[editorName];
            const value = resetValues[editorName];
            
            if (editor && typeof editor.setValue === 'function') {
                try {
                    editor.setValue(value);
                    resetCount++;
                    debugLog('EDITOR', `${editorName} 리셋 완료`);
                } catch (e) {
                    console.warn(`${editorName} 리셋 실패:`, e);
                }
            }
        });
        
        debugLog('EDITOR', `총 ${resetCount}개 에디터 리셋 완료`);
        return resetCount === Object.keys(resetValues).length;
        
    } catch (error) {
        console.error('에디터 리셋 실패:', error);
        return false;
    }
}

/**
 * 에디터 상태 확인
 */
function checkEditorStatus() {
    const editors = {
        'answerInputEditor': window.answerInputEditor,
        'metaEditor': window.metaEditor,
        'tagsEditor': window.tagsEditor,
        'htmlEditorInstance': window.htmlEditorInstance,
        'answerEditor': window.answerEditor,
        'metaEditorInstance_html': window.metaEditorInstance_html,
        'tagsEditorInstance_html': window.tagsEditorInstance_html
    };
    
    const status = {};
    
    Object.keys(editors).forEach(name => {
        const editor = editors[name];
        status[name] = {
            exists: !!editor,
            hasSetValue: editor && typeof editor.setValue === 'function',
            hasGetValue: editor && typeof editor.getValue === 'function',
            hasRefresh: editor && typeof editor.refresh === 'function',
            isCodeMirror: editor && editor.constructor && editor.constructor.name === 'CodeMirror'
        };
        
        if (editor && editor.getValue) {
            try {
                const content = editor.getValue();
                status[name].contentLength = content.length;
                status[name].isEmpty = content.trim() === '' || content.trim() === '{}';
            } catch (e) {
                status[name].error = e.message;
            }
        }
    });
    
    console.log('에디터 상태 확인:', status);
    return status;
}

/* ========== 전역 에디터 네임스페이스 ========== */
window.CPAgent.Editor = {
    // 메인 함수들
    initialize: initializeAllEditors,
    refresh: refreshAllEditors,
    refreshAll: refreshAllEditors,
    resize: resizeAllEditors,
    changeTheme: changeEditorTheme,
    validateAllJson: validateAllJsonEditors,
    forceReinitializeHtmlTab: forceReinitializeHtmlTabEditors,
    resetAll: resetAllEditors,
    checkStatus: checkEditorStatus,
    
    // 개별 초기화 함수들
    initializeAnswerInput: initializeAnswerInputEditor,
    initializeMeta: initializeMetaEditor,
    initializeTags: initializeTagsEditor,
    initializeHtml: initializeHtmlEditor,
    initializeAnswer: initializeAnswerEditor,
    initializeHtmlTab: initializeHtmlTabEditors
};

// 전역 함수로도 노출 (하위 호환성)
window.initializeHtmlTabEditors = initializeHtmlTabEditors;
window.checkAllEditorsStatus = checkEditorStatus;