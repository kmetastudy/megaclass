// static/js/super_agent/batch-upload.js
// 파일 업로드 및 배치 처리 관련 함수들

function initializeUpload() {
    console.log('Upload 모듈 초기화');
    
    // 파일 입력 변경 (멀티 파일)
    $('#fileInput').on('change', handleFileSelect);
    
    // 드래그 앤 드롭 (멀티 파일)
    const uploadArea = document.getElementById('uploadArea');
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files).filter(file => file.name.endsWith('.json'));
        if (files.length > 0) {
            handleFiles(files);
        } else {
            alert('JSON 파일만 업로드 가능합니다.');
        }
    });
}

function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
        handleFiles(files);
    }
}

function handleFiles(files) {
    const jsonFiles = files.filter(file => file.name.endsWith('.json'));
    
    if (jsonFiles.length === 0) {
        alert('JSON 파일만 업로드 가능합니다.');
        return;
    }

    if (jsonFiles.length !== files.length) {
        alert(`${files.length - jsonFiles.length}개 파일이 JSON이 아니어서 제외되었습니다.`);
    }

    uploadedFiles = [];
    allUploadedData = [];
    
    let processedCount = 0;
    const totalFiles = jsonFiles.length;

    jsonFiles.forEach((file, index) => {
        const formData = new FormData();
        formData.append('file', file);

        $.ajax({
            url: "/agent/api/questions/batch/upload/",
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': csrfToken
            },
            success: function(response) {
                processedCount++;
                
                if (response.success) {
                    uploadedFiles.push({
                        name: file.name,
                        data: response.data,
                        success: true
                    });
                    allUploadedData = allUploadedData.concat(response.data);
                } else {
                    uploadedFiles.push({
                        name: file.name,
                        error: response.error,
                        success: false
                    });
                }
                
                if (processedCount === totalFiles) {
                    showFilePreview();
                }
            },
            error: function() {
                processedCount++;
                uploadedFiles.push({
                    name: file.name,
                    error: '업로드 실패',
                    success: false
                });
                
                if (processedCount === totalFiles) {
                    showFilePreview();
                }
            }
        });
    });
}

function showFilePreview() {
    $('#uploadArea').hide();
    $('#filePreview').show();
    
    const successFiles = uploadedFiles.filter(f => f.success);
    const errorFiles = uploadedFiles.filter(f => !f.success);
    const totalItems = allUploadedData.length;
    
    const content = $('#previewContent');
    content.html(`
        <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <div class="text-sm text-blue-600 font-medium">업로드된 파일</div>
                <div class="text-2xl font-bold text-blue-800">${successFiles.length}</div>
            </div>
            <div class="bg-green-50 p-4 rounded-lg border border-green-200">
                <div class="text-sm text-green-600 font-medium">총 문항 수</div>
                <div class="text-2xl font-bold text-green-800">${totalItems}</div>
            </div>
            <div class="bg-red-50 p-4 rounded-lg border border-red-200">
                <div class="text-sm text-red-600 font-medium">오류 파일</div>
                <div class="text-2xl font-bold text-red-800">${errorFiles.length}</div>
            </div>
        </div>
        
        <div class="max-h-60 overflow-y-auto">
            <h5 class="font-semibold text-gray-700 mb-3">파일 목록</h5>
            ${uploadedFiles.map((file, index) => `
                <div class="flex items-center justify-between p-3 border rounded-lg mb-2 transition-all hover:shadow-sm ${file.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}">
                    <div class="flex items-center">
                        <i class="fas fa-${file.success ? 'check-circle text-green-500' : 'exclamation-circle text-red-500'} mr-3"></i>
                        <span class="font-medium">${file.name}</span>
                    </div>
                    <div class="text-sm text-gray-600">
                        ${file.success ? `${file.data.length}개 문항` : file.error}
                    </div>
                </div>
            `).join('')}
            
            ${totalItems > 0 ? `
                <div class="mt-4 p-3 bg-gray-50 rounded-lg border">
                    <h6 class="font-semibold text-gray-700 mb-2">문항 미리보기 (처음 3개)</h6>
                    ${allUploadedData.slice(0, 3).map((item, index) => `
                        <div class="text-sm p-2 border-b last:border-b-0 hover:bg-white transition-colors">
                            <strong>${index + 1}.</strong> ${item.course} - ${item.chasi} (${item.type})
                        </div>
                    `).join('')}
                    ${allUploadedData.length > 3 ? `<div class="text-sm text-gray-500 p-2">... 외 ${allUploadedData.length - 3}개</div>` : ''}
                </div>
            ` : ''}
        </div>
    `);
}

function startProcessing() {
    if (!allUploadedData || allUploadedData.length === 0) {
        alert('처리할 데이터가 없습니다.');
        return;
    }

    isProcessing = true;
    isPaused = false;
    currentIndex = 0;
    processResults = [];

    $('#filePreview').hide();
    $('#progressContainer').show();
    $('#processingIndicator').show();
    $('#completionIndicator').hide();
    
    updateProgress();
    processNextItem();
}

function processNextItem() {
    if (!isProcessing || isPaused) {
        return;
    }
    
    if (currentIndex >= allUploadedData.length) {
        finishProcessing();
        return;
    }

    const item = allUploadedData[currentIndex];
    $('#currentProcessing').text(`${currentIndex + 1}/${allUploadedData.length}: ${item.course} - ${item.chasi}`);

    $.ajax({
        url: "/agent/api/questions/batch/process/",
        type: 'POST',
        data: JSON.stringify({ 
            item: item,
            selected_course_id: selectedCourseId 
        }),
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function(response) {
            processResults.push({
                item: item,
                response: response,
                success: response.success
            });

            addLogItem(response, item);
            
            if (response.success) {
                setTimeout(() => {
                    if (typeof updateTreeItem === 'function') {
                        updateTreeItem(response.chasi_id, response.action, response.title, response.slide_id);
                    }
                }, 200);
            }

            currentIndex++;
            updateProgress();
            
            setTimeout(processNextItem, 300);
        },
        error: function() {
            processResults.push({
                item: item,
                success: false,
                error: '네트워크 오류'
            });

            addLogItem({ success: false, error: '네트워크 오류' }, item);
            currentIndex++;
            updateProgress();
            
            setTimeout(processNextItem, 300);
        }
    });
}

function finishProcessing() {
    isProcessing = false;
    
    $('#processingIndicator').hide();
    $('#progressContainer').hide();
    
    // 완료 상태 표시
    const successCount = processResults.filter(r => r.success).length;
    const totalCount = processResults.length;
    
    $('#completionSummary').text(`${successCount}/${totalCount} 문항이 성공적으로 처리되었습니다.`);
    $('#completionIndicator').show();
    
    // 5초 후 완료 표시 숨김
    setTimeout(() => {
        $('#completionIndicator').hide();
    }, 5000);
}

function pauseProcessing() {
    isPaused = !isPaused;
    const btn = $('#pauseBtn');
    if (isPaused) {
        btn.html('<i class="fas fa-play"></i> 재개');
    } else {
        btn.html('<i class="fas fa-pause"></i> 일시정지');
        if (isProcessing) {
            processNextItem();
        }
    }
}

function stopProcessing() {
    isProcessing = false;
    isPaused = false;
    
    $('#processingIndicator').hide();
    $('#progressContainer').hide();
    $('#pauseBtn').html('<i class="fas fa-pause"></i> 일시정지');
    
    const processedCount = currentIndex;
    const totalCount = allUploadedData.length;
    
    $('#completionSummary').text(`처리가 중단되었습니다. ${processedCount}/${totalCount} 문항이 처리되었습니다.`);
    $('#completionIndicator').show();
}

function updateProgress() {
    const percent = allUploadedData.length > 0 ? Math.round((currentIndex / allUploadedData.length) * 100) : 0;
    
    $('#progressFill').css('width', percent + '%');
    $('#progressText').text(`${currentIndex} / ${allUploadedData.length} 처리됨`);
    $('#progressPercent').text(percent + '%');
}

function addLogItem(response, item) {
    let solutionPreview = '';
    if (response.success && item.answer && item.answer.solution) {
        // 유니코드 디코딩 처리
        let solutionText = item.answer.solution;
        if (typeof solutionText === 'string' && solutionText.includes('\\u')) {
            try {
                solutionText = JSON.parse('"' + solutionText + '"');
            } catch (e) {
                // 디코딩 실패 시 원본 사용
            }
        }
        solutionPreview = solutionText.length > 50 ? 
            solutionText.substring(0, 50) + '...' : 
            solutionText;
    }
    
    const logItem = $(`
        <div class="log-item ${response.success ? 'success' : 'error'}">
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <strong>${item.course} - ${item.chasi}</strong>
                    <div class="text-xs mt-1">${response.message || response.error || '처리됨'}</div>
                    ${solutionPreview ? `<div class="text-xs mt-1 text-gray-600 italic">해설: ${solutionPreview}</div>` : ''}
                </div>
                <div class="text-xs ml-2">
                    <i class="fas fa-${response.success ? 'check-circle text-green-500' : 'exclamation-circle text-red-500'}"></i>
                </div>
            </div>
        </div>
    `);
    
    $('#logContent').prepend(logItem);
    $('#resultLog').show();
    $('#logContent').scrollTop(0);
}

function resetUpload() {
    uploadedFiles = [];
    allUploadedData = [];
    isProcessing = false;
    isPaused = false;
    currentIndex = 0;
    processResults = [];
    
    $('#filePreview').hide();
    $('#progressContainer').hide();
    $('#processingIndicator').hide();
    $('#completionIndicator').hide();
    $('#uploadArea').show();
    $('#fileInput').val('');
}

function exportResults() {
    if (processResults.length === 0) {
        alert('내보낼 결과가 없습니다.');
        return;
    }
    
    const dataStr = JSON.stringify(processResults, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'batch_process_results.json';
    link.click();
    URL.revokeObjectURL(url);
}

function clearLog() {
    $('#logContent').empty();
    processResults = [];
    $('#resultLog').hide();
}

// 전역 함수로 노출
window.startProcessing = startProcessing;
window.pauseProcessing = pauseProcessing;
window.stopProcessing = stopProcessing;
window.resetUpload = resetUpload;
window.exportResults = exportResults;
window.clearLog = clearLog;