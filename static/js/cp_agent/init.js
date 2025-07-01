// static/js/cp_agent/init.js - 애플리케이션 초기화 (수정됨 - 자동복구 기능 제거)

/* ========== 초기화 설정 ========== */

/**
 * CP Agent 애플리케이션 초기화
 */
$(document).ready(function() {
    debugLog('INIT', 'CP Agent 초기화 시작...');
    
    try {
        const totalTimer = new window.PerformanceTimer('CP Agent 전체 초기화');
        
        // 단계별 초기화 실행
        initializeApplication()
            .then(() => {
                totalTimer.end();
                debugLog('INIT', 'CP Agent 초기화 완료!');
                
                // 초기화 완료 후 추가 작업
                postInitializationTasks();
            })
            .catch(error => {
                debugLog('INIT', 'CP Agent 초기화 실패', error);
                console.error('초기화 실패:', error);
                showToast('CP Agent 초기화 중 오류가 발생했습니다', 'error');
                
                // 오류 발생 시 기본 상태로 설정
                setFallbackState();
            });
            
    } catch (error) {
        debugLog('INIT', 'CP Agent 초기화 중 예외 발생', error);
        console.error('초기화 예외:', error);
        showToast('페이지 초기화 중 심각한 오류가 발생했습니다', 'error');
        setFallbackState();
    }
});

/**
 * 애플리케이션 초기화 메인 함수
 */
async function initializeApplication() {
    debugLog('INIT', '애플리케이션 초기화 시작');
    
    try {
        // 1. UI 초기화
        await initializeUI();
        
        // 2. 에디터 초기화 (가장 중요)
        await initializeEditors();
        
        // 3. 이벤트 바인딩
        await initializeEvents();
        
        // 4. 데이터 로드
        await initializeData();
        
        // 5. 설정 적용
        await applyInitialSettings();
        
        debugLog('INIT', '애플리케이션 초기화 완료');
        
    } catch (error) {
        debugLog('INIT', '애플리케이션 초기화 중 오류', error);
        throw error;
    }
}

/* ========== 단계별 초기화 함수들 ========== */

/**
 * 1. UI 초기화
 */
function initializeUI() {
    return new Promise((resolve, reject) => {
        try {
            debugLog('INIT', 'UI 초기화 시작');
            const timer = new window.PerformanceTimer('UI 초기화');
            
            // 탭 초기화
            if (window.CPAgent && CPAgent.UI) {
                CPAgent.UI.switchTab('contents');
                CPAgent.UI.switchPreviewTab('render');
            } else {
                // 기본 UI 초기화
                $('.tab-content').removeClass('active').hide();
                $('#contentsTab').addClass('active').show();
                $('.preview-tab-content').removeClass('active').hide();
                $('#renderTab').addClass('active').show();
            }
            
            // 초기 설정
            $('#contentChapter').prop('disabled', true);
            $('#templateFormType').prop('disabled', true);
            
            // UI 상태 설정
            if (window.CPAgent && CPAgent.UI) {
                CPAgent.UI.updateEditControls();
            }
            
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
 * 2. 에디터 초기화 (핵심)
 */
function initializeEditors() {
    return new Promise((resolve, reject) => {
        try {
            debugLog('INIT', '에디터 초기화 시작');
            const timer = new window.PerformanceTimer('에디터 초기화');
            
            // CPAgent.Editor가 있는지 확인
            if (window.CPAgent && CPAgent.Editor && typeof CPAgent.Editor.initialize === 'function') {
                debugLog('INIT', 'CPAgent.Editor.initialize 사용');
                const success = CPAgent.Editor.initialize();
                
                if (success) {
                    debugLog('INIT', '에디터 초기화 성공');
                } else {
                    debugLog('INIT', '에디터 초기화 실패, 개별 초기화 시도');
                    initializeEditorsIndividually();
                }
            } else {
                debugLog('INIT', 'CPAgent.Editor.initialize 없음, 개별 초기화');
                initializeEditorsIndividually();
            }
            
            // 에디터 리프레시 (비동기)
            setTimeout(() => {
                if (window.CPAgent && CPAgent.Editor && typeof CPAgent.Editor.refreshAll === 'function') {
                    CPAgent.Editor.refreshAll();
                } else {
                    // 수동으로 에디터 리프레시
                    refreshEditorsManually();
                }
                
                timer.end();
                debugLog('INIT', '에디터 초기화 완료');
                resolve();
            }, 200);
            
        } catch (error) {
            debugLog('INIT', '에디터 초기화 실패', error);
            
            // 에디터 초기화가 실패해도 계속 진행
            console.warn('에디터 초기화 실패, 계속 진행:', error);
            resolve();
        }
    });
}

/**
 * 개별 에디터 초기화
 */
function initializeEditorsIndividually() {
    debugLog('INIT', '개별 에디터 초기화 시작');
    
    try {
        // 각 에디터를 개별적으로 초기화
        const editorFunctions = [
            'initializeAnswerInputEditor',
            'initializeMetaEditor', 
            'initializeTagsEditor',
            'initializeHtmlEditor',
            'initializeAnswerEditor'
        ];
        
        editorFunctions.forEach(funcName => {
            try {
                if (typeof window[funcName] === 'function') {
                    window[funcName]();
                    debugLog('INIT', `${funcName} 성공`);
                } else if (window.CPAgent && CPAgent.Editor && typeof CPAgent.Editor[funcName] === 'function') {
                    CPAgent.Editor[funcName]();
                    debugLog('INIT', `CPAgent.Editor.${funcName} 성공`);
                } else {
                    console.warn(`${funcName} 함수를 찾을 수 없음`);
                }
            } catch (e) {
                console.warn(`${funcName} 실패:`, e);
            }
        });
        
        // HTML탭 에디터들 초기화 (지연)
        setTimeout(() => {
            try {
                if (typeof initializeHtmlTabEditors === 'function') {
                    initializeHtmlTabEditors();
                } else if (window.CPAgent && CPAgent.Editor && typeof CPAgent.Editor.initializeHtmlTab === 'function') {
                    CPAgent.Editor.initializeHtmlTab();
                }
                debugLog('INIT', 'HTML탭 에디터 초기화 완료');
            } catch (e) {
                console.warn('HTML탭 에디터 초기화 실패:', e);
            }
        }, 300);
        
    } catch (error) {
        console.error('개별 에디터 초기화 실패:', error);
    }
}

/**
 * 수동 에디터 리프레시
 */
function refreshEditorsManually() {
    debugLog('INIT', '수동 에디터 리프레시');
    
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
                debugLog('INIT', `에디터 ${index} 리프레시 완료`);
            } catch (e) {
                console.warn(`에디터 ${index} 리프레시 실패:`, e);
            }
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
            const timer = new window.PerformanceTimer('이벤트 바인딩');
            
            // 메인 이벤트 바인딩
            if (window.CPAgent && CPAgent.Events && typeof CPAgent.Events.bind === 'function') {
                CPAgent.Events.bind();
                if (typeof CPAgent.Events.bindDynamic === 'function') {
                    CPAgent.Events.bindDynamic();
                }
            } else {
                console.warn('CPAgent.Events 없음, 기본 이벤트만 바인딩');
                bindBasicEvents();
            }
            
            timer.end();
            debugLog('INIT', '이벤트 바인딩 완료');
            resolve();
            
        } catch (error) {
            debugLog('INIT', '이벤트 바인딩 실패', error);
            
            // 이벤트 바인딩 실패 시 기본 이벤트라도 바인딩
            try {
                bindBasicEvents();
                console.warn('기본 이벤트 바인딩으로 대체');
                resolve();
            } catch (e) {
                reject(error);
            }
        }
    });
}

/**
 * 기본 이벤트 바인딩 (CPAgent.Events가 없을 때 사용)
 */
function bindBasicEvents() {
    debugLog('INIT', '기본 이벤트 바인딩');
    
    // 검색 관련
    $('#contentCategory, #contentType, #contentCourse, #contentChapter').off('change.init').on('change.init', function() {
        if (window.CPAgent && CPAgent.Data && typeof CPAgent.Data.searchContents === 'function') {
            CPAgent.Data.searchContents();
        }
    });
    
    $('#contentSearch').off('keypress.init').on('keypress.init', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            if (window.CPAgent && CPAgent.Data && typeof CPAgent.Data.searchContents === 'function') {
                CPAgent.Data.searchContents();
            }
        }
    });
    
    // 템플릿 관련
    $('#templateCategory, #templateType').off('change.init').on('change.init', function() {
        if (window.CPAgent && CPAgent.Data && typeof CPAgent.Data.searchTemplates === 'function') {
            CPAgent.Data.searchTemplates();
        }
    });
    
    $('#templateSearch').off('keypress.init').on('keypress.init', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            if (window.CPAgent && CPAgent.Data && typeof CPAgent.Data.searchTemplates === 'function') {
                CPAgent.Data.searchTemplates();
            }
        }
    });
    
    // 폼 제출 방지
    $('#contentForm, #templateForm').off('submit.init').on('submit.init', function(e) {
        e.preventDefault();
    });
    
    debugLog('INIT', '기본 이벤트 바인딩 완료');
}

/**
 * 4. 데이터 로드
 */
function initializeData() {
    return new Promise((resolve, reject) => {
        try {
            debugLog('INIT', '데이터 로드 시작');
            const timer = new window.PerformanceTimer('데이터 로드');
            
            // 초기 데이터 로드 (비동기)
            if (window.CPAgent && CPAgent.Data && typeof CPAgent.Data.loadInitialData === 'function') {
                CPAgent.Data.loadInitialData();
            } else {
                console.warn('CPAgent.Data 없음, 기본 데이터 로드 시도');
                loadBasicData();
            }
            
            // 데이터 로드는 백그라운드에서 진행되므로 바로 resolve
            timer.end();
            debugLog('INIT', '데이터 로드 시작 완료');
            resolve();
            
        } catch (error) {
            debugLog('INIT', '데이터 로드 실패', error);
            // 데이터 로드 실패해도 계속 진행
            resolve();
        }
    });
}

/**
 * 기본 데이터 로드 (CPAgent.Data가 없을 때 사용)
 */
function loadBasicData() {
    debugLog('INIT', '기본 데이터 로드 시작');
    
    // 카테고리 로드
    $.get('/cp/api/categories/')
        .done(function(data) {
            const categorySelects = ['#contentCategory', '#templateCategory', '#templateFormCategory'];
            categorySelects.forEach(selector => {
                const $select = $(selector);
                $select.empty().append('<option value="">카테고리 선택</option>');
                data.forEach(category => {
                    $select.append(`<option value="${category.id}">${category.category_name}</option>`);
                });
            });
            debugLog('INIT', '카테고리 로드 완료');
        })
        .fail(function() {
            console.warn('카테고리 로드 실패');
        });
    
    // 컨텐츠 타입 로드
    $.get('/cp/api/content-types/')
        .done(function(data) {
            const typeSelects = ['#content_type', '#contentType', '#templateType', '#templateFormType'];
            typeSelects.forEach(selector => {
                const $select = $(selector);
                $select.empty();
                if (selector === '#content_type') {
                    $select.append('<option value="">선택하세요</option>');
                } else {
                    $select.append('<option value="">타입 선택</option>');
                }
                data.forEach(type => {
                    $select.append(`<option value="${type.id}">${type.type_name}</option>`);
                });
            });
            debugLog('INIT', '컨텐츠 타입 로드 완료');
        })
        .fail(function() {
            console.warn('컨텐츠 타입 로드 실패');
        });
}

/**
 * 5. 초기 설정 적용
 */
function applyInitialSettings() {
    return new Promise((resolve, reject) => {
        try {
            debugLog('INIT', '초기 설정 적용 시작');
            const timer = new window.PerformanceTimer('초기 설정 적용');
            
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
            // 설정 적용 실패해도 계속 진행
            resolve();
        }
    });
}

/* ========== 설정 적용 함수들 ========== */

/**
 * 테마 설정 적용
 */
function applyThemeSettings() {
    const savedTheme = localStorage.getItem('cp_agent_theme') || 'material';
    if (window.CPAgent && CPAgent.Editor && typeof CPAgent.Editor.changeTheme === 'function') {
        CPAgent.Editor.changeTheme(savedTheme);
    }
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
    
    if (userSettings.debugMode && window.CPAgent) {
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
 * 초기화 완료 후 추가 작업 (자동 복구 기능 제거됨)
 */
function postInitializationTasks() {
    debugLog('INIT', '초기화 완료 후 추가 작업 시작');
    
    try {
        // 디버깅 함수 등록
        registerDebugFunctions();
        
        // 상태 모니터링 시작 (자동 복구 없이 단순 모니터링만)
        startStatusMonitoring();
        
        // 자동 저장 기능 활성화 (설정에 따라)
        initializeAutoSave();
        
        // 키보드 단축키 도움말 표시 (첫 방문시)
        showKeyboardShortcutsIfFirstVisit();
        
        // 에디터 상태 최종 확인
        setTimeout(() => {
            if (typeof checkAllEditorsStatus === 'function') {
                checkAllEditorsStatus();
            }
        }, 2000);
        
        debugLog('INIT', '초기화 완료 후 추가 작업 완료');
        
    } catch (error) {
        console.error('초기화 완료 후 작업 중 오류:', error);
    }
}

/**
 * 디버깅 함수 등록
 */
function registerDebugFunctions() {
    try {
        // 전역 디버깅 함수들
        if (!window.CPAgent) {
            window.CPAgent = {};
        }
        
        window.CPAgent.debug = {
            checkEvents: function() {
                if (window.CPAgent && CPAgent.Events && typeof CPAgent.Events.checkBindings === 'function') {
                    CPAgent.Events.checkBindings();
                } else {
                    console.log('이벤트 체크 함수 없음');
                }
            },
            getStats: function() {
                return {
                    content: window.CPAgent.currentContent || null,
                    editing: window.CPAgent.TextEditing ? CPAgent.TextEditing.getEditingStats() : null,
                    images: window.CPAgent.Image ? CPAgent.Image.getImageStats() : null,
                    templates: window.templates ? window.templates.length : 0
                };
            },
            validateEditors: function() {
                if (window.CPAgent && CPAgent.Editor && typeof CPAgent.Editor.validateAllJson === 'function') {
                    return CPAgent.Editor.validateAllJson();
                } else {
                    console.log('에디터 검증 함수 없음');
                    return false;
                }
            },
            refreshAll: function() {
                if (window.CPAgent && CPAgent.Editor && typeof CPAgent.Editor.refreshAll === 'function') {
                    CPAgent.Editor.refreshAll();
                }
                if (window.CPAgent && CPAgent.Data) {
                    if (typeof CPAgent.Data.searchContents === 'function') {
                        CPAgent.Data.searchContents();
                    }
                    if (typeof CPAgent.Data.searchTemplates === 'function') {
                        CPAgent.Data.searchTemplates();
                    }
                }
            }
        };
        
        // 하위 호환성을 위한 전역 함수들
        if (typeof window.testEvents === 'undefined') {
            window.testEvents = window.CPAgent.debug.checkEvents;
        }
        if (typeof window.searchContents === 'undefined') {
            window.searchContents = function() {
                if (window.CPAgent && CPAgent.Data && typeof CPAgent.Data.searchContents === 'function') {
                    CPAgent.Data.searchContents();
                }
            };
        }
        if (typeof window.searchTemplates === 'undefined') {
            window.searchTemplates = function() {
                if (window.CPAgent && CPAgent.Data && typeof CPAgent.Data.searchTemplates === 'function') {
                    CPAgent.Data.searchTemplates();
                }
            };
        }
        
        debugLog('INIT', '디버깅 함수 등록 완료');
        
    } catch (error) {
        console.error('디버깅 함수 등록 실패:', error);
    }
}

/**
 * 상태 모니터링 시작 (자동 복구 없이 단순 모니터링만)
 */
function startStatusMonitoring() {
    try {
        // 10분마다 상태 체크 (자동 복구는 하지 않음)
        setInterval(() => {
            const stats = {
                memoryUsage: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) + 'MB' : 'N/A',
                temporaryUploads: window.temporaryUploads ? window.temporaryUploads.length : 0,
                wordMappings: window.wordMappings ? window.wordMappings.size : 0,
                activeEditors: [
                    window.answerInputEditor, 
                    window.metaEditor, 
                    window.tagsEditor, 
                    window.htmlEditorInstance, 
                    window.answerEditor
                ].filter(e => e).length
            };
            
            debugLog('MONITOR', '상태 체크', stats);
            
            // 메모리 사용량이 너무 높으면 경고만 표시
            if (performance.memory && performance.memory.usedJSHeapSize > 100 * 1024 * 1024) {
                debugLog('MONITOR', '높은 메모리 사용량 감지');
                console.warn('메모리 사용량이 높습니다:', stats.memoryUsage);
            }
            
        }, 10 * 60 * 1000); // 10분
        
        debugLog('INIT', '상태 모니터링 시작 (자동 복구 없음)');
        
    } catch (error) {
        console.error('상태 모니터링 시작 실패:', error);
    }
}

/**
 * 자동 저장 기능 초기화
 */
function initializeAutoSave() {
    try {
        const autoSaveEnabled = localStorage.getItem('cp_agent_auto_save') === 'true';
        
        if (autoSaveEnabled) {
            // 5분마다 자동 저장 (임시 저장)
            setInterval(() => {
                if (window.currentContent && window.htmlEditorInstance && window.htmlEditorInstance.getValue().trim()) {
                    const tempData = {
                        title: $('#title').val(),
                        content_type: $('#content_type').val(),
                        page: window.htmlEditorInstance.getValue(),
                        answer: window.answerEditor ? window.answerEditor.getValue() : '{}',
                        timestamp: new Date().toISOString()
                    };
                    
                    localStorage.setItem('cp_agent_temp_save', JSON.stringify(tempData));
                    debugLog('INIT', '임시 저장 완료');
                }
            }, 5 * 60 * 1000); // 5분
        }
        
    } catch (error) {
        console.error('자동 저장 초기화 실패:', error);
    }
}

/**
 * 첫 방문시 키보드 단축키 도움말 표시
 */
function showKeyboardShortcutsIfFirstVisit() {
    try {
        const hasVisited = localStorage.getItem('cp_agent_has_visited');
        
        if (!hasVisited) {
            setTimeout(() => {
                showToast('💡 Ctrl+S: 저장, Ctrl+Enter: AI 생성, Ctrl+Shift+D: 디버그 패널', 'success');
                localStorage.setItem('cp_agent_has_visited', 'true');
            }, 3000);
        }
        
    } catch (error) {
        console.error('단축키 도움말 표시 실패:', error);
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
        $('.tab-content').removeClass('active').hide();
        $('#contentsTab').addClass('active').show();
        $('.preview-tab-content').removeClass('active').hide();
        $('#renderTab').addClass('active').show();
        
        // 오류 메시지 표시
        $('#contentsList').html('<p class="text-red-500 text-center py-4">초기화 중 오류가 발생했습니다. 페이지를 새로고침 해주세요.</p>');
        
        // 기본 이벤트만 바인딩
        bindBasicEvents();
        
        // 응급 제어 패널 표시
        setTimeout(() => {
            $('#emergencyControls').removeClass('hidden');
        }, 1000);
        
    } catch (error) {
        debugLog('INIT', '기본 상태 설정 실패', error);
        console.error('기본 상태 설정 실패:', error);
    }
}

/**
 * 애플리케이션 재시작
 */
function restartApplication() {
    debugLog('INIT', '애플리케이션 재시작');
    
    try {
        // 모든 이벤트 제거
        if (window.CPAgent && CPAgent.Events && typeof CPAgent.Events.unbindAll === 'function') {
            CPAgent.Events.unbindAll();
        }
        
        // 변수 초기화
        window.currentContent = null;
        window.templates = [];
        window.temporaryUploads = [];
        if (window.wordMappings) {
            window.wordMappings.clear();
        }
        
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
        
    } catch (error) {
        console.error('재시작 실패:', error);
        showToast('재시작 실패', 'error');
    }
}

/**
 * 초기화 상태 확인
 */
function checkInitializationStatus() {
    const status = {
        cpAgent: !!window.CPAgent,
        editors: {
            answerInput: !!window.answerInputEditor,
            meta: !!window.metaEditor,
            tags: !!window.tagsEditor,
            html: !!window.htmlEditorInstance,
            answer: !!window.answerEditor
        },
        modules: {
            UI: !!(window.CPAgent && CPAgent.UI),
            Data: !!(window.CPAgent && CPAgent.Data),
            Content: !!(window.CPAgent && CPAgent.Content),
            Events: !!(window.CPAgent && CPAgent.Events),
            Editor: !!(window.CPAgent && CPAgent.Editor)
        }
    };
    
    console.log('초기화 상태 확인:', status);
    return status;
}

/* ========== 전역 초기화 네임스페이스 ========== */
if (!window.CPAgent) {
    window.CPAgent = {};
}

window.CPAgent.Init = {
    initialize: initializeApplication,
    restart: restartApplication,
    setFallbackState: setFallbackState,
    checkStatus: checkInitializationStatus
};