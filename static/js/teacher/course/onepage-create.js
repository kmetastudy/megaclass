// static/js/teacher/course/onepage-create.js

// CodeMirror 에디터 인스턴스들
let quickPageEditor, quickMetaEditor, quickTagsEditor;

// 생성 탭 에디터 초기화
function initCreateTabEditors() {
    // 이미 초기화된 경우 스킵
    if (quickPageEditor) return;
    
    // HTML 에디터 (page 필드)
    const pageTextarea = document.getElementById('quickPageTextarea');
    const pageContainer = document.getElementById('quickPageEditor');
    
    if (pageTextarea && pageContainer && typeof CodeMirror !== 'undefined') {
        quickPageEditor = CodeMirror(pageContainer, {
            value: pageTextarea.value || '',
            mode: 'xml',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            autoCloseTags: true,
            placeholder: '콘텐츠 내용을 입력하세요...'
        });
        
        // 변경사항을 원본 textarea에 반영
        quickPageEditor.on('change', function() {
            pageTextarea.value = quickPageEditor.getValue();
        });
    }
    
    // JSON 에디터 - metadata
    const metaTextarea = document.getElementById('quickMetaTextarea');
    const metaContainer = document.getElementById('quickMetaEditor');
    
    if (metaTextarea && metaContainer && typeof CodeMirror !== 'undefined') {
        quickMetaEditor = CodeMirror(metaContainer, {
            value: metaTextarea.value || '{}',
            mode: 'javascript',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            placeholder: '{"key": "value"}'
        });
        
        quickMetaEditor.on('change', function() {
            metaTextarea.value = quickMetaEditor.getValue();
        });
    }
    
    // JSON 에디터 - tags
    const tagsTextarea = document.getElementById('quickTagsTextarea');
    const tagsContainer = document.getElementById('quickTagsEditor');
    
    if (tagsTextarea && tagsContainer && typeof CodeMirror !== 'undefined') {
        quickTagsEditor = CodeMirror(tagsContainer, {
            value: tagsTextarea.value || '{}',
            mode: 'javascript',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            placeholder: '{"평가기준": "예시"}'
        });
        
        quickTagsEditor.on('change', function() {
            tagsTextarea.value = quickTagsEditor.getValue();
        });
    }
}

// 템플릿 삽입 함수
window.insertQuickTemplate = function(type) {
    if (!quickPageEditor) {
        initCreateTabEditors();
        // 에디터가 초기화될 때까지 잠시 기다림
        setTimeout(() => insertQuickTemplate(type), 100);
        return;
    }
    
    let template = '';
    
    switch(type) {
        case 'multiple-choice':
            template = `<div class="question">
    <h4>문제: 다음 중 올바른 것은?</h4>
    <ol type="1">
        <li>첫 번째 보기</li>
        <li>두 번째 보기</li>
        <li>세 번째 보기</li>
        <li>네 번째 보기</li>
    </ol>
</div>`;
            break;
            
        case 'short-answer':
            template = `<div class="question">
    <h4>문제: 다음 빈칸에 알맞은 답을 쓰시오.</h4>
    <p>_________는 우리나라의 수도입니다.</p>
    <div class="answer-input">
        <label>답: <input type="text" name="answer" class="form-input" /></label>
    </div>
</div>`;
            break;
            
        case 'essay':
            template = `<div class="question">
    <h4>문제: 다음 주제에 대해 서술하시오.</h4>
    <p>민주주의의 기본 원리에 대해 설명하시오. (200자 이상)</p>
    <div class="answer-input">
        <textarea name="answer" rows="10" class="form-textarea w-full" placeholder="답안을 작성하세요..."></textarea>
    </div>
</div>`;
            break;
    }
    
    if (quickPageEditor && template) {
        quickPageEditor.setValue(template);
    }
}

// 빠른 콘텐츠 생성 폼 제출
document.addEventListener('DOMContentLoaded', function() {
    const quickForm = document.getElementById('quickContentForm');
    if (quickForm) {
        quickForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // 폼 데이터 수집
            const formData = new FormData(e.target);
            
            // 에디터의 값들을 폼데이터에 추가
            if (quickPageEditor) {
                formData.set('page', quickPageEditor.getValue());
            }
            if (quickMetaEditor) {
                formData.set('meta_data', quickMetaEditor.getValue());
            }
            if (quickTagsEditor) {
                formData.set('tags', quickTagsEditor.getValue());
            }
            
            // 유효성 검사
            if (!validateQuickContentForm(formData)) {
                return;
            }
            
            // 제출 버튼 비활성화
            const submitBtn = e.target.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>생성 중...';
            
            try {
                const response = await fetch('/teacher/contents/create/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': window.courseConfig.csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });
                
                if (response.ok) {
                    // 성공적으로 생성된 경우
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        const result = await response.json();
                        if (result.success) {
                            handleSuccessfulContentCreation(result);
                        } else {
                            throw new Error(result.message || '콘텐츠 생성에 실패했습니다.');
                        }
                    } else {
                        // 리다이렉트 응답인 경우 (성공)
                        handleSuccessfulContentCreation({
                            success: true,
                            message: '콘텐츠가 성공적으로 생성되었습니다.'
                        });
                    }
                } else {
                    // 오류 응답 처리
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.message || '콘텐츠 생성에 실패했습니다.');
                }
            } catch (error) {
                window.showMessage(error.message, 'error');
            } finally {
                // 제출 버튼 활성화
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });
    }
});

// 콘텐츠 생성 성공 처리
function handleSuccessfulContentCreation(result) {
    window.showMessage(result.message || '콘텐츠가 생성되었습니다.', 'success');
    
    // 폼 초기화
    resetQuickContentForm();
    
    // 생성된 콘텐츠가 있으면 드롭 영역에 자동 추가
    if (result.content) {
        window.addDroppedContent({
            id: result.content.id,
            title: result.content.title,
            type: result.content.content_type_display || result.content.content_type
        });
    }
    
    // 검색 탭으로 전환하여 새로 생성된 콘텐츠 확인
    setTimeout(() => {
        window.switchTab('search');
        // 최근 생성된 콘텐츠를 보기 위해 빈 검색 실행
        window.searchContents();
    }, 1000);
}

// 빠른 콘텐츠 폼 유효성 검사
function validateQuickContentForm(formData) {
    const title = formData.get('title');
    const contentType = formData.get('content_type');
    const page = formData.get('page');
    
    if (!title || title.trim().length < 2) {
        window.showMessage('제목은 2자 이상 입력해주세요.', 'error');
        document.querySelector('input[name="title"]').focus();
        return false;
    }
    
    if (!contentType) {
        window.showMessage('콘텐츠 타입을 선택해주세요.', 'error');
        document.querySelector('select[name="content_type"]').focus();
        return false;
    }
    
    if (!page || page.trim().length < 10) {
        window.showMessage('콘텐츠 내용은 10자 이상 입력해주세요.', 'error');
        if (quickPageEditor) {
            quickPageEditor.focus();
        }
        return false;
    }
    
    // JSON 형식 검증
    try {
        const metaData = formData.get('meta_data');
        if (metaData && metaData.trim()) {
            JSON.parse(metaData);
        }
        
        const tags = formData.get('tags');
        if (tags && tags.trim()) {
            JSON.parse(tags);
        }
    } catch (e) {
        window.showMessage('JSON 형식이 올바르지 않습니다: ' + e.message, 'error');
        return false;
    }
    
    return true;
}

// 빠른 콘텐츠 폼 초기화
function resetQuickContentForm() {
    const form = document.getElementById('quickContentForm');
    if (form) {
        form.reset();
        
        // 에디터들 초기화
        if (quickPageEditor) {
            quickPageEditor.setValue('');
        }
        if (quickMetaEditor) {
            quickMetaEditor.setValue('{}');
        }
        if (quickTagsEditor) {
            quickTagsEditor.setValue('{}');
        }
    }
}

// 콘텐츠 타입 변경 시 템플릿 제안
document.addEventListener('DOMContentLoaded', function() {
    const contentTypeSelect = document.getElementById('createContentType');
    if (contentTypeSelect) {
        contentTypeSelect.addEventListener('change', function() {
            const selectedType = this.selectedOptions[0];
            if (selectedType && selectedType.text) {
                const typeName = selectedType.text.toLowerCase();
                
                // 자동으로 적절한 템플릿 제안
                if (typeName.includes('객관식')) {
                    suggestTemplate('multiple-choice');
                } else if (typeName.includes('단답형')) {
                    suggestTemplate('short-answer');
                } else if (typeName.includes('서술형')) {
                    suggestTemplate('essay');
                }
            }
        });
    }
});

// 템플릿 제안
function suggestTemplate(templateType) {
    // 현재 에디터가 비어있는 경우에만 템플릿 제안
    if (quickPageEditor && (!quickPageEditor.getValue() || quickPageEditor.getValue().trim() === '')) {
        const templateNames = {
            'multiple-choice': '객관식',
            'short-answer': '단답형',
            'essay': '서술형'
        };
        
        const templateName = templateNames[templateType];
        if (templateName) {
            // 자동으로 템플릿 삽입하지 않고 사용자에게 알림
            setTimeout(() => {
                if (confirm(`${templateName} 문제 템플릿을 삽입하시겠습니까?`)) {
                    insertQuickTemplate(templateType);
                }
            }, 100);
        }
    }
}

// 콘텐츠 생성 미리보기
function previewQuickContent() {
    const title = document.querySelector('input[name="title"]').value;
    const contentType = document.querySelector('select[name="content_type"] option:checked').text;
    const page = quickPageEditor ? quickPageEditor.getValue() : '';
    const answer = document.querySelector('textarea[name="answer"]').value;
    
    if (!title && !page) {
        window.showMessage('미리볼 내용이 없습니다.', 'warning');
        return;
    }
    
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl max-w-3xl max-h-[90vh] overflow-hidden w-full">
            <div class="p-6 border-b border-gray-200">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="text-xl font-semibold">${escapeHtml(title || '제목 없음')}</h3>
                        <span class="content-type-badge badge-blue mt-2">
                            ${escapeHtml(contentType || '타입 없음')}
                        </span>
                    </div>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
            </div>
            <div class="content-preview p-6 overflow-y-auto" style="max-height: calc(90vh - 200px);">
                ${page || '<p class="text-gray-500">내용이 없습니다.</p>'}
                ${answer ? `
                    <div class="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
                        <h4 class="font-semibold text-green-800 mb-2">정답</h4>
                        <div class="text-green-700">${escapeHtml(answer)}</div>
                    </div>
                ` : ''}
            </div>
            <div class="p-6 border-t border-gray-200 flex justify-end">
                <button onclick="this.closest('.fixed').remove()" class="btn-modern btn-secondary">
                    닫기
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 모달 외부 클릭 시 닫기
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// 미리보기 버튼 추가 (선택사항)
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('quickContentForm');
    if (form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            const previewBtn = document.createElement('button');
            previewBtn.type = 'button';
            previewBtn.className = 'btn-modern btn-secondary w-full mb-2';
            previewBtn.innerHTML = '<i class="fas fa-eye mr-2"></i>미리보기';
            previewBtn.onclick = previewQuickContent;
            
            submitBtn.parentNode.insertBefore(previewBtn, submitBtn);
        }
    }
});