// static/js/cp_agent/image.js - 이미지 처리 시스템

/* ========== 이미지 업로드 시스템 ========== */

/**
 * 이미지 업로드
 */
function uploadImage(file, $img) {
    debugLog('IMAGE', '이미지 업로드 시작', file.name);
    
    // 파일 유효성 검사
    const validation = validateImageFile(file);
    if (!validation.valid) {
        showToast(validation.message, 'error');
        return;
    }
    
    // 로딩 상태 표시
    $img.addClass('image-loading');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('original_name', file.name);
    formData.append('file_type', file.type);
    formData.append('file_size', file.size);
    
    // 현재 콘텐츠 ID가 있으면 전송
    if (currentContent && currentContent.id) {
        formData.append('content_id', currentContent.id);
    }
    
    const timer = new PerformanceTimer('이미지 업로드');
    
    $.ajax({
        url: '/cp/api/upload-image/',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(data) {
            debugLog('IMAGE', '업로드 성공', data);
            
            // 현재 이미지 정보 수집
            const imageId = $img.attr('id');
            const newSrc = data.file_url;
            
            // HTML 에디터의 현재 내용을 DOM으로 파싱하여 교체
            const currentHtml = htmlEditorInstance.getValue();
            let updatedHtml = updateImageSrcInHtml(currentHtml, imageId, newSrc);
            
            if (updatedHtml !== currentHtml) {
                htmlEditorInstance.setValue(updatedHtml);
                debugLog('IMAGE', 'HTML 이미지 src 교체 성공');
            } else {
                debugLog('IMAGE', 'HTML 이미지 src 교체 실패');
                showToast('이미지 교체에 실패했습니다', 'error');
                $img.removeClass('image-loading');
                return;
            }
            
            // 원본 src 저장 (취소 시 복원용)
            if (!$img.attr('data-original-src')) {
                $img.attr('data-original-src', $img.attr('src'));
            }
            
            // 캐시 버스터 추가
            const cacheBustedUrl = newSrc + '?t=' + Date.now();
            
            // 이미지 요소 업데이트
            updateImageElement($img, cacheBustedUrl, data.attachment_id, newSrc);
            
            // 모든 탭의 동일한 이미지들 업데이트
            setTimeout(() => {
                CPAgent.Content.updatePreview();
                updateAllTabImages(imageId, cacheBustedUrl);
            }, 100);
            
            // 임시 업로드 목록에 추가
            if (data.attachment_id) {
                temporaryUploads.push(data.attachment_id);
            }
            
            timer.end();
            showToast('이미지가 업로드되었습니다!', 'success');
            CPAgent.UI.updateEditControls();
        },
        error: function(xhr) {
            debugLog('IMAGE', '업로드 실패', xhr);
            
            $img.removeClass('image-loading');
            
            let errorMsg = '이미지 업로드 중 오류가 발생했습니다.';
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    errorMsg = response.error;
                }
            } catch (e) {
                debugLog('IMAGE', '에러 응답 파싱 실패', e);
            }
            
            showToast(errorMsg, 'error');
        }
    });
}

/**
 * 이미지 파일 유효성 검사
 */
function validateImageFile(file) {
    // 파일 크기 검증 (10MB 제한)
    if (file.size > 10 * 1024 * 1024) {
        return {
            valid: false,
            message: '파일 크기는 10MB 이하여야 합니다'
        };
    }
    
    // 파일 타입 검증
    if (!file.type.startsWith('image/')) {
        return {
            valid: false,
            message: '이미지 파일만 업로드 가능합니다'
        };
    }
    
    // 지원되는 이미지 형식 확인
    const supportedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'];
    if (!supportedTypes.includes(file.type)) {
        return {
            valid: false,
            message: '지원되지 않는 이미지 형식입니다. (JPG, PNG, GIF, WebP, SVG만 지원)'
        };
    }
    
    return { valid: true };
}

/**
 * 이미지 요소 업데이트
 */
function updateImageElement($img, cacheBustedUrl, attachmentId, newSrc) {
    $img.attr('src', cacheBustedUrl);
    $img.attr('data-changed', 'true');
    $img.attr('data-attachment-id', attachmentId || '');
    $img.attr('data-new-src', newSrc);
    $img.removeClass('image-loading');
    
    debugLog('IMAGE', '이미지 요소 업데이트 완료', {
        src: cacheBustedUrl,
        attachmentId: attachmentId,
        newSrc: newSrc
    });
}

/* ========== HTML 이미지 src 교체 ========== */

/**
 * DOM 파서를 사용하여 HTML에서 이미지 src 정확히 교체
 */
function updateImageSrcInHtml(html, imageId, newSrc) {
    debugLog('IMAGE', 'DOM 파서를 통한 이미지 교체', { imageId, newSrc });
    
    try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        let imageFound = false;
        
        // ID로 이미지 찾기
        if (imageId) {
            const targetImg = doc.getElementById(imageId);
            if (targetImg) {
                debugLog('IMAGE', 'ID로 이미지 발견', targetImg.src);
                targetImg.setAttribute('src', newSrc);
                imageFound = true;
            }
        }
        
        // ID로 찾지 못한 경우 손상된 URL 감지하여 교체
        if (!imageFound) {
            const allImages = doc.querySelectorAll('img');
            
            for (let i = 0; i < allImages.length; i++) {
                const img = allImages[i];
                const currentSrc = img.getAttribute('src');
                
                if (currentSrc && isCorruptedSrc(currentSrc)) {
                    debugLog('IMAGE', '손상된 URL 감지하여 교체', currentSrc);
                    img.setAttribute('src', newSrc);
                    imageFound = true;
                    break;
                }
            }
        }
        
        if (imageFound) {
            const updatedHtml = doc.body.innerHTML;
            debugLog('IMAGE', 'DOM 파서 교체 성공');
            return updatedHtml;
        } else {
            debugLog('IMAGE', '교체할 이미지를 찾지 못함');
            return html;
        }
        
    } catch (error) {
        debugLog('IMAGE', 'DOM 파서 오류', error);
        return html;
    }
}

/**
 * 모든 탭의 동일한 이미지들 업데이트
 */
function updateAllTabImages(imageId, newSrc) {
    debugLog('IMAGE', '모든 탭 이미지 업데이트', { imageId, newSrc });
    
    $('.preview-tab-content').each(function() {
        const tabId = $(this).attr('id');
        
        // ID로 찾기
        if (imageId) {
            const $targetImg = $(this).find(`#${imageId}`);
            if ($targetImg.length > 0) {
                $targetImg.attr('src', newSrc);
                debugLog('IMAGE', `${tabId} 탭 이미지 업데이트 완료`);
            }
        }
        
        // 손상된 src를 가진 이미지들도 정리
        $(this).find('img').each(function() {
            const currentSrc = $(this).attr('src');
            if (currentSrc && isCorruptedSrc(currentSrc)) {
                $(this).attr('src', newSrc);
                debugLog('IMAGE', `${tabId} 탭 손상된 이미지 복구 완료`);
            }
        });
    });
}

/* ========== 이미지 변경사항 관리 ========== */

/**
 * 이미지 변경사항 취소
 */
function cancelImageChanges() {
    debugLog('IMAGE', '이미지 변경사항 취소');
    
    $('.editable-image[data-changed="true"]').each(function() {
        const $img = $(this);
        const originalSrc = $img.attr('data-original-src');
        const attachmentId = $img.attr('data-attachment-id');
        
        if (originalSrc) {
            // 원래 이미지로 복원
            $img.attr('src', originalSrc);
            
            // HTML 에디터의 내용도 업데이트
            const newSrc = $img.attr('data-new-src');
            if (newSrc) {
                let html = htmlEditorInstance.getValue();
                html = html.replace(newSrc, originalSrc);
                htmlEditorInstance.setValue(html);
            }
            
            // 변경 표시 제거
            $img.removeAttr('data-changed data-attachment-id data-new-src');
        }
        
        // 임시 업로드 파일 삭제
        if (attachmentId) {
            deleteTemporaryUpload(attachmentId);
        }
    });
    
    // 임시 업로드 목록 초기화
    temporaryUploads = [];
    
    // 미리보기 업데이트
    CPAgent.Content.updatePreview();
}

/**
 * 임시 업로드 파일 삭제
 */
function deleteTemporaryUpload(attachmentId) {
    $.ajax({
        url: `/cp/api/cleanup-temp-upload/${attachmentId}/`,
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function() {
            debugLog('IMAGE', `임시 이미지 ${attachmentId} 삭제 완료`);
        },
        error: function(xhr) {
            debugLog('IMAGE', `임시 이미지 ${attachmentId} 삭제 실패`, xhr);
        }
    });
}

/* ========== 이미지 유효성 검사 및 정리 ========== */

/**
 * HTML 에디터에서 손상된 이미지 src 모두 정리
 */
function cleanupCorruptedImageSrcs() {
    debugLog('IMAGE', '손상된 이미지 src 정리 시작');
    
    const currentHtml = htmlEditorInstance.getValue();
    const parser = new DOMParser();
    const doc = parser.parseFromString(currentHtml, 'text/html');
    
    let hasChanges = false;
    const allImages = doc.querySelectorAll('img');
    
    allImages.forEach((img, index) => {
        const currentSrc = img.getAttribute('src');
        if (currentSrc && isCorruptedSrc(currentSrc)) {
            debugLog('IMAGE', `손상된 이미지 ${index} 발견`, currentSrc);
            
            // 첫 번째 유효한 URL만 추출
            const cleanSrc = extractCleanImageUrl(currentSrc);
            if (cleanSrc) {
                img.setAttribute('src', cleanSrc);
                hasChanges = true;
                debugLog('IMAGE', '정리된 src', cleanSrc);
            }
        }
    });
    
    if (hasChanges) {
        const cleanedHtml = doc.body.innerHTML;
        htmlEditorInstance.setValue(cleanedHtml);
        CPAgent.Content.updatePreview();
        showToast('손상된 이미지 경로를 정리했습니다', 'success');
    } else {
        showToast('정리할 손상된 이미지가 없습니다', 'warning');
    }
}

/**
 * 손상된 이미지 URL에서 첫 번째 유효한 URL 추출
 */
function extractCleanImageUrl(corruptedSrc) {
    const extensions = ['.gif', '.jpg', '.jpeg', '.png', '.webp', '.svg'];
    
    for (const ext of extensions) {
        const firstExtIndex = corruptedSrc.indexOf(ext);
        if (firstExtIndex > -1) {
            return corruptedSrc.substring(0, firstExtIndex + ext.length);
        }
    }
    
    return null;
}

/**
 * 모든 이미지의 유효성 검사
 */
function validateAllImages() {
    debugLog('IMAGE', '이미지 유효성 검사 시작');
    
    const currentHtml = htmlEditorInstance.getValue();
    const parser = new DOMParser();
    const doc = parser.parseFromString(currentHtml, 'text/html');
    
    const allImages = doc.querySelectorAll('img');
    const report = {
        total: allImages.length,
        valid: 0,
        corrupted: 0,
        missing: 0,
        details: []
    };
    
    allImages.forEach((img, index) => {
        const src = img.getAttribute('src');
        const id = img.getAttribute('id') || `image-${index}`;
        const alt = img.getAttribute('alt') || '(alt 없음)';
        
        const detail = {
            index: index,
            id: id,
            alt: alt,
            src: src,
            status: 'unknown'
        };
        
        if (!src) {
            detail.status = 'missing';
            detail.issue = 'src 속성이 없음';
            report.missing++;
        } else if (isCorruptedSrc(src)) {
            detail.status = 'corrupted';
            detail.issue = 'URL이 누적됨';
            report.corrupted++;
        } else {
            detail.status = 'valid';
            report.valid++;
        }
        
        report.details.push(detail);
        debugLog('IMAGE', `이미지 ${index} 검사`, detail);
    });
    
    debugLog('IMAGE', '검사 결과', {
        전체: report.total,
        정상: report.valid,
        손상: report.corrupted,
        누락: report.missing
    });
    
    // 결과 표시
    showImageValidationReport(report);
    
    return report;
}

/**
 * 이미지 검사 결과 표시
 */
function showImageValidationReport(report) {
    let message = `📊 이미지 검사 결과\n\n`;
    message += `전체: ${report.total}개\n`;
    message += `✅ 정상: ${report.valid}개\n`;
    message += `❌ 손상: ${report.corrupted}개\n`;
    message += `⚠️ 누락: ${report.missing}개\n\n`;
    
    if (report.corrupted > 0 || report.missing > 0) {
        message += `🔧 문제가 있는 이미지:\n`;
        report.details.forEach(detail => {
            if (detail.status !== 'valid') {
                message += `- ${detail.id}: ${detail.issue}\n`;
            }
        });
        
        if (report.corrupted > 0) {
            message += `\n"손상된 이미지 경로 정리" 버튼을 클릭하여 자동 수정할 수 있습니다.`;
        }
    } else {
        message += `🎉 모든 이미지가 정상입니다!`;
    }
    
    alert(message);
    
    // 토스트로도 간단한 결과 표시
    if (report.corrupted > 0 || report.missing > 0) {
        showToast(`이미지 검사 완료: 문제 ${report.corrupted + report.missing}개 발견`, 'warning');
    } else {
        showToast('모든 이미지가 정상입니다!', 'success');
    }
}

/**
 * 저장 전 이미지 자동 검증 및 정리
 */
function validateAndCleanupBeforeSave() {
    debugLog('IMAGE', '저장 전 이미지 자동 정리');
    
    const report = validateAllImages();
    
    if (report.corrupted > 0) {
        debugLog('IMAGE', '손상된 이미지 발견, 자동 정리 시작');
        cleanupCorruptedImageSrcs();
        
        // 정리 후 다시 검증
        setTimeout(() => {
            const newReport = validateAllImages();
            if (newReport.corrupted === 0) {
                debugLog('IMAGE', '이미지 정리 완료');
                showToast('저장 전 이미지 경로 정리 완료', 'success');
            }
        }, 100);
    }
}

/* ========== 이미지 통계 및 유틸리티 ========== */

/**
 * 이미지 통계 가져오기
 */
function getImageStats() {
    const stats = {
        totalImages: $('img').length,
        editableImages: $('.editable-image').length,
        changedImages: $('.editable-image[data-changed="true"]').length,
        temporaryUploads: temporaryUploads.length
    };
    
    debugLog('IMAGE', '이미지 통계', stats);
    return stats;
}

/**
 * 모든 이미지 새로고침
 */
function refreshAllImages() {
    debugLog('IMAGE', '모든 이미지 새로고침');
    
    $('img').each(function() {
        const $img = $(this);
        const src = $img.attr('src');
        
        if (src && !src.includes('?t=')) {
            $img.attr('src', src + '?t=' + Date.now());
        }
    });
}

/* ========== 전역 이미지 네임스페이스 ========== */
window.CPAgent.Image = {
    uploadImage,
    cancelImageChanges,
    cleanupCorruptedImageSrcs,
    validateAllImages,
    validateAndCleanupBeforeSave,
    getImageStats,
    refreshAllImages,
    
    // 내부 함수들 (필요시 접근)
    updateImageSrcInHtml,
    updateAllTabImages,
    validateImageFile
};