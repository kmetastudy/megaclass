/**
 * 컨텐츠 라이브러리 관리 클래스
 */
class ContentLibrary {
    constructor() {
        this.config = null;
        this.currentContentId = null;
        this.init();
    }
    
    /**
     * 초기화
     */
    init() {
        try {
            // Django 데이터 로드
            const djangoDataElement = document.getElementById('django-data');
            if (djangoDataElement) {
                this.config = JSON.parse(djangoDataElement.textContent);
            }
            
            // 이벤트 리스너 등록
            this.bindEvents();
            
            console.log('ContentLibrary initialized');
        } catch (error) {
            console.error('ContentLibrary initialization failed:', error);
        }
    }
    
    /**
     * 이벤트 리스너 등록
     */
    bindEvents() {
        // 컨텐츠 생성 버튼
        const createBtn = document.getElementById('createContentBtn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.showCreateContentMessage());
        }
        
        const createEmptyBtn = document.getElementById('createContentEmptyBtn');
        if (createEmptyBtn) {
            createEmptyBtn.addEventListener('click', () => this.showCreateContentMessage());
        }
        
        // 모달 외부 클릭시 닫기
        document.addEventListener('click', (event) => {
            if (event.target.id === 'contentPreviewModal') {
                this.closeModal();
            }
            if (event.target.id === 'courseSelectModal') {
                this.closeCourseModal();
            }
        });
        
        // ESC 키로 모달 닫기
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.closeModal();
                this.closeCourseModal();
            }
        });
    }
    
    /**
     * 컨텐츠 미리보기
     */
    viewContent(contentId) {
        if (!this.config) {
            alert(this.getDefaultMessage('previewNotAvailable'));
            return;
        }
        
        this.currentContentId = contentId;
        const modal = document.getElementById('contentPreviewModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalContent = document.getElementById('modalContent');
        
        // 로딩 표시
        modalTitle.textContent = '컨텐츠 로딩 중...';
        modalContent.innerHTML = '<div class="text-center py-8"><i class="fas fa-spinner fa-spin text-2xl text-gray-400"></i></div>';
        
        // 모달 표시
        modal.classList.remove('hidden');
        
        // API 호출
        const url = this.config.urls.contentPreview.replace('CONTENT_ID', contentId);
        
        fetch(url, {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.config.csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                modalTitle.textContent = data.content.title;
                modalContent.innerHTML = this.renderContentPreview(data.content);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Content preview error:', error);
            modalTitle.textContent = '오류';
            modalContent.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-exclamation-triangle text-red-500 text-2xl mb-2"></i>
                    <p class="text-gray-600">${this.getMessage('loadingError')}</p>
                </div>
            `;
        });
    }
    
    /**
     * 컨텐츠 사용 (차시에 추가)
     */
    useContent(contentId) {
        if (!this.config) {
            alert(this.getDefaultMessage('addToChasi'));
            return;
        }
        
        this.currentContentId = contentId;
        this.loadCourseList();
    }
    
    /**
     * 코스 목록 로드
     */
    loadCourseList() {
        const modal = document.getElementById('courseSelectModal');
        const courseList = document.getElementById('courseList');
        
        // 로딩 표시
        courseList.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i> 로딩 중...</div>';
        
        // 모달 표시
        modal.classList.remove('hidden');
        
        // API 호출
        fetch(this.config.urls.courseList, {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.config.csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.renderCourseList(data.courses);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Course list error:', error);
            courseList.innerHTML = `
                <div class="text-center py-4 text-red-600">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    ${this.getMessage('loadingError')}
                </div>
            `;
        });
    }
    
    /**
     * 컨텐츠 미리보기 렌더링
     */
    renderContentPreview(content) {
        return `
            <div class="space-y-4">
                <div class="flex items-center space-x-2">
                    <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                        ${content.content_type}
                    </span>
                    <span class="text-gray-500 text-sm">${content.difficulty_level}</span>
                    <span class="text-gray-500 text-sm">${content.estimated_time}분</span>
                </div>
                
                <div class="prose max-w-none">
                    ${content.page}
                </div>
                
                ${content.tags && content.tags.length ? `
                <div class="flex flex-wrap gap-2">
                    ${content.tags.map(tag => `<span class="bg-gray-100 text-gray-600 px-2 py-1 rounded text-sm">#${tag}</span>`).join('')}
                </div>
                ` : ''}
                
                <div class="flex justify-end space-x-3 pt-4 border-t">
                    <button onclick="ContentLibrary.closeModal()" 
                            class="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400">
                        닫기
                    </button>
                    <button onclick="ContentLibrary.useContent(${content.id})" 
                            class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
                        차시에 추가
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * 코스 목록 렌더링
     */
    renderCourseList(courses) {
        const courseList = document.getElementById('courseList');
        
        if (!courses || courses.length === 0) {
            courseList.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-folder-open text-2xl mb-2"></i>
                    <p>사용 가능한 코스가 없습니다.</p>
                </div>
            `;
            return;
        }
        
        courseList.innerHTML = courses.map(course => `
            <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                 onclick="ContentLibrary.selectCourse(${course.id}, '${course.subject_name}')">
                <h4 class="font-medium text-gray-800">${course.subject_name}</h4>
                <p class="text-sm text-gray-600">${course.target}</p>
                <p class="text-xs text-gray-500 mt-1">${course.chapter_count}개 대단원</p>
            </div>
        `).join('');
    }
    
    /**
     * 코스 선택
     */
    selectCourse(courseId, courseName) {
        // 여기서 실제로는 차시 목록을 보여줘야 하지만, 
        // 간단히 처리하기 위해 확인 메시지만 표시
        if (confirm(`"${courseName}" 코스의 차시에 이 컨텐츠를 추가하시겠습니까?`)) {
            this.addContentToChasi(courseId);
        }
    }
    
    /**
     * 차시에 컨텐츠 추가
     */
    addContentToChasi(courseId) {
        fetch(this.config.urls.addToChasi, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.config.csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content_id: this.currentContentId,
                course_id: courseId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(this.getMessage('addSuccess'));
                this.closeCourseModal();
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Add content error:', error);
            alert(this.getMessage('addError'));
        });
    }
    
    /**
     * 컨텐츠 생성 메시지 표시
     */
    showCreateContentMessage() {
        alert(this.getMessage('createContentNotAvailable'));
    }
    
    /**
     * 미리보기 모달 닫기
     */
    closeModal() {
        const modal = document.getElementById('contentPreviewModal');
        modal.classList.add('hidden');
    }
    
    /**
     * 코스 선택 모달 닫기
     */
    closeCourseModal() {
        const modal = document.getElementById('courseSelectModal');
        modal.classList.add('hidden');
    }
    
    /**
     * 메시지 가져오기
     */
    getMessage(key) {
        return this.config?.messages?.[key] || this.getDefaultMessage(key);
    }
    
    /**
     * 기본 메시지 가져오기
     */
    getDefaultMessage(key) {
        const defaultMessages = {
            createContentNotAvailable: '컨텐츠 제작은 CP 앱에서 가능합니다.',
            previewNotAvailable: '미리보기 기능을 준비 중입니다.',
            addToChasi: '차시에 컨텐츠를 추가하시겠습니까?',
            selectChasi: '컨텐츠를 추가할 차시를 선택하세요.',
            loadingError: '데이터를 불러오는 중 오류가 발생했습니다.',
            addSuccess: '컨텐츠가 성공적으로 추가되었습니다.',
            addError: '컨텐츠 추가 중 오류가 발생했습니다.'
        };
        
        return defaultMessages[key] || '알 수 없는 오류가 발생했습니다.';
    }
}

// 전역 ContentLibrary 인스턴스 생성
window.ContentLibrary = new ContentLibrary();

// DOM 로드 완료 후 초기화
document.addEventListener('DOMContentLoaded', function() {
    if (!window.ContentLibrary.config) {
        window.ContentLibrary.init();
    }
});