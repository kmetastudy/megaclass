// static/js/super_agent/batch-tree.js
// 트리 뷰 관련 함수들

function initializeTree() {
    console.log('Tree 모듈 초기화');
    
    // 트리 토글 이벤트
    $(document).on('click', '.tree-toggle', function(e) {
        e.stopPropagation();
        const treeItem = $(this).closest('.tree-item');
        const children = treeItem.find('> .tree-children');
        
        if (children.is(':visible')) {
            children.hide();
            $(this).addClass('collapsed');
        } else {
            children.show();
            $(this).removeClass('collapsed');
        }
    });

    // 트리 아이템 클릭 이벤트 (미리보기)
    $(document).on('click', '.tree-content', function(e) {
        if ($(e.target).hasClass('tree-toggle')) {
            return;
        }
        
        // 기존 선택 해제
        $('.tree-content').removeClass('selected');
        $(this).addClass('selected');
        
        const treeItem = $(this).closest('.tree-item');
        const itemType = treeItem.data('type');
        const itemId = treeItem.data('id');
        
        if (itemType === 'slide') {
            if (typeof loadSlidePreview === 'function') {
                loadSlidePreview(itemId, treeItem.data('content-id'));
            }
        } else {
            if (typeof showDefaultPreview === 'function') {
                showDefaultPreview(itemType, treeItem.find('.tree-text').text());
            }
        }
    });
}

function renderCourseTree() {
    const tree = $('#courseTree');
    tree.empty();
    
    if (filteredCourseStructure.length === 0) {
        tree.html('<div class="text-center py-8 text-gray-500">선택된 코스가 없습니다.</div>');
        return;
    }
    
    let totalItems = 0;
    filteredCourseStructure.forEach(course => {
        const courseElement = createCourseElement(course);
        tree.append(courseElement);
        totalItems += countTreeItems(course);
    });
    
    $('#treeItemCount').text(totalItems);
}

function countTreeItems(course) {
    let count = 1; // 코스 자체
    if (course.chapters) {
        course.chapters.forEach(chapter => {
            count += 1; // 챕터
            if (chapter.subchapters) {
                chapter.subchapters.forEach(subchapter => {
                    count += 1; // 서브챕터
                    if (subchapter.chasis) {
                        count += subchapter.chasis.length; // 차시들
                        subchapter.chasis.forEach(chasi => {
                            if (chasi.slides) {
                                count += chasi.slides.length; // 슬라이드들
                            }
                        });
                    }
                });
            }
        });
    }
    return count;
}

function createCourseElement(course) {
    const hasChapters = course.chapters && course.chapters.length > 0;
    
    const element = $(`
        <div class="tree-item" data-type="course" data-id="${course.id}">
            <div class="tree-content">
                ${hasChapters ? '<i class="fas fa-chevron-down tree-toggle"></i>' : '<span style="width: 20px; display: inline-block;"></span>'}
                <i class="fas fa-book tree-icon text-purple-600"></i>
                <span class="tree-text font-semibold">${course.subject_name}</span>
                <span class="tree-badge">${course.chapters.length}</span>
            </div>
            ${hasChapters ? '<div class="tree-children"></div>' : ''}
        </div>
    `);
    
    if (hasChapters) {
        const childrenContainer = element.find('.tree-children');
        course.chapters.forEach(chapter => {
            childrenContainer.append(createChapterElement(chapter));
        });
    }
    
    return element;
}

function createChapterElement(chapter) {
    const hasSubchapters = chapter.subchapters && chapter.subchapters.length > 0;
    
    const element = $(`
        <div class="tree-item" data-type="chapter" data-id="${chapter.id}">
            <div class="tree-content">
                ${hasSubchapters ? '<i class="fas fa-chevron-down tree-toggle"></i>' : '<span style="width: 20px; display: inline-block;"></span>'}
                <i class="fas fa-folder tree-icon text-blue-600"></i>
                <span class="tree-text">${chapter.order}. ${chapter.title}</span>
                <span class="tree-badge">${chapter.subchapters.length}</span>
            </div>
            ${hasSubchapters ? '<div class="tree-children"></div>' : ''}
        </div>
    `);
    
    if (hasSubchapters) {
        const childrenContainer = element.find('.tree-children');
        chapter.subchapters.forEach(subchapter => {
            childrenContainer.append(createSubchapterElement(subchapter));
        });
    }
    
    return element;
}

function createSubchapterElement(subchapter) {
    const hasChasis = subchapter.chasis && subchapter.chasis.length > 0;
    
    const element = $(`
        <div class="tree-item" data-type="subchapter" data-id="${subchapter.id}">
            <div class="tree-content">
                ${hasChasis ? '<i class="fas fa-chevron-down tree-toggle"></i>' : '<span style="width: 20px; display: inline-block;"></span>'}
                <i class="fas fa-folder-open tree-icon text-green-600"></i>
                <span class="tree-text">${subchapter.order}. ${subchapter.title}</span>
                <span class="tree-badge">${subchapter.chasis.length}</span>
            </div>
            ${hasChasis ? '<div class="tree-children"></div>' : ''}
        </div>
    `);
    
    if (hasChasis) {
        const childrenContainer = element.find('.tree-children');
        subchapter.chasis.forEach(chasi => {
            childrenContainer.append(createChasiElement(chasi));
        });
    }
    
    return element;
}

function createChasiElement(chasi) {
    const hasSlides = chasi.slides && chasi.slides.length > 0;
    
    const element = $(`
        <div class="tree-item" data-type="chasi" data-id="${chasi.id}">
            <div class="tree-content">
                ${hasSlides ? '<i class="fas fa-chevron-down tree-toggle"></i>' : '<span style="width: 20px; display: inline-block;"></span>'}
                <i class="fas fa-book-reader tree-icon text-purple-600"></i>
                <span class="tree-text">${chasi.order}. ${chasi.title}</span>
                <span class="tree-badge">${chasi.slides.length}</span>
            </div>
            ${hasSlides ? '<div class="tree-children"></div>' : ''}
        </div>
    `);
    
    if (hasSlides) {
        const childrenContainer = element.find('.tree-children');
        chasi.slides.forEach(slide => {
            childrenContainer.append(createSlideElement(slide));
        });
    }
    
    return element;
}

function createSlideElement(slide) {
    return $(`
        <div class="tree-item" data-type="slide" data-id="${slide.id}" data-content-id="${slide.content_id || ''}">
            <div class="tree-content">
                <span style="width: 20px; display: inline-block;"></span>
                <i class="fas fa-file-alt tree-icon text-orange-600"></i>
                <span class="tree-text">${slide.slide_number}. ${slide.title}</span>
                <span class="type-badge">${slide.content_type}</span>
            </div>
        </div>
    `);
}

function updateTreeItem(chasiId, action, title, slideId) {
    const chasiElement = $(`.tree-item[data-type="chasi"][data-id="${chasiId}"] .tree-content`);
    if (chasiElement.length > 0) {
        chasiElement.addClass('processing');
        
        setTimeout(() => {
            chasiElement.removeClass('processing').addClass('updated');
            
            // 새로운 슬라이드 추가
            if (action === 'created' && slideId) {
                addNewSlideToTree(chasiId, slideId, title);
            }
            
            // 슬라이드 카운트 업데이트
            const badge = chasiElement.find('.tree-badge');
            if (badge.length > 0 && action === 'created') {
                const currentCount = parseInt(badge.text()) || 0;
                badge.text(currentCount + 1);
                badge.addClass('badge-updated');
                setTimeout(() => {
                    badge.removeClass('badge-updated');
                }, 1000);
            }
            
            setTimeout(() => {
                chasiElement.removeClass('updated');
            }, 3000);
        }, 500);
    }
}

function addNewSlideToTree(chasiId, slideId, title) {
    const chasiItem = $(`.tree-item[data-type="chasi"][data-id="${chasiId}"]`);
    let childrenContainer = chasiItem.find('> .tree-children');
    
    // children 컨테이너가 없으면 생성
    if (childrenContainer.length === 0) {
        childrenContainer = $('<div class="tree-children"></div>');
        chasiItem.append(childrenContainer);
        
        // toggle 버튼도 추가
        const toggleBtn = chasiItem.find('.tree-content');
        if (toggleBtn.find('.tree-toggle').length === 0) {
            toggleBtn.prepend('<i class="fas fa-chevron-down tree-toggle"></i>');
        }
    }
    
    // 새 슬라이드 요소 생성
    const newSlide = $(`
        <div class="tree-item" data-type="slide" data-id="${slideId}">
            <div class="tree-content">
                <span style="width: 20px; display: inline-block;"></span>
                <i class="fas fa-file-alt tree-icon text-orange-600"></i>
                <span class="tree-text">${title}</span>
                <span class="type-badge">new</span>
            </div>
        </div>
    `);
    
    childrenContainer.append(newSlide);
    
    // 애니메이션 후 일반 스타일로 변경
    setTimeout(() => {
        newSlide.find('.type-badge').text('slide');
    }, 1000);
}