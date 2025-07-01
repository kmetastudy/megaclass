// static/js/cp_agent/data.js - 데이터 로드 및 검색 함수들

/* ========== 초기 데이터 로드 ========== */

/**
 * 초기 데이터 로드
 */
function loadInitialData() {
    debugLog('DATA', '초기 데이터 로드 시작');
    
    const timer = new PerformanceTimer('초기 데이터 로드');
    
    // 병렬로 데이터 로드
    Promise.all([
        loadCategories(),
        loadAllContentTypes(),
        loadCourses()
    ]).then(() => {
        // 초기 검색 실행
        searchContents();
        searchTemplates();
        
        timer.end();
        debugLog('DATA', '초기 데이터 로드 완료');
    }).catch(error => {
        debugLog('DATA', '초기 데이터 로드 실패', error);
        showToast('초기 데이터 로드 중 오류가 발생했습니다', 'error');
    });
}

/**
 * 카테고리 로드
 */
function loadCategories() {
    return new Promise((resolve, reject) => {
        $.get('/cp/api/categories/')
            .done(function(data) {
                debugLog('DATA', '카테고리 로드 완료', data);
                
                const categorySelects = [
                    '#contentCategory', 
                    '#templateCategory', 
                    '#templateFormCategory'
                ];
                
                categorySelects.forEach(selector => {
                    const $select = $(selector);
                    $select.empty().append('<option value="">카테고리 선택</option>');
                    data.forEach(category => {
                        $select.append(`<option value="${category.id}">${category.category_name}</option>`);
                    });
                });
                
                resolve(data);
            })
            .fail(function(xhr) {
                debugLog('DATA', '카테고리 로드 실패', xhr);
                showToast('카테고리를 불러오는데 실패했습니다', 'error');
                reject(xhr);
            });
    });
}

/**
 * 모든 컨텐츠 타입 로드
 */
function loadAllContentTypes() {
    return new Promise((resolve, reject) => {
        $.get('/cp/api/content-types/')
            .done(function(data) {
                debugLog('DATA', '컨텐츠 타입 로드 완료', data);
                
                const typeSelects = [
                    '#content_type', 
                    '#contentType', 
                    '#templateType', 
                    '#templateFormType'
                ];
                
                typeSelects.forEach(selector => {
                    const $select = $(selector);
                    const currentValue = $select.val();
                    
                    $select.empty();
                    
                    // 기본 옵션 추가
                    if (selector === '#content_type') {
                        $select.append('<option value="">선택하세요</option>');
                    } else {
                        $select.append('<option value="">타입 선택</option>');
                    }
                    
                    // 타입 옵션들 추가
                    data.forEach(type => {
                        $select.append(`<option value="${type.id}">${type.type_name}</option>`);
                    });
                    
                    // 이전 선택값 복원
                    if (currentValue) {
                        $select.val(currentValue);
                    }
                });
                
                resolve(data);
            })
            .fail(function(xhr) {
                debugLog('DATA', '컨텐츠 타입 로드 실패', xhr);
                showToast('컨텐츠 타입을 불러오는데 실패했습니다', 'error');
                reject(xhr);
            });
    });
}

/**
 * 카테고리별 컨텐츠 타입 로드
 */
function loadContentTypesByCategory(categoryId, targetSelectors = null) {
    debugLog('DATA', '카테고리별 컨텐츠 타입 로드', categoryId);
    
    if (!categoryId) {
        return loadAllContentTypes();
    }
    
    const defaultSelectors = ['#contentType', '#content_type'];
    const selectors = targetSelectors || defaultSelectors;
    
    return new Promise((resolve, reject) => {
        $.get(`/cp/api/content-types/?category=${categoryId}`)
            .done(function(data) {
                debugLog('DATA', '카테고리별 컨텐츠 타입 로드 완료', data);
                
                selectors.forEach(selector => {
                    const $select = $(selector);
                    const currentValue = $select.val();
                    
                    $select.empty();
                    
                    if (selector === '#content_type') {
                        $select.append('<option value="">선택하세요</option>');
                    } else {
                        $select.append('<option value="">타입 선택</option>');
                    }
                    
                    data.forEach(type => {
                        $select.append(`<option value="${type.id}">${type.type_name}</option>`);
                    });
                    
                    // 이전 선택값이 새 목록에 있으면 복원
                    if (currentValue && $select.find(`option[value="${currentValue}"]`).length > 0) {
                        $select.val(currentValue);
                    }
                });
                
                resolve(data);
            })
            .fail(function(xhr) {
                debugLog('DATA', '카테고리별 컨텐츠 타입 로드 실패', xhr);
                showToast('컨텐츠 타입을 불러오는데 실패했습니다', 'error');
                // 실패 시 전체 타입 로드
                loadAllContentTypes().then(resolve).catch(reject);
            });
    });
}

/**
 * 코스 로드
 */
function loadCourses() {
    return new Promise((resolve, reject) => {
        $.get('/cp/api/courses/')
            .done(function(data) {
                debugLog('DATA', '코스 로드 완료', data);
                
                const $select = $('#contentCourse');
                $select.empty().append('<option value="">코스 선택</option>');
                data.forEach(course => {
                    $select.append(`<option value="${course.id}">${course.subject_name}</option>`);
                });
                
                resolve(data);
            })
            .fail(function(xhr) {
                debugLog('DATA', '코스 로드 실패', xhr);
                showToast('코스를 불러오는데 실패했습니다', 'error');
                reject(xhr);
            });
    });
}

/**
 * 챕터 로드
 */
function loadChaptersByCourse(courseId) {
    return new Promise((resolve, reject) => {
        if (!courseId) {
            const $chapterSelect = $('#contentChapter');
            $chapterSelect.empty().append('<option value="">대단원 선택</option>');
            $chapterSelect.prop('disabled', true);
            resolve([]);
            return;
        }
        
        const $chapterSelect = $('#contentChapter');
        $chapterSelect.html('<option value="">로딩 중...</option>').prop('disabled', true);
        
        $.get(`/cp/api/courses/${courseId}/chapters/`)
            .done(function(data) {
                debugLog('DATA', '챕터 로드 완료', data);
                
                $chapterSelect.empty().append('<option value="">대단원 선택</option>');
                data.forEach(chapter => {
                    $chapterSelect.append(`<option value="${chapter.id}">${chapter.chapter_title}</option>`);
                });
                $chapterSelect.prop('disabled', false);
                
                resolve(data);
            })
            .fail(function(xhr) {
                debugLog('DATA', '챕터 로드 실패', xhr);
                $chapterSelect.html('<option value="">챕터 로드 실패</option>');
                showToast('챕터를 불러오는데 실패했습니다', 'error');
                reject(xhr);
            });
    });
}

/* ========== 검색 함수들 ========== */

/**
 * 컨텐츠 검색
 */
function searchContents() {
    debugLog('DATA', '컨텐츠 검색 시작');
    
    const params = {
        category: $('#contentCategory').val(),
        type: $('#contentType').val(),
        course: $('#contentCourse').val(),
        chapter: $('#contentChapter').val(),
        search: $('#contentSearch').val()
    };
    
    debugLog('DATA', '검색 파라미터', params);
    
    const $list = $('#contentsList');
    const $count = $('#contentsCount');
    
    // 로딩 상태 표시
    showLoadingState($list, '검색 중...');
    
    $.get('/cp/api/contents/search/', params)
        .done(function(data) {
            debugLog('DATA', '검색 결과', data);
            
            $list.empty();
            $count.text(data.length);
            
            if (data.length === 0) {
                showEmptyState($list, '검색 결과가 없습니다', 'fas fa-search');
                return;
            }
            
            // 결과를 순차적으로 애니메이션과 함께 표시
            data.forEach((content, index) => {
                setTimeout(() => {
                    const $item = CPAgent.UI.createContentListItem(content);
                    $list.append($item);
                }, index * 50); // 50ms 간격으로 순차 표시
            });
        })
        .fail(function(xhr) {
            debugLog('DATA', '컨텐츠 검색 실패', xhr);
            
            let errorMsg = '검색 중 오류가 발생했습니다.';
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    errorMsg = response.error;
                }
            } catch (e) {
                debugLog('DATA', '에러 응답 파싱 실패', e);
            }
            
            showErrorState($list, errorMsg);
            showToast(errorMsg, 'error');
            $count.text('0');
        });
}

/**
 * 템플릿 검색
 */
function searchTemplates() {
    debugLog('DATA', '템플릿 검색 시작');
    
    const params = {
        category: $('#templateCategory').val(),
        type: $('#templateType').val(),
        search: $('#templateSearch').val()
    };
    
    debugLog('DATA', '템플릿 검색 파라미터', params);
    
    const $list = $('#templatesList');
    const $select = $('#template_select');
    const $count = $('#templatesCount');
    
    // 로딩 상태 표시
    showLoadingState($list, '템플릿 검색 중...');
    
    $.get('/cp/api/templates/search/', params)
        .done(function(data) {
            debugLog('DATA', '템플릿 검색 결과', data);
            
            // 전역 변수에 저장
            templates = data;
            
            $list.empty();
            $select.empty().append('<option value="">템플릿 없음</option>');
            $count.text(data.length);
            
            if (data.length === 0) {
                showEmptyState($list, '검색 결과가 없습니다', 'fas fa-search');
                return;
            }
            
            // 결과를 순차적으로 표시
            data.forEach((template, index) => {
                setTimeout(() => {
                    // 리스트에 추가
                    const $item = CPAgent.UI.createTemplateListItem(template);
                    $list.append($item);
                    
                    // 선택 옵션에 추가
                    const categoryName = template.category_name || '카테고리 없음';
                    const typeName = template.content_type_name || '타입 없음';
                    $select.append(`<option value="${template.id}">${template.title} (${categoryName}-${typeName})</option>`);
                }, index * 50);
            });
        })
        .fail(function(xhr) {
            debugLog('DATA', '템플릿 검색 실패', xhr);
            
            let errorMsg = '템플릿 검색 중 오류가 발생했습니다.';
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    errorMsg = response.error;
                }
            } catch (e) {
                debugLog('DATA', '에러 응답 파싱 실패', e);
            }
            
            showErrorState($list, errorMsg);
            showToast(errorMsg, 'error');
            $count.text('0');
        });
}

/* ========== 전역 데이터 네임스페이스 ========== */
window.CPAgent.Data = {
    loadInitialData,
    loadCategories,
    loadAllContentTypes,
    loadContentTypesByCategory,
    loadCourses,
    loadChaptersByCourse,
    searchContents,
    searchTemplates
};