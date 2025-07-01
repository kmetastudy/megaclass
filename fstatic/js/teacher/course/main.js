// /static/js/teacher/course/main.js
// 메인 초기화 및 트리 관리

// 페이지 로드 시 초기화
$(document).ready(function() {
    initializeTree();
    loadCourseOverview();
});

// 트리 초기화
function initializeTree() {
    $('#courseTree').jstree({
        'core': {
            'data': function(node, cb) {
                if(node.id === "#") {
                    $.ajax({
                        url: window.courseConfig.urls.courseStructure,
                        success: function(data) {
                            cb(formatTreeData(data));
                        },
                        error: function() {
                            showError('코스 구조를 불러올 수 없습니다.');
                        }
                    });
                }
            },
            'check_callback': true,
            'themes': {
                'responsive': true,
                'variant': 'large',
                'stripes': false,
                'dots': false
            }
        },
        'types': {
            'course': {
                'icon': 'fas fa-book text-blue-600'
            },
            'chapter': {
                'icon': 'fas fa-bookmark text-green-600'
            },
            'subchapter': {
                'icon': 'fas fa-file-alt text-yellow-600'
            },
            'chasi': {
                'icon': 'fas fa-clock text-purple-600'
            }
        },
        'plugins': ['types', 'contextmenu', 'state'],
        'contextmenu': {
            'items': customContextMenu
        }
    });

    // 노드 선택 이벤트
    $('#courseTree').on('select_node.jstree', function(e, data) {
        window.currentNode = data.node;
        window.currentActiveNodeId = data.node.id;
        loadNodeContent(data.node);
    });
}

// 트리 데이터 포맷
function formatTreeData(data) {
    if (!data.structure) {
        console.error('Invalid data structure:', data);
        return [];
    }

    const structure = data.structure;
    let treeData = [{
        'id': 'course_' + structure.course.id,
        'text': structure.course.subject_name + (structure.chapters ? ` <span class="tree-count-badge">${structure.chapters.length}</span>` : ''),
        'type': 'course',
        'state': {'opened': true},
        'data': {'type': 'course', 'id': structure.course.id},
        'children': []
    }];

    if (structure.chapters) {
        structure.chapters.forEach(function(chapter) {
            const chapterChildCount = chapter.subchapters ? chapter.subchapters.length : 0;
            let chapterNode = {
                'id': 'chapter_' + chapter.id,
                'text': chapter.order + '. ' + chapter.title + (chapterChildCount > 0 ? ` <span class="tree-count-badge">${chapterChildCount}</span>` : ''),
                'type': 'chapter',
                'data': {'type': 'chapter', 'id': chapter.id},
                'li_attr': {'class': 'node-chapter'},
                'children': []
            };

            if (chapter.subchapters) {
                chapter.subchapters.forEach(function(subchapter) {
                    const subchapterChildCount = subchapter.chasis ? subchapter.chasis.length : 0;
                    let subchapterNode = {
                        'id': 'subchapter_' + subchapter.id,
                        'text': subchapter.order + '. ' + subchapter.title + (subchapterChildCount > 0 ? ` <span class="tree-count-badge">${subchapterChildCount}</span>` : ''),
                        'type': 'subchapter',
                        'data': {'type': 'subchapter', 'id': subchapter.id},
                        'li_attr': {'class': 'node-subchapter'},
                        'children': []
                    };

                    if (subchapter.chasis) {
                        subchapter.chasis.forEach(function(chasi) {
                            let chasiNode = {
                                'id': 'chasi_' + chasi.id,
                                'text': chasi.order + '. ' + chasi.title + ` <span class="tree-count-badge">${chasi.slide_count}</span>`,
                                'type': 'chasi',
                                'data': {'type': 'chasi', 'id': chasi.id},
                                'li_attr': {'class': 'node-chasi'}
                            };
                            subchapterNode.children.push(chasiNode);
                        });
                    }

                    chapterNode.children.push(subchapterNode);
                });
            }

            treeData[0].children.push(chapterNode);
        });
    }

    return treeData;
}

// 코스 개요 로드
function loadCourseOverview() {
    const html = `
        <div class="mb-8">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div class="stat-card">
                    <div class="flex items-center justify-between mb-2">
                        <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-book text-blue-600 text-xl"></i>
                        </div>
                        <span class="text-xs text-gray-500">총계</span>
                    </div>
                    <p class="text-2xl font-bold text-gray-800">${window.courseConfig.stats.totalChapters}</p>
                    <p class="text-sm text-gray-600">대단원</p>
                </div>

                <div class="stat-card">
                    <div class="flex items-center justify-between mb-2">
                        <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-file-alt text-green-600 text-xl"></i>
                        </div>
                        <span class="text-xs text-gray-500">총계</span>
                    </div>
                    <p class="text-2xl font-bold text-gray-800">${window.courseConfig.stats.totalSubchapters}</p>
                    <p class="text-sm text-gray-600">소단원</p>
                </div>

                <div class="stat-card">
                    <div class="flex items-center justify-between mb-2">
                        <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-clock text-purple-600 text-xl"></i>
                        </div>
                        <span class="text-xs text-gray-500">총계</span>
                    </div>
                    <p class="text-2xl font-bold text-gray-800">${window.courseConfig.stats.totalChasis}</p>
                    <p class="text-sm text-gray-600">차시</p>
                </div>

                <div class="stat-card">
                    <div class="flex items-center justify-between mb-2">
                        <div class="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-images text-orange-600 text-xl"></i>
                        </div>
                        <span class="text-xs text-gray-500">총계</span>
                    </div>
                    <p class="text-2xl font-bold text-gray-800">${window.courseConfig.stats.totalSlides}</p>
                    <p class="text-sm text-gray-600">슬라이드</p>
                </div>
            </div>

            <div class="flex justify-end mb-6">
                <button onclick="showAddChapterForm()" class="btn-modern btn-primary">
                    <i class="fas fa-plus"></i>
                    대단원 추가
                </button>
            </div>

            <div id="chapters-container">
                <!-- 대단원 목록이 여기에 동적으로 로드됩니다 -->
            </div>
        </div>
    `;

    $('#contentTitle').html('<i class="fas fa-home mr-2"></i>코스 개요');
    $('#contentArea').html(html);
    
    // 대단원 목록 로드
    loadChapters();
}

// 대단원 목록 로드
function loadChapters() {
    $.ajax({
        url: `/teacher/api/course/${window.courseConfig.courseId}/detail/`,
        method: 'GET',
        success: function(response) {
            if (!response.chapters || response.chapters.length === 0) {
                $('#chapters-container').html(`
                    <div class="text-center py-12 bg-gray-50 rounded-lg">
                        <i class="fas fa-folder-open text-gray-300 text-5xl mb-4"></i>
                        <p class="text-gray-500">대단원이 없습니다.</p>
                        <button onclick="showAddChapterForm()" class="mt-4 btn-modern btn-primary">
                            <i class="fas fa-plus mr-2"></i>첫 번째 대단원 추가
                        </button>
                    </div>
                `);
            }
        }
    });
}

// 컨텍스트 메뉴 커스터마이즈
function customContextMenu(node) {
    const type = node.data.type;
    const items = {};

    if (type === 'course') {
        items.addChapter = {
            label: '대단원 추가',
            action: function() { showAddChapterForm(); }
        };
    } else if (type === 'chapter') {
        items.addSubchapter = {
            label: '소단원 추가',
            action: function() { SubChapterManager.showCreateForm(node.data.id); }
        };
        items.edit = {
            label: '수정',
            action: function() { 
                loadNodeContent(node);
            }
        };
        items.delete = {
            label: '삭제',
            action: function() { ChapterManager.delete(node.data.id); }
        };
    } else if (type === 'subchapter') {
        items.addChasi = {
            label: '차시 추가',
            action: function() { ChasiManager.showCreateForm(node.data.id); }
        };
        items.edit = {
            label: '수정',
            action: function() { 
                loadNodeContent(node);
            }
        };
        items.delete = {
            label: '삭제',
            action: function() { SubChapterManager.delete(node.data.id); }
        };
    } else if (type === 'chasi') {
        items.manageSlides = {
            label: '슬라이드 관리',
            action: function() {
                window.location.href = window.courseConfig.urls.chasiSlideManage.replace('0', node.data.id);
            }
        };
        items.edit = {
            label: '수정',
            action: function() { 
                loadNodeContent(node);
            }
        };
        items.delete = {
            label: '삭제',
            action: function() { ChasiManager.delete(node.data.id); }
        };
    }

    return items;
}

// 대단원 추가 폼 표시 (전역 함수)
window.showAddChapterForm = function() {
    ChapterManager.showCreateForm();
};

// 글로벌 이벤트 핸들러 등록
$(document).on('click', '[data-action]', function(e) {
    e.preventDefault();
    const action = $(this).data('action');
    const params = $(this).data();
    
    switch(action) {
        case 'add-chapter':
            ChapterManager.showCreateForm();
            break;
        case 'add-subchapter':
            SubChapterManager.showCreateForm(params.chapterId);
            break;
        case 'add-chasi':
            ChasiManager.showCreateForm(params.subchapterId);
            break;
        case 'add-slide':
            SlideManager.addSlide(params.chasiId);
            break;
    }
});

// 키보드 단축키
$(document).on('keydown', function(e) {
    // Ctrl/Cmd + S: 저장
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const activeForm = $('form:visible').first();
        if (activeForm.length) {
            activeForm.submit();
        }
    }
    
    // ESC: 취소/닫기
    if (e.key === 'Escape') {
        const modal = $('.modal:visible').first();
        if (modal.length) {
            modal.find('[data-dismiss="modal"]').click();
        }
    }
});