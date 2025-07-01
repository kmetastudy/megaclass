// static/js/teacher/course/onepage-tree.js
// 트리 구조 관리 및 노드 로딩

// 트리 상태 관리
const treeState = {
    expandedNodes: new Set(),
    selectedNode: null,
    loadingNodes: new Set()
};

// 코스 구조 로드
window.loadCourseStructure = async function() {
    const container = document.getElementById('chapters-container');
    if (!container) return;
    
    try {
        // 로딩 상태 표시
        container.innerHTML = `
            <div class="text-center py-4 text-gray-500">
                <i class="fas fa-spinner fa-spin mr-2"></i>
                <p>로딩 중...</p>
            </div>
        `;
        
        const response = await fetch(window.courseConfig.urls.courseStructure, {
            headers: {
                'X-CSRFToken': window.courseConfig.csrfToken
            }
        });
        
        if (!response.ok) {
            throw new Error('코스 구조를 불러올 수 없습니다.');
        }
        
        const data = await response.json();
        window.structureData = data;
        
        renderTreeStructure(data);
        
    } catch (error) {
        console.error('코스 구조 로드 오류:', error);
        container.innerHTML = `
            <div class="text-center py-4 text-red-500">
                <i class="fas fa-exclamation-circle mr-2"></i>
                <p>구조 로드 실패</p>
                <button onclick="loadCourseStructure()" class="mt-2 text-blue-600 hover:text-blue-800">
                    다시 시도
                </button>
            </div>
        `;
    }
};

// 트리 구조 렌더링
function renderTreeStructure(data) {
    const container = document.getElementById('chapters-container');
    if (!container || !data.structure) return;
    
    const structure = data.structure;
    
    if (!structure.chapters || structure.chapters.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-folder-open text-4xl mb-4"></i>
                <p class="mb-4">대단원이 없습니다.</p>
                <button onclick="showCreateChapterForm()" class="btn-modern btn-primary">
                    <i class="fas fa-plus mr-2"></i>첫 번째 대단원 추가
                </button>
            </div>
        `;
        return;
    }
    
    const chaptersHtml = structure.chapters.map(chapter => renderChapterNode(chapter)).join('');
    container.innerHTML = chaptersHtml;
    
    // 이벤트 리스너 등록
    setupTreeEventListeners();
}

// 대단원 노드 렌더링
function renderChapterNode(chapter) {
    const isExpanded = treeState.expandedNodes.has(`chapter_${chapter.id}`);
    const hasSubchapters = chapter.subchapters && chapter.subchapters.length > 0;
    
    return `
        <div class="tree-item" data-type="chapter" data-id="${chapter.id}">
            ${hasSubchapters ? `
                <span class="tree-toggle ${isExpanded ? '' : 'collapsed'}" 
                      onclick="toggleTreeNode('chapter_${chapter.id}')">
                    <i class="fas fa-chevron-down"></i>
                </span>
            ` : '<span class="tree-toggle" style="visibility: hidden;"><i class="fas fa-chevron-down"></i></span>'}
            
            <div class="tree-content" onclick="selectTreeNode('chapter', ${chapter.id})">
                <i class="fas fa-bookmark tree-icon text-green-600"></i>
                <span class="tree-text">${escapeHtml(chapter.title)}</span>
                <span class="tree-badge">${chapter.subchapters ? chapter.subchapters.length : 0}</span>
            </div>
            
            ${hasSubchapters ? `
                <div class="tree-children" style="display: ${isExpanded ? 'block' : 'none'};">
                    ${chapter.subchapters.map(subchapter => renderSubchapterNode(subchapter)).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// 소단원 노드 렌더링
function renderSubchapterNode(subchapter) {
    const isExpanded = treeState.expandedNodes.has(`subchapter_${subchapter.id}`);
    const hasChasis = subchapter.chasis && subchapter.chasis.length > 0;
    
    return `
        <div class="tree-item" data-type="subchapter" data-id="${subchapter.id}">
            ${hasChasis ? `
                <span class="tree-toggle ${isExpanded ? '' : 'collapsed'}" 
                      onclick="toggleTreeNode('subchapter_${subchapter.id}')">
                    <i class="fas fa-chevron-down"></i>
                </span>
            ` : '<span class="tree-toggle" style="visibility: hidden;"><i class="fas fa-chevron-down"></i></span>'}
            
            <div class="tree-content" onclick="selectTreeNode('subchapter', ${subchapter.id})">
                <i class="fas fa-file-alt tree-icon text-yellow-600"></i>
                <span class="tree-text">${escapeHtml(subchapter.title)}</span>
                <span class="tree-badge">${subchapter.chasis ? subchapter.chasis.length : 0}</span>
            </div>
            
            ${hasChasis ? `
                <div class="tree-children" style="display: ${isExpanded ? 'block' : 'none'};">
                    ${subchapter.chasis.map(chasi => renderChasiNode(chasi)).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// 차시 노드 렌더링
function renderChasiNode(chasi) {
    return `
        <div class="tree-item" data-type="chasi" data-id="${chasi.id}">
            <span class="tree-toggle" style="visibility: hidden;">
                <i class="fas fa-chevron-down"></i>
            </span>
            
            <div class="tree-content" onclick="selectTreeNode('chasi', ${chasi.id})">
                <i class="fas fa-clock tree-icon text-purple-600"></i>
                <span class="tree-text">${escapeHtml(chasi.title)}</span>
                <span class="tree-badge">${chasi.slide_count || 0}</span>
            </div>
        </div>
    `;
}

// 트리 노드 토글
window.toggleTreeNode = function(nodeId) {
    const toggle = document.querySelector(`[onclick="toggleTreeNode('${nodeId}')"]`);
    const children = toggle.parentElement.querySelector('.tree-children');
    
    if (!children) return;
    
    const isExpanded = !toggle.classList.contains('collapsed');
    
    if (isExpanded) {
        // 접기
        toggle.classList.add('collapsed');
        children.style.display = 'none';
        treeState.expandedNodes.delete(nodeId);
    } else {
        // 펼치기
        toggle.classList.remove('collapsed');
        children.style.display = 'block';
        treeState.expandedNodes.add(nodeId);
    }
};

// 트리 노드 선택
window.selectTreeNode = function(type, id) {
    // 이전 선택 해제
    document.querySelectorAll('.tree-content.selected').forEach(el => {
        el.classList.remove('selected');
    });
    
    // 새로운 선택
    const nodeElement = document.querySelector(`[data-type="${type}"][data-id="${id}"] .tree-content`);
    if (nodeElement) {
        nodeElement.classList.add('selected');
        treeState.selectedNode = { type, id };
        window.currentActiveNodeId = `${type}_${id}`;
        
        // 노드 콘텐츠 로드
        loadNodeContent(type, id);
    }
};

// 노드 콘텐츠 로드
async function loadNodeContent(type, id) {
    const contentArea = document.getElementById('contentArea');
    const contentTitle = document.getElementById('contentTitle');
    
    // 로딩 상태 표시
    contentArea.innerHTML = `
        <div class="flex items-center justify-center py-12">
            <div class="text-center">
                <div class="loading-spinner mx-auto mb-4"></div>
                <p class="text-gray-600">로딩 중...</p>
            </div>
        </div>
    `;
    
    try {
        let data;
        let titleText;
        
        switch (type) {
            case 'course':
                loadCourseOverview();
                return;
                
            case 'chapter':
                data = await apiRequest(`/teacher/api/chapter/${id}/detail/`);
                titleText = `<i class="fas fa-bookmark mr-2"></i>대단원: ${data.chapter_title}`;
                renderChapterDetail(data);
                break;
                
            case 'subchapter':
                data = await apiRequest(`/teacher/api/subchapter/${id}/detail/`);
                titleText = `<i class="fas fa-file-alt mr-2"></i>소단원: ${data.sub_chapter_title}`;
                renderSubchapterDetail(data);
                break;
                
            case 'chasi':
                data = await apiRequest(`/teacher/api/chasi/${id}/detail/`);
                titleText = `<i class="fas fa-clock mr-2"></i>차시: ${data.chasi_title}`;
                renderChasiDetail(data);
                break;
                
            default:
                throw new Error('알 수 없는 노드 타입입니다.');
        }
        
        if (titleText) {
            contentTitle.innerHTML = titleText;
        }
        
    } catch (error) {
        console.error('노드 콘텐츠 로드 오류:', error);
        contentArea.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-exclamation-circle text-red-500 text-5xl mb-4"></i>
                <p class="text-gray-700 mb-2">콘텐츠를 불러올 수 없습니다.</p>
                <p class="text-sm text-gray-500">${error.message}</p>
                <button onclick="loadNodeContent('${type}', ${id})" 
                        class="mt-4 btn-modern btn-secondary">
                    다시 시도
                </button>
            </div>
        `;
    }
}

// 코스 개요 로드
function loadCourseOverview() {
    const contentTitle = document.getElementById('contentTitle');
    const contentArea = document.getElementById('contentArea');
    
    contentTitle.innerHTML = '<i class="fas fa-home mr-2"></i>코스 개요';
    
    const html = `
        <div class="space-y-6">
            <!-- 통계 카드들 -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div class="flex items-center justify-between mb-4">
                        <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-bookmark text-blue-600 text-xl"></i>
                        </div>
                    </div>
                    <p class="text-2xl font-bold text-gray-800">${window.courseConfig.stats.totalChapters}</p>
                    <p class="text-sm text-gray-600">대단원</p>
                </div>
                
                <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div class="flex items-center justify-between mb-4">
                        <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-file-alt text-green-600 text-xl"></i>
                        </div>
                    </div>
                    <p class="text-2xl font-bold text-gray-800">${window.courseConfig.stats.totalSubchapters}</p>
                    <p class="text-sm text-gray-600">소단원</p>
                </div>
                
                <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div class="flex items-center justify-between mb-4">
                        <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-clock text-purple-600 text-xl"></i>
                        </div>
                    </div>
                    <p class="text-2xl font-bold text-gray-800">${window.courseConfig.stats.totalChasis}</p>
                    <p class="text-sm text-gray-600">차시</p>
                </div>
                
                <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div class="flex items-center justify-between mb-4">
                        <div class="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                            <i class="fas fa-images text-orange-600 text-xl"></i>
                        </div>
                    </div>
                    <p class="text-2xl font-bold text-gray-800">${window.courseConfig.stats.totalSlides}</p>
                    <p class="text-sm text-gray-600">슬라이드</p>
                </div>
            </div>
            
            <!-- 빠른 액션 -->
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 class="text-lg font-semibold text-gray-800 mb-4">빠른 작업</h3>
                <div class="flex flex-wrap gap-3">
                    <button onclick="showCreateChapterForm()" class="btn-modern btn-primary">
                        <i class="fas fa-plus mr-2"></i>대단원 추가
                    </button>
                    <button onclick="window.toggleContentsPanel()" class="btn-modern btn-secondary">
                        <i class="fas fa-database mr-2"></i>콘텐츠 라이브러리
                    </button>
                    <a href="${window.courseConfig.urls.contentsCreate}" target="_blank" class="btn-modern btn-secondary">
                        <i class="fas fa-plus-circle mr-2"></i>새 콘텐츠 만들기
                    </a>
                </div>
            </div>
            
            <!-- 최근 활동 -->
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 class="text-lg font-semibold text-gray-800 mb-4">코스 구조</h3>
                <p class="text-gray-600 mb-4">왼쪽 트리에서 대단원, 소단원, 차시를 선택하여 상세 정보를 확인하고 관리할 수 있습니다.</p>
                
                ${window.structureData && window.structureData.structure.chapters && window.structureData.structure.chapters.length > 0 ? `
                    <div class="space-y-2">
                        ${window.structureData.structure.chapters.slice(0, 3).map(chapter => `
                            <div class="p-3 bg-gray-50 rounded cursor-pointer hover:bg-gray-100" 
                                 onclick="selectTreeNode('chapter', ${chapter.id})">
                                <div class="flex items-center justify-between">
                                    <span class="font-medium">${escapeHtml(chapter.title)}</span>
                                    <span class="text-sm text-gray-500">${chapter.subchapters ? chapter.subchapters.length : 0}개 소단원</span>
                                </div>
                            </div>
                        `).join('')}
                        ${window.structureData.structure.chapters.length > 3 ? `
                            <p class="text-sm text-gray-500 text-center">외 ${window.structureData.structure.chapters.length - 3}개 더...</p>
                        ` : ''}
                    </div>
                ` : `
                    <p class="text-gray-500 text-center py-4">아직 생성된 대단원이 없습니다.</p>
                `}
            </div>
        </div>
    `;
    
    contentArea.innerHTML = html;
}

// 대단원 상세 렌더링
function renderChapterDetail(data) {
    const contentArea = document.getElementById('contentArea');
    
    const html = `
        <div class="space-y-6">
            <!-- 대단원 정보 카드 -->
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-800">대단원 정보</h3>
                    <div class="flex space-x-2">
                        <button onclick="editChapter(${data.id})" class="btn-modern btn-secondary">
                            <i class="fas fa-edit mr-2"></i>수정
                        </button>
                        <button onclick="deleteChapter(${data.id})" class="btn-modern btn-danger">
                            <i class="fas fa-trash mr-2"></i>삭제
                        </button>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">대단원명</label>
                        <p class="text-gray-900">${escapeHtml(data.chapter_title)}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">순서</label>
                        <p class="text-gray-900">${data.chapter_order}</p>
                    </div>
                    ${data.description ? `
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium text-gray-700 mb-1">설명</label>
                            <p class="text-gray-900">${escapeHtml(data.description)}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- 소단원 목록 -->
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-800">소단원 목록</h3>
                    <button onclick="showCreateSubchapterForm(${data.id})" class="btn-modern btn-primary">
                        <i class="fas fa-plus mr-2"></i>소단원 추가
                    </button>
                </div>
                
                ${data.subchapters && data.subchapters.length > 0 ? `
                    <div class="space-y-3">
                        ${data.subchapters.map(subchapter => `
                            <div class="p-4 border border-gray-200 rounded-lg hover:shadow-sm transition cursor-pointer"
                                 onclick="selectTreeNode('subchapter', ${subchapter.id})">
                                <div class="flex items-center justify-between">
                                    <div>
                                        <h4 class="font-medium text-gray-800">${subchapter.order}. ${escapeHtml(subchapter.title)}</h4>
                                        <p class="text-sm text-gray-600 mt-1">
                                            <i class="fas fa-clock mr-1"></i>${subchapter.chasi_count || 0}개 차시
                                        </p>
                                    </div>
                                    <div class="flex space-x-2">
                                        <button onclick="event.stopPropagation(); editSubchapter(${subchapter.id})" 
                                                class="text-blue-600 hover:text-blue-800">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button onclick="event.stopPropagation(); deleteSubchapter(${subchapter.id})" 
                                                class="text-red-600 hover:text-red-800">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <div class="text-center py-8 bg-gray-50 rounded-lg">
                        <i class="fas fa-folder-open text-gray-300 text-4xl mb-4"></i>
                        <p class="text-gray-500 mb-4">소단원이 없습니다.</p>
                        <button onclick="showCreateSubchapterForm(${data.id})" class="btn-modern btn-primary">
                            첫 번째 소단원 추가
                        </button>
                    </div>
                `}
            </div>
        </div>
    `;
    
    contentArea.innerHTML = html;
}

// 소단원 상세 렌더링
function renderSubchapterDetail(data) {
    const contentArea = document.getElementById('contentArea');
    
    const html = `
        <div class="space-y-6">
            <!-- 소단원 정보 카드 -->
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-800">소단원 정보</h3>
                    <div class="flex space-x-2">
                        <button onclick="editSubchapter(${data.id})" class="btn-modern btn-secondary">
                            <i class="fas fa-edit mr-2"></i>수정
                        </button>
                        <button onclick="deleteSubchapter(${data.id})" class="btn-modern btn-danger">
                            <i class="fas fa-trash mr-2"></i>삭제
                        </button>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">소단원명</label>
                        <p class="text-gray-900">${escapeHtml(data.sub_chapter_title)}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">순서</label>
                        <p class="text-gray-900">${data.sub_chapter_order}</p>
                    </div>
                    ${data.description ? `
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium text-gray-700 mb-1">설명</label>
                            <p class="text-gray-900">${escapeHtml(data.description)}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- 차시 목록 -->
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-800">차시 목록</h3>
                    <button onclick="showCreateChasiForm(${data.id})" class="btn-modern btn-primary">
                        <i class="fas fa-plus mr-2"></i>차시 추가
                    </button>
                </div>
                
                ${data.chasis && data.chasis.length > 0 ? `
                    <div class="space-y-3">
                        ${data.chasis.map(chasi => `
                            <div class="p-4 border border-gray-200 rounded-lg hover:shadow-sm transition cursor-pointer"
                                 onclick="selectTreeNode('chasi', ${chasi.id})">
                                <div class="flex items-center justify-between">
                                    <div>
                                        <h4 class="font-medium text-gray-800">${chasi.order}. ${escapeHtml(chasi.title)}</h4>
                                        <div class="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                                            <span><i class="fas fa-images mr-1"></i>${chasi.slide_count || 0}개 슬라이드</span>
                                            <span><i class="fas fa-clock mr-1"></i>${chasi.duration_minutes}분</span>
                                        </div>
                                    </div>
                                    <div class="flex space-x-2">
                                        <a href="${window.courseConfig.urls.chasiSlideManage.replace('0', chasi.id)}" 
                                           onclick="event.stopPropagation()"
                                           class="text-green-600 hover:text-green-800">
                                            <i class="fas fa-images"></i>
                                        </a>
                                        <button onclick="event.stopPropagation(); editChasi(${chasi.id})" 
                                                class="text-blue-600 hover:text-blue-800">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button onclick="event.stopPropagation(); deleteChasi(${chasi.id})" 
                                                class="text-red-600 hover:text-red-800">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <div class="text-center py-8 bg-gray-50 rounded-lg">
                        <i class="fas fa-clock text-gray-300 text-4xl mb-4"></i>
                        <p class="text-gray-500 mb-4">차시가 없습니다.</p>
                        <button onclick="showCreateChasiForm(${data.id})" class="btn-modern btn-primary">
                            첫 번째 차시 추가
                        </button>
                    </div>
                `}
            </div>
        </div>
    `;
    
    contentArea.innerHTML = html;
}

// 차시 상세 렌더링  
function renderChasiDetail(data) {
    const contentArea = document.getElementById('contentArea');
    
    const html = `
        <div class="space-y-6">
            <!-- 차시 정보 카드 -->
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-800">차시 정보</h3>
                    <div class="flex space-x-2">
                        <a href="${window.courseConfig.urls.chasiSlideManage.replace('0', data.id)}" 
                           class="btn-modern btn-primary">
                            <i class="fas fa-images mr-2"></i>슬라이드 관리
                        </a>
                        <button onclick="editChasi(${data.id})" class="btn-modern btn-secondary">
                            <i class="fas fa-edit mr-2"></i>수정
                        </button>
                        <button onclick="deleteChasi(${data.id})" class="btn-modern btn-danger">
                            <i class="fas fa-trash mr-2"></i>삭제
                        </button>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">차시명</label>
                        <p class="text-gray-900">${escapeHtml(data.chasi_title)}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">순서</label>
                        <p class="text-gray-900">${data.chasi_order}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">수업시간</label>
                        <p class="text-gray-900">${data.duration_minutes}분</p>
                    </div>
                    ${data.learning_objectives ? `
                        <div class="md:col-span-3">
                            <label class="block text-sm font-medium text-gray-700 mb-1">학습목표</label>
                            <p class="text-gray-900">${escapeHtml(data.learning_objectives)}</p>
                        </div>
                    ` : ''}
                    ${data.description ? `
                        <div class="md:col-span-3">
                            <label class="block text-sm font-medium text-gray-700 mb-1">설명</label>
                            <p class="text-gray-900">${escapeHtml(data.description)}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- 슬라이드 미리보기 -->
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-800">
                        슬라이드 미리보기 
                        <span class="text-sm text-gray-500 ml-2">(${data.slides ? data.slides.length : 0}개)</span>
                    </h3>
                </div>
                
                ${data.slides && data.slides.length > 0 ? `
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        ${data.slides.slice(0, 6).map((slide, index) => `
                            <div class="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                                        슬라이드 ${index + 1}
                                    </span>
                                    <span class="text-xs text-gray-500">${slide.estimated_time || 5}분</span>
                                </div>
                                <h5 class="font-medium text-gray-800 text-sm mb-1">
                                    ${escapeHtml(slide.content_title || slide.slide_title)}
                                </h5>
                                <p class="text-xs text-gray-600">
                                    ${escapeHtml(slide.content_type || '콘텐츠')}
                                </p>
                            </div>
                        `).join('')}
                        ${data.slides.length > 6 ? `
                            <div class="border border-gray-200 rounded-lg p-4 flex items-center justify-center bg-gray-50">
                                <p class="text-sm text-gray-500">외 ${data.slides.length - 6}개 더...</p>
                            </div>
                        ` : ''}
                    </div>
                ` : `
                    <div class="text-center py-8 bg-gray-50 rounded-lg">
                        <i class="fas fa-images text-gray-300 text-4xl mb-4"></i>
                        <p class="text-gray-500 mb-4">슬라이드가 없습니다.</p>
                        <a href="${window.courseConfig.urls.chasiSlideManage.replace('0', data.id)}" 
                           class="btn-modern btn-primary">
                            슬라이드 추가하기
                        </a>
                    </div>
                `}
            </div>
        </div>
    `;
    
    contentArea.innerHTML = html;
}

// 트리 이벤트 리스너 설정
function setupTreeEventListeners() {
    // 이미 HTML에서 onclick으로 처리됨
}

// 생성 폼 함수들 (전역으로 노출)
window.showCreateChapterForm = function() {
    window.showMessage('대단원 생성 기능은 준비 중입니다.', 'info');
};

window.showCreateSubchapterForm = function(chapterId) {
    window.showMessage('소단원 생성 기능은 준비 중입니다.', 'info');
};

window.showCreateChasiForm = function(subchapterId) {
    window.showMessage('차시 생성 기능은 준비 중입니다.', 'info');
};

// 편집/삭제 함수들 (전역으로 노출)
window.editChapter = function(id) {
    window.showMessage('대단원 편집 기능은 준비 중입니다.', 'info');
};

window.deleteChapter = function(id) {
    if (confirm('정말 이 대단원을 삭제하시겠습니까?\n하위의 모든 소단원과 차시도 함께 삭제됩니다.')) {
        window.showMessage('대단원 삭제 기능은 준비 중입니다.', 'info');
    }
};

window.editSubchapter = function(id) {
    window.showMessage('소단원 편집 기능은 준비 중입니다.', 'info');
};

window.deleteSubchapter = function(id) {
    if (confirm('정말 이 소단원을 삭제하시겠습니까?\n하위의 모든 차시도 함께 삭제됩니다.')) {
        window.showMessage('소단원 삭제 기능은 준비 중입니다.', 'info');
    }
};

window.editChasi = function(id) {
    window.showMessage('차시 편집 기능은 준비 중입니다.', 'info');
};

window.deleteChasi = function(id) {
    if (confirm('정말 이 차시를 삭제하시겠습니까?\n모든 슬라이드도 함께 삭제됩니다.')) {
        window.showMessage('차시 삭제 기능은 준비 중입니다.', 'info');
    }
};