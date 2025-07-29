// static/js/super_agent/batch-advanced-editor.js
// 고급 편집기 관련 함수들 (이미지, 테이블, SVG)

function initializeAdvancedEditor() {
    console.log('Advanced Editor 모듈 초기화');
    
    // 고급 편집기 툴바 이벤트
    $('#insertImageBlock').on('click', () => toggleInsertMode('image-block'));
    $('#insertImageInline').on('click', () => toggleInsertMode('image-inline'));
    $('#insertTable').on('click', insertTable);
    $('#insertSVG').on('click', insertSVG);
    $('#clearFormat').on('click', clearFormat);
    $('#undoBtn').on('click', () => document.execCommand('undo'));
    $('#redoBtn').on('click', () => document.execCommand('redo'));
    $('#saveAdvancedContent').on('click', saveAdvancedContent);
    
    // 편집 영역 고급 이벤트
    $('#editablePreview').on('click', handleAdvancedEditorClick);
    $('#editablePreview').on('mousedown', handleAdvancedMouseDown);
    $('#editablePreview').on('mousemove', handleAdvancedMouseMove);
    $('#editablePreview').on('mouseup', handleAdvancedMouseUp);
    
    // ESC 키로 삽입 모드 취소
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape' && isInsertMode) {
            cancelInsertMode();
        }
    });
}

// 삽입 모드 관리
function toggleInsertMode(type) {
    if (isInsertMode && insertType === type) {
        cancelInsertMode();
    } else {
        activateInsertMode(type);
    }
}

function activateInsertMode(type) {
    cancelInsertMode(); // 기존 모드 취소
    
    isInsertMode = true;
    insertType = type;
    
    $('#editablePreview').addClass('insert-mode');
    
    // 해당 버튼 활성화
    const buttonId = type === 'image-block' ? '#insertImageBlock' : '#insertImageInline';
    $(buttonId).addClass('active');
    
    showAdvancedStatusMessage('클릭하여 이미지를 삽입하세요. ESC로 취소할 수 있습니다.', 'success');
}

function cancelInsertMode() {
    isInsertMode = false;
    insertType = '';
    
    $('#editablePreview').removeClass('insert-mode');
    $('.toolbar-btn.active').removeClass('active');
    
    // 크기 조절 박스 제거
    if (resizeBox) {
        $(resizeBox).remove();
        resizeBox = null;
    }
}

// 편집기 클릭 처리
function handleAdvancedEditorClick(e) {
    if (isInsertMode && insertType.startsWith('image-')) {
        e.preventDefault();
        e.stopPropagation();
        
        const isBlock = insertType === 'image-block';
        insertImagePlaceholder(e, isBlock);
        
        cancelInsertMode();
    }
}

function insertImagePlaceholder(e, isBlock) {
    const placeholder = $(`
        <div class="image-placeholder ${isBlock ? 'block' : 'inline'}">
            <i class="fas fa-image" style="font-size: 24px; display: block; margin-bottom: 8px;"></i>
            <div>클릭하여 이미지 선택</div>
        </div>
    `);
    
    if (isBlock) {
        // 블록 이미지: 클릭한 위치에 가장 가까운 블록 요소 다음에 삽입
        const target = $(e.target).closest('div, p, h1, h2, h3, h4, h5, h6');
        if (target.length > 0) {
            target.after(placeholder);
        } else {
            $('#editablePreview').append(placeholder);
        }
    } else {
        // 인라인 이미지: 클릭한 위치에 삽입
        const range = document.caretRangeFromPoint(e.clientX, e.clientY);
        if (range) {
            range.insertNode(placeholder[0]);
        } else {
            $('#editablePreview').append(placeholder);
        }
    }
    
    // 플레이스홀더 클릭 이벤트
    placeholder.on('click', function(e) {
        e.preventDefault();
        currentImagePlaceholder = this;
        $('#imageUpload').click();
    });
}

// 이미지 업로드
function uploadAdvancedImage(file, placeholder) {
    // 파일 유효성 검사
    if (!file.type.startsWith('image/')) {
        showAdvancedStatusMessage('이미지 파일만 선택할 수 있습니다.', 'error');
        return;
    }
    
    if (file.size > 5 * 1024 * 1024) { // 5MB 제한
        showAdvancedStatusMessage('파일 크기는 5MB를 초과할 수 없습니다.', 'error');
        return;
    }
    
    // 로딩 상태 표시
    $(placeholder).html(`
        <div class="loading-spinner"></div>
        <div style="margin-top: 8px;">업로드 중...</div>
    `);
    
    // 파일 업로드
    const formData = new FormData();
    formData.append('file', file);
    
    $.ajax({
        url: "/agent/api/files/upload/temporary/",
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function(response) {
            if (response.success) {
                uploadedAttachments.add(response.attachment_id);
                replaceWithAdvancedImage(placeholder, response.file_url, response.attachment_id);
                showAdvancedStatusMessage('이미지가 성공적으로 업로드되었습니다.', 'success');
            } else {
                showAdvancedStatusMessage(response.error || '업로드에 실패했습니다.', 'error');
                $(placeholder).remove();
            }
        },
        error: function() {
            showAdvancedStatusMessage('네트워크 오류가 발생했습니다.', 'error');
            $(placeholder).remove();
        }
    });
}

function replaceWithAdvancedImage(placeholder, imageUrl, attachmentId) {
    const isBlock = $(placeholder).hasClass('block');
    
    const imageContainer = $(`
        <div class="image-container ${isBlock ? 'block' : 'inline'}" data-attachment-id="${attachmentId}">
            <img src="${imageUrl}" alt="Uploaded image" style="${isBlock ? '' : 'width: 120px; height: auto;'}">
            <div class="image-controls">
                <button class="image-control-btn edit" onclick="editAdvancedImage(this)" title="이미지 교체">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="image-control-btn delete" onclick="deleteAdvancedImage(this)" title="이미지 삭제">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `);
    
    $(placeholder).replaceWith(imageContainer);
    currentImagePlaceholder = null;
}

// 기존 이미지에 컨트롤 추가
function addControlsToExistingImages() {
    $('#editablePreview img').each(function() {
        if (!$(this).parent().hasClass('image-container')) {
            wrapImageWithContainer(this);
        }
    });
}

function wrapImageWithContainer(img) {
    const $img = $(img);
    const isBlock = $img.css('display') === 'block' || 
                   $img.parent().is('div') ||
                   $img.css('width') === '100%';
    
    const container = $(`
        <div class="image-container ${isBlock ? 'block' : 'inline'}">
            <div class="image-controls">
                <button class="image-control-btn edit" onclick="editAdvancedImage(this)" title="이미지 교체">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="image-control-btn delete" onclick="deleteAdvancedImage(this)" title="이미지 삭제">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `);
    
    $img.wrap(container);
}

// 이미지 편집/삭제 함수들
window.editAdvancedImage = function(button) {
    const container = $(button).closest('.image-container')[0];
    currentImagePlaceholder = container;
    $('#imageUpload').click();
};

window.deleteAdvancedImage = function(button) {
    if (!confirm('이미지를 삭제하시겠습니까?')) return;
    
    const container = $(button).closest('.image-container');
    const attachmentId = container.data('attachment-id');
    
    if (attachmentId) {
        // 서버에서 파일 삭제
        $.ajax({
            url: "/agent/api/files/delete/temporary/",
            type: 'POST',
            data: JSON.stringify({ attachment_id: attachmentId }),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': csrfToken
            },
            success: function(response) {
                if (response.success) {
                    uploadedAttachments.delete(parseInt(attachmentId));
                    showAdvancedStatusMessage('이미지가 삭제되었습니다.', 'success');
                }
            },
            error: function() {
                console.error('Delete error');
            }
        });
    }
    
    container.remove();
};

// 마우스 이벤트 처리 (크기 조절)
function handleAdvancedMouseDown(e) {
    if (isInsertMode && insertType.startsWith('image-')) {
        e.preventDefault();
        isResizing = true;
        resizeStartX = e.clientX;
        resizeStartY = e.clientY;
        
        createResizeBox(e.clientX, e.clientY);
    }
}

function handleAdvancedMouseMove(e) {
    if (isResizing && resizeBox) {
        updateResizeBox(e.clientX, e.clientY);
    }
}

function handleAdvancedMouseUp(e) {
    if (isResizing && resizeBox) {
        finalizeResize(e);
        isResizing = false;
    }
}

function createResizeBox(x, y) {
    resizeBox = $(`
        <div class="resize-box" style="left: ${x}px; top: ${y}px; width: 0px; height: 0px;">
            <div class="resize-info"></div>
        </div>
    `)[0];
    
    $('body').append(resizeBox);
}

function updateResizeBox(currentX, currentY) {
    const width = Math.abs(currentX - resizeStartX);
    const height = Math.abs(currentY - resizeStartY);
    const left = Math.min(currentX, resizeStartX);
    const top = Math.min(currentY, resizeStartY);
    
    $(resizeBox).css({
        left: left + 'px',
        top: top + 'px',
        width: width + 'px',
        height: height + 'px'
    });
    
    // 상대적 크기 계산
    const editorRect = $('#editablePreview')[0].getBoundingClientRect();
    const relativeWidth = Math.round((width / editorRect.width) * 100);
    const relativeHeight = Math.round((height / editorRect.height) * 100);
    
    $(resizeBox).find('.resize-info').text(`${relativeWidth}% × ${relativeHeight}%`);
}

function finalizeResize(e) {
    const width = Math.abs(e.clientX - resizeStartX);
    const height = Math.abs(e.clientY - resizeStartY);
    
    if (width > 20 && height > 20) {
        const editorRect = $('#editablePreview')[0].getBoundingClientRect();
        const relativeWidth = Math.round((width / editorRect.width) * 100);
        const relativeHeight = Math.round((height / editorRect.height) * 100);
        
        // 크기가 지정된 이미지 플레이스홀더 생성
        const placeholder = $(`
            <div class="image-placeholder ${insertType === 'image-block' ? 'block' : 'inline'}" 
                 style="width: ${relativeWidth}%; height: ${Math.max(relativeHeight, 10)}%;">
                <i class="fas fa-image" style="font-size: 24px; display: block; margin-bottom: 8px;"></i>
                <div>클릭하여 이미지 선택</div>
                <div style="font-size: 12px; opacity: 0.7;">${relativeWidth}% × ${relativeHeight}%</div>
            </div>
        `);
        
        // 편집 영역에 추가
        $('#editablePreview').append(placeholder);
        
        // 플레이스홀더 클릭 이벤트
        placeholder.on('click', function(e) {
            e.preventDefault();
            currentImagePlaceholder = this;
            $('#imageUpload').click();
        });
    }
    
    $(resizeBox).remove();
    resizeBox = null;
}

// 테이블 삽입
function insertTable() {
    const rows = prompt('행 수를 입력하세요:', '3');
    const cols = prompt('열 수를 입력하세요:', '3');
    
    if (!rows || !cols || isNaN(rows) || isNaN(cols)) return;
    
    const rowCount = parseInt(rows);
    const colCount = parseInt(cols);
    
    if (rowCount < 1 || colCount < 1 || rowCount > 20 || colCount > 10) {
        showAdvancedStatusMessage('행은 1-20개, 열은 1-10개까지 가능합니다.', 'error');
        return;
    }
    
    let tableHTML = '<table class="content-table"><thead><tr>';
    
    // 헤더 생성
    for (let i = 0; i < colCount; i++) {
        tableHTML += `<th>헤더 ${i + 1}</th>`;
    }
    tableHTML += '</tr></thead><tbody>';
    
    // 바디 생성
    for (let i = 0; i < rowCount - 1; i++) {
        tableHTML += '<tr>';
        for (let j = 0; j < colCount; j++) {
            tableHTML += `<td>내용 ${i + 1}-${j + 1}</td>`;
        }
        tableHTML += '</tr>';
    }
    tableHTML += '</tbody></table>';
    
    insertHTMLAtCursor(tableHTML);
    showAdvancedStatusMessage('테이블이 삽입되었습니다.', 'success');
}

// SVG 삽입
function insertSVG() {
    const svgOptions = [
        { name: '원', svg: '<svg width="100" height="100" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="#3b82f6" stroke="#1e40af" stroke-width="2"/></svg>' },
        { name: '사각형', svg: '<svg width="100" height="80" viewBox="0 0 100 80"><rect x="10" y="10" width="80" height="60" fill="#10b981" stroke="#059669" stroke-width="2" rx="5"/></svg>' },
        { name: '삼각형', svg: '<svg width="100" height="80" viewBox="0 0 100 80"><polygon points="50,10 90,70 10,70" fill="#f59e0b" stroke="#d97706" stroke-width="2"/></svg>' },
        { name: '화살표', svg: '<svg width="100" height="50" viewBox="0 0 100 50"><path d="M10 25 L70 25 M60 15 L70 25 L60 35" fill="none" stroke="#ef4444" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>' }
    ];
    
    const choice = prompt(`SVG를 선택하세요:\n${svgOptions.map((opt, i) => `${i + 1}. ${opt.name}`).join('\n')}\n번호를 입력하세요:`, '1');
    
    if (!choice || isNaN(choice)) return;
    
    const index = parseInt(choice) - 1;
    if (index < 0 || index >= svgOptions.length) {
        showAdvancedStatusMessage('올바른 번호를 선택해주세요.', 'error');
        return;
    }
    
    const svgHTML = `<div class="svg-container">${svgOptions[index].svg}</div>`;
    insertHTMLAtCursor(svgHTML);
    showAdvancedStatusMessage('SVG가 삽입되었습니다.', 'success');
}

function insertHTMLAtCursor(html) {
    if ($('#editablePreview').is('[contenteditable]')) {
        document.execCommand('insertHTML', false, html);
    } else {
        $('#editablePreview').append(html);
    }
}

function clearFormat() {
    if ($('#editablePreview').is('[contenteditable]')) {
        document.execCommand('removeFormat');
        showAdvancedStatusMessage('서식이 제거되었습니다.', 'success');
    }
}

function saveAdvancedContent() {
    const content = $('#editablePreview').html();
    
    // HTML 에디터 업데이트
    if (htmlEditor) {
        htmlEditor.setValue(content);
    }
    
    // 임시 첨부파일들을 최종 확정
    if (uploadedAttachments.size > 0 && currentSlideData && currentSlideData.content) {
        finalizeAttachments(Array.from(uploadedAttachments), currentSlideData.content.id);
    }
    
    // 기존 저장 함수 호출
    if (typeof saveHtmlContent === 'function') {
        saveHtmlContent();
    }
}

function finalizeAttachments(attachmentIds, contentId) {
    $.ajax({
        url: `/agent/api/contents/${contentId}/attachments/finalize/`,
        type: 'POST',
        data: JSON.stringify({ attachment_ids: attachmentIds }),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function(response) {
            if (response.success) {
                uploadedAttachments.clear();
                console.log('첨부파일 확정 완료:', response.updated_count);
            }
        },
        error: function() {
            console.error('첨부파일 확정 오류');
        }
    });
}

function showAdvancedStatusMessage(message, type) {
    const statusDiv = $(`<div class="status-message ${type}">${message}</div>`);
    $('body').append(statusDiv);
    
    setTimeout(() => {
        statusDiv.remove();
    }, 3000);
}

function resetEditor() {
    if (!confirm('편집기를 초기화하시겠습니까? 저장하지 않은 변경사항은 사라집니다.')) return;
    
    $('#editablePreview').html(`
        <div class="preview-placeholder">
            <i class="fas fa-edit"></i>
            <h4 class="text-lg font-semibold mb-2">편집할 문항을 선택해주세요</h4>
            <p class="text-sm">편집모드를 켜고 텍스트를 클릭하여 수정할 수 있습니다</p>
        </div>
    `);
    
    cancelInsertMode();
    uploadedAttachments.clear();
    showAdvancedStatusMessage('편집기가 초기화되었습니다.', 'success');
}

// 기존 이미지 업로드 함수 (레거시 지원)
function uploadImage(file, currentEditingImage) {
    // 레거시 이미지 업로드 지원
    const formData = new FormData();
    formData.append('file', file);
    
    $.ajax({
        url: "/agent/api/files/upload/temporary/",
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function(response) {
            if (response.success) {
                if (currentEditingImage) {
                    $(currentEditingImage).attr('src', response.file_url);
                    uploadedAttachments.add(response.attachment_id);
                    showAdvancedStatusMessage('이미지가 성공적으로 교체되었습니다.', 'success');
                }
            } else {
                showAdvancedStatusMessage(response.error || '업로드에 실패했습니다.', 'error');
            }
        },
        error: function() {
            showAdvancedStatusMessage('네트워크 오류가 발생했습니다.', 'error');
        }
    });
}

// 전역 함수로 노출
window.resetEditor = resetEditor;