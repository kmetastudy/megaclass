// static/js/cp_agent/init.js - 애플리케이션 초기화

/* ========== 초기화 설정 ========== */

/**
 * CP Agent 애플리케이션 초기화
 */
$(document).ready(function() {
    debugLog('INIT', 'CP Agent 초기화 시작...');
    
    try {
        const totalTimer = new PerformanceTimer('CP Agent 전체 초기화');
        
        // 초기화 단계별 실행
        initializeApplication()
            .then(() => {
                totalTimer.end();
                debugLog('INIT', 'CP Agent 초기화 완료!');
                showToast('CP Agent가 성공적으로 초기화되었습니다', 'success');
                
                // 초기화 완료 후 추가 작업
                postInitializationTasks();
            })
            .catch(error => {
                debugLog('INIT', 'CP Agent 초기화 실패', error);
                showToast('CP Agent 초기화 중 오류가 발생했습니다', 'error');
                
                // 오류 발생 시 기본 상태로 설정
                setFallbackState();
            });
            
    } catch (error) {
        debugLog('INIT', 'CP Agent 초기화 중 예외 발생', error);
        showToast('페이지 초기화 중 심각한 오류가 발생했습니다', 'error');
        setFallbackState();
    }
});

/**
 * 애플리케이션 초기화 메인 함수
 */
async function initializeApplication() {
    debugLog('INIT', '애플리케이션 초기화 시작');
    
    // 1. UI 초기화
    await initializeUI();
    
    // 2. 에디터 초기화
    await initializeEditors();
    
    // 3. 이벤트 바인딩
    await initializeEvents();
    
    // 4. 데이터 로드
    await initializeData();
    
    // 5. 설정 적용
    await applyInitialSettings();
    
    debugLog('INIT', '애플리케이션 초기화 완료');
}

/* ========== 단계별 초기화 함수들 ========== */

/**
 * 1. UI 초기화
 */
function initializeUI() {
    return new Promise((resolve, reject) => {
        try {
            debugLog('INIT', 'UI 초기화 시작');
            const timer = new PerformanceTimer('UI 초기화');
            
            // 탭 초기화
            CPAgent.UI.switchTab('contents');
            CPAgent.UI.switchPreviewTab('render');
            
            // 초기 설정
            $('#contentChapter').prop('disabled', true);
            $('#templateFormType').prop('disabled', true);
            
            // UI 상태 설정
            CPAgent.UI.updateEditControls();
            
            timer.end();
            debugLog('INIT', 'UI 초기화 완료');
            resolve();
            
        } catch (error) {
            debugLog('INIT', 'UI 초기화 실패', error);
            reject(error);
        }
    });
}

/**
 * 2. 에디터 초기화
 */
function initializeEditors() {
    return new Promise((resolve, reject) => {
        try {
            debugLog('INIT', '에디터 초기화 시작');
            const timer = new PerformanceTimer('에디터 초기화');
            
            // 에디터 초기화 (동기 함수지만 Promise로 래핑)
            CPAgent.Editor.initialize();
            
            // 에디터 리프레시
            setTimeout(() => {
                CPAgent.Editor.refreshAll();
                timer.end();
                debugLog('INIT', '에디터 초기화 완료');
                resolve();
            }, 100);
            
        } catch (error) {
            debugLog('INIT', '에디터 초기화 실패', error);
            reject(error);
        }
    });
}

/**
 * 3. 이벤트 바인딩
 */
function initializeEvents() {
    return new Promise((resolve, reject) => {
        try {
            debugLog('INIT', '이벤트 바인딩 시작');
            const timer = new PerformanceTimer('이벤트 바인딩');
            
            // 메인 이벤트 바인딩
            CPAgent.Events.bind();
            
            // 동적 이벤트 바인딩
            CPAgent.Events.bindDynamic();
            
            timer.end();
            debugLog('INIT', '이벤트 바인딩 완료');
            resolve();
            
        } catch (error) {
            debugLog('INIT', '이벤트 바인딩 실패', error);
            reject(error);
        }
    });
}

/**
 * 4. 데이터 로드
 */
function initializeData() {
    return new Promise((resolve, reject) => {
        try {
            debugLog('INIT', '데이터 로드 시작');
            const timer = new PerformanceTimer('데이터 로드');
            
            // 초기 데이터 로드 (비동기)
            CPAgent.Data.loadInitialData();
            
            // 데이터 로드는 백그라운드에서 진행되므로 바로 resolve
            timer.end();
            debugLog('INIT', '데이터 로드 시작 완료');
            resolve();
            
        } catch (error) {
            debugLog('INIT', '데이터 로드 실패', error);
            reject(error);
        }
    });
}

/**
 * 5. 초기 설정 적용
 */
function applyInitialSettings() {
    return new Promise((resolve, reject) => {
        try {
            debugLog('INIT', '초기 설정 적용 시작');
            const timer = new PerformanceTimer('초기 설정 적용');
            
            // 테마 설정
            applyThemeSettings();
            
            // 언어 설정
            applyLanguageSettings();
            
            // 사용자 설정
            applyUserSettings();
            
            // 성능 설정
            applyPerformanceSettings();
            
            timer.end();
            debugLog('INIT', '초기 설정 적용 완료');
            resolve();
            
        } catch (error) {
            debugLog('INIT', '초기 설정 적용 실패', error);
            reject(error);
        }
    });
}

/* ========== 설정 적용 함수들 ========== */

/**
 * 테마 설정 적용
 */
function applyThemeSettings() {
    const savedTheme = localStorage.getItem('cp_agent_theme') || 'material';
    CPAgent.Editor.changeTheme(savedTheme);
    debugLog('INIT', '테마 설정 적용', savedTheme);
}

/**
 * 언어 설정 적용
 */
function applyLanguageSettings() {
    const savedLanguage = localStorage.getItem('cp_agent_language') || 'ko';
    // 향후 다국어 지원 시 구현
    debugLog('INIT', '언어 설정 적용', savedLanguage);
}

/**
 * 사용자 설정 적용
 */
function applyUserSettings() {
    // 사용자별 설정 적용
    const userSettings = {
        autoSave: localStorage.getItem('cp_agent_auto_save') === 'true',
        showHints: localStorage.getItem('cp_agent_show_hints') !== 'false',
        debugMode: localStorage.getItem('cp_agent_debug_mode') === 'true'
    };
    
    debugLog('INIT', '사용자 설정 적용', userSettings);
    
    // 설정에 따른 UI 조정
    if (!userSettings.showHints) {
        $('.edit-help').hide();
    }
    
    if (userSettings.debugMode) {
        window.CPAgent.debugMode = true;
    }
}

/**
 * 성능 설정 적용
 */
function applyPerformanceSettings() {
    // 성능 관련 설정
    const performanceSettings = {
        enableAnimations: localStorage.getItem('cp_agent_animations') !== 'false',
        debounceTime: parseInt(localStorage.getItem('cp_agent_debounce_time')) || 500
    };
    
    debugLog('INIT', '성능 설정 적용', performanceSettings);
    
    if (!performanceSettings.enableAnimations) {
        $('*').css('transition', 'none');
        $('*').css('animation', 'none');
    }
}

/* ========== 초기화 완료 후 작업 ========== */

/**
 * 초기화 완료 후 추가 작업
 */
function postInitializationTasks() {
    debugLog('INIT', '초기화 완료 후 추가 작업 시작');
    
    // 디버깅 함수 등록
    registerDebugFunctions();
    
    // 상태 모니터링 시작
    startStatusMonitoring();
    
    // 자동 저장 기능 활성화 (설정에 따라)
    initializeAutoSave();
    
    // 키보드 단축키 도움말 표시 (첫 방문시)
    showKeyboardShortcutsIfFirstVisit();
    
    debugLog('INIT', '초기화 완료 후 추가 작업 완료');
}

/**
 * 디버깅 함수 등록
 */
function registerDebugFunctions() {
    // 전역 디버깅 함수들
    window.CPAgent.debug = {
        checkEvents: CPAgent.Events.checkBindings,
        getStats: function() {
            return {
                content: CPAgent.Content,
                editing: CPAgent.TextEditing.getEditingStats(),
                images: CPAgent.Image.getImageStats(),
                templates: templates.length
            };
        },
        validateEditors: CPAgent.Editor.validateAllJson,
        refreshAll: function() {
            CPAgent.Editor.refreshAll();
            CPAgent.Data.searchContents();
            CPAgent.Data.searchTemplates();
        }
    };
    
    // 하위 호환성을 위한 전역 함수들
    window.testEvents = CPAgent.Events.checkBindings;
    window.searchContents = CPAgent.Data.searchContents;
    window.searchTemplates = CPAgent.Data.searchTemplates;
    
    debugLog('INIT', '디버깅 함수 등록 완료');
}

/**
 * 상태 모니터링 시작
 */
function startStatusMonitoring() {
    // 5분마다 상태 체크
    setInterval(() => {
        const stats = {
            memoryUsage: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) + 'MB' : 'N/A',
            temporaryUploads: temporaryUploads.length,
            wordMappings: wordMappings.size,
            activeEditors: [answerInputEditor, metaEditor, tagsEditor, htmlEditorInstance, answerEditor].filter(e => e).length
        };
        
        debugLog('MONITOR', '상태 체크', stats);
        
        // 메모리 사용량이 너무 높으면 경고
        if (performance.memory && performance.memory.usedJSHeapSize > 100 * 1024 * 1024) {
            debugLog('MONITOR', '높은 메모리 사용량 감지');
        }
        
    }, 5 * 60 * 1000); // 5분
}

/**
 * 자동 저장 기능 초기화
 */
function initializeAutoSave() {
    const autoSaveEnabled = localStorage.getItem('cp_agent_auto_save') === 'true';
    
    if (autoSaveEnabled) {
        // 5분마다 자동 저장 (임시 저장)
        setInterval(() => {
            if (currentContent && htmlEditorInstance.getValue().trim()) {
                const tempData = {
                    title: $('#title').val(),
                    content_type: $('#content_type').val(),
                    page: htmlEditorInstance.getValue(),
                    answer: answerEditor.getValue(),
                    timestamp: new Date().toISOString()
                };
                
                localStorage.setItem('cp_agent_temp_save', JSON.stringify(tempData));
                debugLog('INIT', '임시 저장 완료');
            }
        }, 5 * 60 * 1000); // 5분
    }
}

/**
 * 첫 방문시 키보드 단축키 도움말 표시
 */
function showKeyboardShortcutsIfFirstVisit() {
    const hasVisited = localStorage.getItem('cp_agent_has_visited');
    
    if (!hasVisited) {
        setTimeout(() => {
            showToast('💡 Ctrl+S: 저장, Ctrl+Enter: AI 생성, F1: 도움말', 'success');
            localStorage.setItem('cp_agent_has_visited', 'true');
        }, 2000);
    }
}

/* ========== 오류 처리 및 복구 ========== */

/**
 * 오류 발생 시 기본 상태 설정
 */
function setFallbackState() {
    debugLog('INIT', '기본 상태 설정');
    
    try {
        // 기본 UI 설정
        $('.tab-content').hide();
        $('#contentsTab').show();
        $('.preview-tab-content').hide();
        $('#renderTab').show();
        
        // 오류 메시지 표시
        $('#contentsList').html('<p class="text-red-500 text-center py-4">초기화 중 오류가 발생했습니다. 페이지를 새로고침 해주세요.</p>');
        
        // 기본 이벤트만 바인딩
        $(document).on('click', '[onclick]', function(e) {
            try {
                eval($(this).attr('onclick'));
            } catch (error) {
                debugLog('INIT', '이벤트 실행 오류', error);
            }
        });
        
    } catch (error) {
        debugLog('INIT', '기본 상태 설정 실패', error);
    }
}

/**
 * 애플리케이션 재시작
 */
function restartApplication() {
    debugLog('INIT', '애플리케이션 재시작');
    
    // 모든 이벤트 제거
    CPAgent.Events.unbindAll();
    
    // 변수 초기화
    currentContent = null;
    templates = [];
    temporaryUploads = [];
    wordMappings.clear();
    
    // 재초기화
    setTimeout(() => {
        initializeApplication()
            .then(() => {
                showToast('애플리케이션이 재시작되었습니다', 'success');
            })
            .catch(error => {
                debugLog('INIT', '재시작 실패', error);
                showToast('재시작 중 오류가 발생했습니다', 'error');
            });
    }, 1000);
}

/* ========== 전역 초기화 네임스페이스 ========== */
window.CPAgent.Init = {
    initialize: initializeApplication,
    restart: restartApplication,
    setFallbackState: setFallbackState
};