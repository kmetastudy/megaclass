// static/js/cp_agent/text-editing.js - 텍스트 편집 시스템

/* ========== 텍스트 편집 이벤트 바인딩 ========== */

/**
 * 텍스트 편집 이벤트 바인딩
 */
function bindTextEditingEvents() {
    debugLog('TEXT_EDIT', '텍스트 편집 이벤트 바인딩 시작');
    
    // 기존 이벤트 핸들러 모두 제거
    $(document).off('dblclick', '.editable-word');
    $(document).off('click', '.editable-image');
    
    // 새로운 텍스트 편집 이벤트
    $(document).on('dblclick.newTextEdit', '.editable-word', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const $word = $(this);
        const wordId = $word.data('word-id');
        const originalText = $word.data('original');
        const currentText = $word.text();
        
        debugLog('TEXT_EDIT', '텍스트 편집 시작', { wordId, originalText, currentText });
        
        if (!wordId || wordId === 'undefined' || wordId === 'NaN') {
            debugLog('TEXT_EDIT', '유효하지 않은 wordId', wordId);
            showToast('편집할 수 없는 텍스트입니다', 'error');
            return;
        }
        
        if ($word.hasClass('editing-word')) {
            return;
        }
        
        startTextEditing($word, wordId, originalText, currentText);
    });
    
    // 이미지 편집 이벤트
    $(document).on('click.imageEdit', '.editable-image', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        debugLog('TEXT_EDIT', '이미지 편집 클릭');
        currentEditingImage = $(this);
        $('#imageUpload').click();
    });
    
    debugLog('TEXT_EDIT', '이벤트 핸들러 바인딩 완료');
}

/**
 * 텍스트 편집 시작
 */
function startTextEditing($word, wordId, originalText, currentText) {
    debugLog('TEXT_EDIT', '텍스트 편집 시작', { wordId, originalText, currentText });
    
    $word.addClass('editing-word');
    
    const $input = $('<input type="text" class="edit-input">');
    $input.val(currentText);
    $input.css({
        'width': Math.max(100, currentText.length * 10 + 30) + 'px',
        'font-family': $word.css('font-family'),
        'font-size': $word.css('font-size'),
        'font-weight': $word.css('font-weight')
    });
    
    $word.replaceWith($input);
    $input.focus().select();
    
    function finishEditing() {
        const newText = $input.val(); // trim() 하지 않음
        
        if (newText !== currentText) {
            const updateSuccess = updateTextInHtml(wordId, currentText, newText);
            
            if (updateSuccess) {
                const $newWord = $(`<span class="editable-word text-changed" 
                    data-word-id="${wordId}" 
                    data-original="${originalText}"
                    data-changed="true"
                    title="더블클릭하여 편집"
                    style="color: #ef4444 !important; font-weight: 500;">${newText}</span>`);
                
                $input.replaceWith($newWord);
                showToast(`"${currentText}" → "${newText}" 변경되었습니다`, 'success');
                
                setTimeout(() => {
                    CPAgent.Content.updatePreview();
                    CPAgent.UI.updateEditControls();
                }, 100);
            } else {
                restoreOriginalWord();
                showToast('텍스트 업데이트에 실패했습니다', 'error');
            }
        } else {
            restoreOriginalWord();
        }
    }
    
    function cancelEditing() {
        restoreOriginalWord();
        showToast('편집이 취소되었습니다', 'warning');
    }
    
    function restoreOriginalWord() {
        const $restoredWord = $(`<span class="editable-word" 
            data-word-id="${wordId}" 
            data-original="${originalText}"
            title="더블클릭하여 편집">${currentText}</span>`);
        $input.replaceWith($restoredWord);
    }
    
    $input.on('keydown', function(e) {
        e.stopPropagation();
        if (e.key === 'Enter') {
            e.preventDefault();
            finishEditing();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelEditing();
        }
    });
    
    $input.on('blur', function() {
        finishEditing();
    });
}

/* ========== HTML 텍스트 업데이트 ========== */

/**
 * HTML에서 텍스트 업데이트
 */
function updateTextInHtml(wordId, oldText, newText) {
    debugLog('TEXT_EDIT', `HTML 텍스트 업데이트: wordId=${wordId}, "${oldText}" → "${newText}"`);
    
    const mapping = wordMappings.get(wordId);
    if (!mapping) {
        debugLog('TEXT_EDIT', '매핑 정보를 찾을 수 없음', wordId);
        return false;
    }
    
    let currentHtml = htmlEditorInstance.getValue();
    
    const escapedOldText = escapeRegExp(oldText);
    
    const strategies = [
        {
            name: 'word boundary',
            regex: new RegExp(`\\b${escapedOldText}\\b`, 'g')
        },
        {
            name: 'html text',
            regex: new RegExp(`(>[^<]*?)${escapedOldText}([^<]*?<)`, 'g'),
            replacement: `$1${newText}$2`
        },
        {
            name: 'simple text',
            regex: new RegExp(escapedOldText, 'g')
        }
    ];
    
    let updatedHtml = currentHtml;
    let replacementMade = false;
    
    for (const strategy of strategies) {
        if (strategy.regex.test(currentHtml)) {
            if (strategy.replacement) {
                updatedHtml = currentHtml.replace(strategy.regex, strategy.replacement);
            } else {
                updatedHtml = currentHtml.replace(strategy.regex, newText);
            }
            replacementMade = true;
            debugLog('TEXT_EDIT', `${strategy.name} 전략으로 교체 성공`);
            break;
        }
    }
    
    if (replacementMade) {
        htmlEditorInstance.setValue(updatedHtml);
        mapping.originalText = newText;
        wordMappings.set(wordId, mapping);
        return true;
    }
    
    debugLog('TEXT_EDIT', '모든 교체 전략 실패');
    return false;
}

/* ========== 편집 가능한 콘텐츠 생성 ========== */

/**
 * HTML 콘텐츠를 편집 가능한 형태로 변환
 */
function updateEditableContent(html) {
    debugLog('TEXT_EDIT', '편집 가능한 콘텐츠 업데이트 시작');
    
    const timer = new PerformanceTimer('편집 가능한 콘텐츠 생성');
    
    const $container = $('#editableContent');
    $container.empty();
    
    if (!html || html.trim() === '') {
        $container.html('<p class="text-gray-500 text-center py-4">편집할 콘텐츠가 없습니다</p>');
        CPAgent.UI.updateEditControls();
        return;
    }
    
    originalHtmlContent = html;
    wordMappings.clear();
    
    try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        let globalWordId = 0;
        
        function processNode(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                const fullText = node.textContent;
                
                if (!fullText.trim()) {
                    return $('<span>').text(fullText);
                }
                
                const segments = fullText.split(/(\s+)/);
                const $textContainer = $('<span class="text-container">');
                
                segments.forEach((segment, index) => {
                    if (segment.trim()) {
                        const wordId = `word_${globalWordId++}`;
                        
                        wordMappings.set(wordId, {
                            originalText: segment,
                            fullTextContent: fullText,
                            segmentIndex: index,
                            parentNode: node.parentNode ? node.parentNode.tagName : 'BODY'
                        });
                        
                        const $word = $(`<span class="editable-word" 
                            data-word-id="${wordId}" 
                            data-original="${segment}"
                            title="더블클릭하여 편집">${segment}</span>`);
                        
                        $textContainer.append($word);
                    } else if (segment) {
                        $textContainer.append(segment);
                    }
                });
                
                return $textContainer;
                
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                if (node.tagName === 'IMG') {
                    const imageId = `img_${globalWordId++}`;
                    const $img = $(`<div class="relative inline-block">
                        <img src="${node.src}" 
                             class="editable-image max-w-full h-auto" 
                             data-image-id="${imageId}"
                             data-original-src="${node.src}"
                             title="클릭하여 이미지 변경">
                        <div class="image-upload-overlay">
                            <span>📸 클릭하여 변경</span>
                        </div>
                    </div>`);
                    
                    // 이미지 속성 복사
                    const $realImg = $img.find('img');
                    Array.from(node.attributes).forEach(attr => {
                        if (attr.name !== 'src' && attr.name !== 'class') {
                            $realImg.attr(attr.name, attr.value);
                        }
                    });
                    
                    return $img;
                } else {
                    const $element = $(`<${node.tagName.toLowerCase()}></${node.tagName.toLowerCase()}>`);
                    
                    Array.from(node.attributes).forEach(attr => {
                        $element.attr(attr.name, attr.value);
                    });
                    
                    Array.from(node.childNodes).forEach(child => {
                        const $processedChild = processNode(child);
                        if ($processedChild) {
                            $element.append($processedChild);
                        }
                    });
                    
                    return $element;
                }
            }
            
            return null;
        }
        
        const $processedContent = $('<div>');
        Array.from(doc.body.childNodes).forEach(child => {
            const $processed = processNode(child);
            if ($processed) {
                $processedContent.append($processed);
            }
        });
        
        $container.html($processedContent.html());
        
        // 호버 효과 적용
        $container.find('.editable-word').on('mouseenter', function() {
            if (!$(this).hasClass('text-changed')) {
                $(this).css({
                    'background-color': '#dbeafe',
                    'border-color': '#93c5fd'
                });
            }
        }).on('mouseleave', function() {
            if (!$(this).hasClass('text-changed')) {
                $(this).css({
                    'background-color': 'transparent',
                    'border-color': 'transparent'
                });
            }
        });
        
        const editableWordCount = $('.editable-word').length;
        const editableImageCount = $('.editable-image').length;
        
        debugLog('TEXT_EDIT', `편집 가능한 단어: ${editableWordCount}개, 이미지: ${editableImageCount}개`);
        
        CPAgent.UI.updateEditStatus();
        CPAgent.UI.updateEditControls();
        
        timer.end();
        
    } catch (error) {
        debugLog('TEXT_EDIT', 'HTML 파싱 오류', error);
        $container.html('<p class="text-red-500 text-center py-4">콘텐츠 파싱 중 오류가 발생했습니다</p>');
    }
}

/* ========== 편집 컨트롤 함수들 ========== */

/**
 * 모든 변경사항 초기화
 */
function resetAllChanges() {
    if (!confirm('모든 변경사항을 취소하시겠습니까?')) {
        return;
    }
    
    debugLog('TEXT_EDIT', '모든 변경사항 초기화');
    
    // 텍스트 변경사항 취소
    $('.text-changed').each(function() {
        const $changed = $(this);
        const original = $changed.data('original');
        const wordId = $changed.data('word-id');
        
        const $original = $(`<span class="editable-word" 
            data-word-id="${wordId}" 
            data-original="${original}"
            title="더블클릭하여 편집">${original}</span>`);
        $changed.replaceWith($original);
    });
    
    // 이미지 변경사항 취소
    CPAgent.Image.cancelImageChanges();
    
    // HTML 에디터를 원본으로 복원
    if (originalHtmlContent) {
        htmlEditorInstance.setValue(originalHtmlContent);
    }
    
    // 미리보기 업데이트
    CPAgent.Content.updatePreview();
    
    showToast('모든 변경사항이 취소되었습니다', 'success');
}

/**
 * 변경된 요소들 강조 표시
 */
function showChangedElements() {
    const $changedElements = $('.text-changed, .editable-image[data-changed="true"]');
    
    if ($changedElements.length === 0) {
        showToast('변경된 요소가 없습니다', 'warning');
        return;
    }
    
    // 기존 강조 제거
    $('.highlight-changed').removeClass('highlight-changed');
    
    // 변경된 요소들 강조
    $changedElements.addClass('highlight-changed').css({
        'animation': 'pulse 1s infinite',
        'background-color': '#fef3c7'
    });
    
    // 2초 후 강조 제거
    setTimeout(() => {
        $('.highlight-changed').removeClass('highlight-changed').css({
            'animation': '',
            'background-color': ''
        });
    }, 2000);
    
    showToast(`${$changedElements.length}개의 변경된 요소를 강조 표시했습니다`, 'success');
}

/**
 * 편집 통계 가져오기
 */
function getEditingStats() {
    const stats = {
        totalEditableWords: $('.editable-word').length,
        totalEditableImages: $('.editable-image').length,
        changedWords: $('.text-changed').length,
        changedImages: $('.editable-image[data-changed="true"]').length,
        totalWordMappings: wordMappings.size
    };
    
    debugLog('TEXT_EDIT', '편집 통계', stats);
    return stats;
}

/**
 * 편집 상태 초기화
 */
function resetEditingState() {
    debugLog('TEXT_EDIT', '편집 상태 초기화');
    
    wordMappings.clear();
    originalHtmlContent = '';
    
    // 모든 편집 관련 클래스 제거
    $('.text-changed').removeClass('text-changed');
    $('.editing-word').removeClass('editing-word');
    $('.editable-word[data-changed="true"]').removeAttr('data-changed');
    $('.editable-image[data-changed="true"]').removeAttr('data-changed');
    
    CPAgent.UI.updateEditControls();
}

/* ========== 전역 텍스트 편집 네임스페이스 ========== */
window.CPAgent.TextEditing = {
    bindTextEditingEvents,
    updateEditableContent,
    resetAllChanges,
    showChangedElements,
    getEditingStats,
    resetEditingState,
    
    // 내부 함수들 (필요시 접근)
    updateTextInHtml,
    startTextEditing
};