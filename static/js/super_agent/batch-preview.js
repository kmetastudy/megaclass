// static/js/super_agent/batch-preview.js
// 미리보기 및 편집기 관련 함수들

function initializePreview() {
    console.log('Preview 모듈 초기화');
    // 미리보기 관련 초기화는 여기에 추가
}

function loadSlidePreview(slideId, contentId) {
    // 미리보기 로딩 표시
    showLoadingPreview();
    
    // 실제 슬라이드 데이터 가져오기
    $.ajax({
        url: `/agent/api/slides/${slideId}/preview/`,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                currentSlideData = response.slide;
                displaySlidePreview(response.slide);
            } else {
                showErrorPreview('슬라이드를 불러올 수 없습니다.');
            }
        },
        error: function() {
            showErrorPreview('네트워크 오류가 발생했습니다.');
        }
    });
}

function showLoadingPreview() {
    $('#renderTab').html(`
        <div class="text-center py-8 text-gray-500">
            <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
            <p>미리보기를 로딩 중...</p>
        </div>
    `);
}

function showErrorPreview(message) {
    $('#renderTab').html(`
        <div class="text-center py-8 text-red-500">
            <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
            <p>${message}</p>
        </div>
    `);
}

function displaySlidePreview(slide) {
    // 렌더링 탭 업데이트
    const renderContent = slide.content && slide.content.page ? slide.content.page : '<p>콘텐츠가 없습니다.</p>';
    
    $('#renderTab').html(`
        <div class="slide-preview">
            <h4>${slide.title}</h4>
            <div class="slide-meta">
                <span class="type-badge">${slide.content_type || 'unknown'}</span>
                <span>차시: ${slide.chasi.title}</span>
                <span>예상시간: ${slide.estimated_time}분</span>
            </div>
            <div class="slide-content" id="slideContentArea">
                ${renderContent}
            </div>
        </div>
    `);
    
    // 원본 데이터 저장
    originalHtmlContent = renderContent;
    originalAnswerContent = slide.content && slide.content.answer ? 
        JSON.stringify(slide.content.answer, null, 2) : '{}';
    
    // 변경 추적 초기화
    changedElements.clear();
    
    // HTML 에디터 업데이트
    if (htmlEditor) {
        htmlEditor.setValue(renderContent);
    }
    
    // 정답 에디터 업데이트
    if (answerEditor) {
        answerEditor.setValue(originalAnswerContent);
    }
    
    // 편집 가능한 미리보기 업데이트
    $('#editablePreview').html(renderContent);
    
    // 기존 이미지에 컨트롤 추가 (고급 편집기 기능)
    setTimeout(() => {
        if (typeof addControlsToExistingImages === 'function') {
            addControlsToExistingImages();
        }
    }, 100);
    
    // 메타데이터 폼 업데이트
    if (slide.content) {
        $('#tagsInput').val(slide.content.tags || '');
        $('#difficultyInput').val(slide.content.difficulty || '');
        $('#estimatedTimeInput').val(slide.estimated_time || '');
        $('#instructionsInput').val(slide.content.instructions || '');
    }
}

function showDefaultPreview(itemType, itemText) {
    const typeIcons = {
        course: 'fas fa-book',
        chapter: 'fas fa-folder', 
        subchapter: 'fas fa-folder-open',
        chasi: 'fas fa-book-reader'
    };
    
    const typeNames = {
        course: '코스',
        chapter: '챕터',
        subchapter: '서브챕터', 
        chasi: '차시'
    };
    
    $('#renderTab').html(`
        <div class="preview-placeholder">
            <i class="${typeIcons[itemType] || 'fas fa-file'} text-3xl text-gray-400 mb-4"></i>
            <h4 class="text-lg font-semibold mb-2">${typeNames[itemType] || '항목'} 선택됨</h4>
            <p class="text-sm text-gray-600 mb-4">${itemText}</p>
            <p class="text-xs text-gray-500">문항을 클릭하면 상세 미리보기를 볼 수 있습니다</p>
        </div>
    `);
    
    // 에디터 초기화
    if (htmlEditor) htmlEditor.setValue('');
    if (answerEditor) answerEditor.setValue('{}');
    $('#editablePreview').html(`
        <div class="preview-placeholder">
            <i class="fas fa-edit"></i>
            <h4 class="text-lg font-semibold mb-2">편집할 문항을 선택해주세요</h4>
            <p class="text-sm">편집모드를 켜고 텍스트를 클릭하여 수정할 수 있습니다</p>
        </div>
    `);
    currentSlideData = null;
    originalHtmlContent = '';
    originalAnswerContent = '';
    changedElements.clear();
}

// 미리보기 탭 전환
function switchPreviewTab(tabName) {
    $('.preview-tab').removeClass('active');
    $('.preview-tab-content').removeClass('active');
    
    $(`.preview-tab[data-tab="${tabName}"]`).addClass('active');
    $(`#${tabName}Tab`).addClass('active');
    
    // 에디터 리프레시
    setTimeout(() => {
        if (tabName === 'html' && htmlEditor) {
            htmlEditor.refresh();
        } else if (tabName === 'html' && answerEditor) {
            answerEditor.refresh();
        }
    }, 100);
}

// 편집 모드 토글
function toggleEditMode() {
    isEditMode = !isEditMode;
    const btn = $('#editModeBtn');
    const editablePreview = $('#editablePreview');
    
    if (isEditMode) {
        btn.html('<i class="fas fa-eye"></i> 편집모드 끄기');
        btn.removeClass('btn-secondary').addClass('btn-primary');
        editablePreview.attr('contenteditable', 'true');
        
        // 고급 편집기 기능 활성화
        setTimeout(() => {
            if (typeof addControlsToExistingImages === 'function') {
                addControlsToExistingImages();
            }
        }, 100);
    } else {
        btn.html('<i class="fas fa-edit"></i> 편집모드 켜기');
        btn.removeClass('btn-primary').addClass('btn-secondary');
        editablePreview.removeAttr('contenteditable');
        
        if (typeof cancelInsertMode === 'function') {
            cancelInsertMode();
        }
    }
}

function updatePreviewFromHtml() {
    if (!htmlEditor) return;
    
    const htmlContent = htmlEditor.getValue();
    $('#slideContentArea').html(htmlContent);
    $('#editablePreview').html(htmlContent);
    
    if (isEditMode) {
        $('#editablePreview').attr('contenteditable', 'true');
        setTimeout(() => {
            if (typeof addControlsToExistingImages === 'function') {
                addControlsToExistingImages();
            }
        }, 100);
    }
}

function saveHtmlContent() {
    if (!currentSlideData || !htmlEditor) {
        alert('저장할 데이터가 없습니다.');
        return;
    }
    
    const newHtmlContent = htmlEditor.getValue();
    
    // 실제 저장 API 호출
    $.ajax({
        url: `/agent/api/contents/batch/${currentSlideData.content.id}/update/`,
        type: 'POST',
        data: JSON.stringify({
            page: newHtmlContent
        }),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function(response) {
            if (response.success) {
                // 저장 성공 시 하이라이트 표시
                highlightSavedContent('html');
                originalHtmlContent = newHtmlContent;
                changedElements.delete('html');
                
                // 미리보기 업데이트
                updatePreviewFromHtml();
                
                alert('HTML 콘텐츠가 성공적으로 저장되었습니다.');
            } else {
                alert('저장 중 오류가 발생했습니다: ' + (response.error || '알 수 없는 오류'));
            }
        },
        error: function() {
            alert('네트워크 오류가 발생했습니다.');
        }
    });
}

function validateAnswerJson() {
    if (!answerEditor) return;
    
    try {
        const json = answerEditor.getValue();
        JSON.parse(json);
        alert('JSON 형식이 올바릅니다.');
    } catch (e) {
        alert('JSON 형식이 올바르지 않습니다: ' + e.message);
    }
}

function saveAnswerData() {
    if (!currentSlideData || !answerEditor) {
        alert('저장할 데이터가 없습니다.');
        return;
    }
    
    try {
        const answerJson = answerEditor.getValue();
        const parsedAnswer = JSON.parse(answerJson); // 유효성 검사
        
        // 실제 저장 API 호출
        $.ajax({
            url: `/agent/api/contents/batch/${currentSlideData.content.id}/update/`,
            type: 'POST',
            data: JSON.stringify({
                answer: answerJson
            }),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': csrfToken
            },
            success: function(response) {
                if (response.success) {
                    // 저장 성공 시 하이라이트 표시
                    highlightSavedContent('answer');
                    originalAnswerContent = answerJson;
                    changedElements.delete('answer');
                    
                    alert('정답 데이터가 성공적으로 저장되었습니다.');
                } else {
                    alert('저장 중 오류가 발생했습니다: ' + (response.error || '알 수 없는 오류'));
                }
            },
            error: function() {
                alert('네트워크 오류가 발생했습니다.');
            }
        });
    } catch (e) {
        alert('JSON 형식이 올바르지 않습니다: ' + e.message);
    }
}

function highlightSavedContent(type) {
    let targetElement;
    
    if (type === 'html') {
        targetElement = $('.CodeMirror').first();
    } else if (type === 'answer') {
        targetElement = $('.CodeMirror').last();
    }
    
    if (targetElement.length > 0) {
        targetElement.addClass('save-highlight');
        setTimeout(() => {
            targetElement.removeClass('save-highlight');
        }, 3000);
    }
}

function toggleAccordion() {
    const content = $('#accordionContent');
    const icon = $('#accordionIcon');
    
    if (content.hasClass('show')) {
        content.removeClass('show').slideUp();
        icon.removeClass('rotated');
    } else {
        content.addClass('show').slideDown();
        icon.addClass('rotated');
    }
}

function saveMetadata() {
    if (!currentSlideData) {
        alert('저장할 데이터가 없습니다.');
        return;
    }
    
    const metadata = {
        tags: $('#tagsInput').val().split(',').map(tag => tag.trim()).filter(tag => tag),
        difficulty: $('#difficultyInput').val(),
        estimated_time: parseInt($('#estimatedTimeInput').val()) || 5,
        instructions: $('#instructionsInput').val()
    };
    
    // 실제 저장 API 호출
    $.ajax({
        url: `/agent/api/contents/batch/${currentSlideData.content.id}/update/`,
        type: 'POST',
        data: JSON.stringify({
            meta_data: metadata,
            tags: metadata.tags
        }),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function(response) {
            if (response.success) {
                alert('메타데이터가 성공적으로 저장되었습니다.');
            } else {
                alert('저장 중 오류가 발생했습니다: ' + (response.error || '알 수 없는 오류'));
            }
        },
        error: function() {
            alert('네트워크 오류가 발생했습니다.');
        }
    });
}

// 코드 포맷팅 함수들
function formatHtmlCode() {
    if (!htmlEditor) return;
    
    try {
        const currentCode = htmlEditor.getValue();
        const formattedCode = html_beautify(currentCode, {
            indent_size: 2,
            indent_char: ' ',
            max_preserve_newlines: 2,
            preserve_newlines: true,
            wrap_line_length: 0,
            indent_inner_html: true,
            wrap_attributes: 'auto',
            wrap_attributes_indent_size: 2,
            end_with_newline: false
        });
        
        htmlEditor.setValue(formattedCode);
        
        // 포맷팅 완료 시각 피드백
        const editorContainer = htmlEditor.getWrapperElement();
        editorContainer.style.transition = 'box-shadow 0.3s ease';
        editorContainer.style.boxShadow = '0 0 10px rgba(34, 197, 94, 0.3)';
        setTimeout(() => {
            editorContainer.style.boxShadow = '';
        }, 1000);
        
    } catch (error) {
        alert('HTML 코드 정렬 중 오류가 발생했습니다: ' + error.message);
    }
}

function formatAnswerCode() {
    if (!answerEditor) return;
    
    try {
        const currentCode = answerEditor.getValue();
        const parsed = JSON.parse(currentCode); // 유효성 검사
        const formattedCode = JSON.stringify(parsed, null, 2);
        
        answerEditor.setValue(formattedCode);
        
        // 포맷팅 완료 시각 피드백
        const editorContainer = answerEditor.getWrapperElement();
        editorContainer.style.transition = 'box-shadow 0.3s ease';
        editorContainer.style.boxShadow = '0 0 10px rgba(34, 197, 94, 0.3)';
        setTimeout(() => {
            editorContainer.style.boxShadow = '';
        }, 1000);
        
    } catch (error) {
        alert('JSON 코드 정렬 중 오류가 발생했습니다: ' + error.message);
    }
}

// 전역 함수로 노출
window.switchPreviewTab = switchPreviewTab;
window.toggleEditMode = toggleEditMode;
window.updatePreviewFromHtml = updatePreviewFromHtml;
window.saveHtmlContent = saveHtmlContent;
window.validateAnswerJson = validateAnswerJson;
window.saveAnswerData = saveAnswerData;
window.toggleAccordion = toggleAccordion;
window.saveMetadata = saveMetadata;
window.formatHtmlCode = formatHtmlCode;
window.formatAnswerCode = formatAnswerCode;