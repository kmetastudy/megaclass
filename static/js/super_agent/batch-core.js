// static/js/super_agent/batch-core.js
// 핵심 변수 및 초기화 함수들

// 전역 변수들
let uploadedFiles = [];
let allUploadedData = [];
let isProcessing = false;
let isPaused = false;
let currentIndex = 0;
let processResults = [];
let courseStructure = {};
let selectedCourseId = null;
let filteredCourseStructure = [];
let currentSlideData = null;
let isEditMode = false;
let currentEditingImage = null;
let isContentPanelHidden = false;
let htmlEditor = null;
let answerEditor = null;
let lastScrollY = 0;

// 고급 편집기 전역 변수
let isInsertMode = false;
let insertType = '';
let isResizing = false;
let resizeStartX = 0;
let resizeStartY = 0;
let resizeBox = null;
let currentImagePlaceholder = null;
let uploadedAttachments = new Set(); // 업로드된 첨부파일 ID 추적

// 변경 추적을 위한 변수들
let originalHtmlContent = '';
let originalAnswerContent = '';
let changedElements = new Set();

// CSRF 토큰 가져오기
const csrfToken = window.CSRF_TOKEN || '';

// 페이지 로드 시 초기화
$(document).ready(function() {
    initializeCore();
});

function initializeCore() {
    console.log('Batch Core 초기화 시작');
    
    initializeEventHandlers();
    initializeEditors();
    initializeScrollHandler();
    initializeRestoreButton();
    
    // 다른 모듈의 초기화 함수들 호출
    if (typeof initializeUpload === 'function') {
        initializeUpload();
    }
    if (typeof initializeTree === 'function') {
        initializeTree();
    }
    if (typeof initializePreview === 'function') {
        initializePreview();
    }
    if (typeof initializeAdvancedEditor === 'function') {
        initializeAdvancedEditor();
    }
    
    // 코스 구조 로딩
    loadCourseStructure();
    
    console.log('Batch Core 초기화 완료');
}

function initializeRestoreButton() {
    // 페이지 로드 시 복구 버튼 숨김
    const restoreBtn = document.getElementById('restoreBtn');
    const toggleBtn = document.getElementById('contentToggle');
    if (restoreBtn) {
        restoreBtn.style.display = 'none';
    }
    if (toggleBtn) {
        toggleBtn.style.display = 'block';
    }
}

function initializeScrollHandler() {
    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        const header = document.getElementById('pageHeader');
        
        if (currentScrollY > lastScrollY && currentScrollY > 100) {
            // 스크롤 다운 시 헤더 숨김
            header.classList.add('hidden');
        } else {
            // 스크롤 업 시 헤더 보임
            header.classList.remove('hidden');
        }
        
        lastScrollY = currentScrollY;
    });
}

function initializeEditors() {
    // HTML 에디터 초기화
    if (document.getElementById('htmlEditorContainer')) {
        htmlEditor = CodeMirror(document.getElementById('htmlEditorContainer'), {
            mode: 'xml',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            autoCloseTags: true,
            matchBrackets: true,
            indentUnit: 2,
            smartIndent: true,
            value: '',
            styleActiveLine: true,
            foldGutter: true,
            gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
            extraKeys: {
                "Ctrl-Space": "autocomplete",
                "Ctrl-S": function(cm) {
                    if (typeof saveHtmlContent === 'function') {
                        saveHtmlContent();
                    }
                },
                "Ctrl-Alt-F": function(cm) {
                    if (typeof formatHtmlCode === 'function') {
                        formatHtmlCode();
                    }
                }
            }
        });
        
        // 에디터 변경 감지
        htmlEditor.on('change', function(cm, change) {
            if (originalHtmlContent && cm.getValue() !== originalHtmlContent) {
                markContentAsChanged('html');
            }
        });
    }
    
    // 정답 에디터 초기화
    if (document.getElementById('answerEditorContainer')) {
        answerEditor = CodeMirror(document.getElementById('answerEditorContainer'), {
            mode: 'javascript',
            theme: 'material',
            lineNumbers: true,
            lineWrapping: true,
            matchBrackets: true,
            autoCloseBrackets: true,
            indentUnit: 2,
            smartIndent: true,
            value: '{}',
            styleActiveLine: true,
            foldGutter: true,
            gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
            extraKeys: {
                "Ctrl-Space": "autocomplete",
                "Ctrl-S": function(cm) {
                    if (typeof saveAnswerData === 'function') {
                        saveAnswerData();
                    }
                },
                "Ctrl-Alt-F": function(cm) {
                    if (typeof formatAnswerCode === 'function') {
                        formatAnswerCode();
                    }
                }
            }
        });
        
        // 에디터 변경 감지
        answerEditor.on('change', function(cm, change) {
            if (originalAnswerContent && cm.getValue() !== originalAnswerContent) {
                markContentAsChanged('answer');
            }
        });
    }
}

function markContentAsChanged(type) {
    changedElements.add(type);
    // 시각적 표시는 저장 완료 후에만 적용
}

function initializeEventHandlers() {
    // 코스 선택 변경
    $('#courseSelect').on('change', function() {
        selectedCourseId = $(this).val() || null;
        filterCourseStructure();
        if (typeof renderCourseTree === 'function') {
            renderCourseTree();
        }
    });
    
    // 이미지 업로드 이벤트
    $('#imageUpload').on('change', function(e) {
        const file = e.target.files[0];
        if (file && currentImagePlaceholder) {
            if (typeof uploadAdvancedImage === 'function') {
                uploadAdvancedImage(file, currentImagePlaceholder);
            }
        } else if (file && currentEditingImage) {
            if (typeof uploadImage === 'function') {
                uploadImage(file, currentEditingImage);
            }
        }
        $(this).val('');
    });
}

// 패널 관리 함수들
function hideContentPanel() {
    const contentPanel = document.getElementById('contentPanel');
    const treePanel = document.getElementById('treePanel');
    const previewPanel = document.getElementById('previewPanel');
    const toggleBtn = document.getElementById('contentToggle');
    const restoreBtn = document.getElementById('restoreBtn');
    
    isContentPanelHidden = true;
    contentPanel.classList.add('hidden');
    treePanel.classList.add('expanded');
    previewPanel.classList.add('expanded');
    
    toggleBtn.innerHTML = '<i class="fas fa-eye"></i> 보이기';
    toggleBtn.style.display = 'none'; // 숨기기 버튼 숨김
    restoreBtn.style.display = 'block'; // 복구 버튼 표시
}

function showContentPanel() {
    const contentPanel = document.getElementById('contentPanel');
    const treePanel = document.getElementById('treePanel');
    const previewPanel = document.getElementById('previewPanel');
    const toggleBtn = document.getElementById('contentToggle');
    const restoreBtn = document.getElementById('restoreBtn');
    
    isContentPanelHidden = false;
    contentPanel.classList.remove('hidden');
    treePanel.classList.remove('expanded');
    previewPanel.classList.remove('expanded');
    
    toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i> 숨기기';
    toggleBtn.style.display = 'block'; // 숨기기 버튼 표시
    restoreBtn.style.display = 'none'; // 복구 버튼 숨김
}

function toggleContentPanel() {
    if (isContentPanelHidden) {
        showContentPanel();
    } else {
        hideContentPanel();
    }
}

// 코스 구조 관련 함수들
function filterCourseStructure() {
    if (!selectedCourseId) {
        filteredCourseStructure = courseStructure;
    } else {
        filteredCourseStructure = courseStructure.filter(course => 
            course.id.toString() === selectedCourseId
        );
    }
}

function loadCourseStructure() {
    $.ajax({
        url: "/agent/api/courses/structure/",
        type: 'GET',
        success: function(response) {
            if (response.success) {
                courseStructure = response.courses;
                filterCourseStructure();
                if (typeof renderCourseTree === 'function') {
                    renderCourseTree();
                }
            } else {
                $('#courseTree').html('<div class="text-center py-8 text-red-500">구조를 불러올 수 없습니다.</div>');
            }
        },
        error: function() {
            $('#courseTree').html('<div class="text-center py-8 text-red-500">네트워크 오류가 발생했습니다.</div>');
        }
    });
}

// 유틸리티 함수들
function refreshTree() {
    loadCourseStructure();
}

function downloadSample() {
    const sampleData = [
        {
            "course": "진로와 직업 ㉮",
            "chasi": "2. 자기 개발",
            "type": "ox",
            "page": "<div>강점은 뛰어난 능력이나 좋은 태도와 같은 긍정적인 특성입니다.</div>",
            "answer": {"answer": "1", "solution": "강점은 남보다 뛰어나거나 잘하는 점을 의미합니다."}
        },
        {
            "course": "진로와 직업 ㉮", 
            "chasi": "2. 자기 개발",
            "type": "choice",
            "page": "<div>커피나 음료를 만드는 직업을 무엇이라고 부를까요?</div>",
            "answer": {"answer": "1", "solution": "바리스타는 커피 전문가입니다."}
        },
        {
            "course": "진로와 직업 ㉮", 
            "chasi": "2. 자기 개발",
            "type": "drag-1",
            "page": "<div>빈칸 채우기 형태의 드래그 문제</div>",
            "answer": {"zone1": "1", "solution": "드래그 문제 해설"}
        },
        {
            "course": "진로와 직업 ㉮", 
            "chasi": "2. 자기 개발",
            "type": "drag-2",
            "page": "<div>순서 배열 형태의 드래그 문제</div>",
            "answer": {"order1": "2", "order2": "1", "order3": "3", "solution": "순서 문제 해설"}
        }
    ];
    
    const dataStr = JSON.stringify(sampleData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'sample_questions.json';
    link.click();
    URL.revokeObjectURL(url);
}

// 전역 함수로 노출
window.toggleContentPanel = toggleContentPanel;
window.showContentPanel = showContentPanel;
window.refreshTree = refreshTree;
window.downloadSample = downloadSample;