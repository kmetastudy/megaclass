/**
 * PAPS 측정 화면 공통 함수 모듈
 * 모든 측정 템플릿에서 공통으로 사용되는 함수들
 */

// 토스트 메시지 표시 함수
export function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        console.warn('Toast container not found');
        return;
    }

    const toast = document.createElement('div');
    toast.className = `px-4 py-2 rounded-lg text-white text-sm mb-2 transform transition-all duration-300 translate-x-full ${
        type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
    }`;
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    
    // 애니메이션
    setTimeout(() => toast.classList.remove('translate-x-full'), 100);
    setTimeout(() => {
        toast.classList.add('translate-x-full');
        setTimeout(() => {
            if (toastContainer.contains(toast)) {
                toastContainer.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// 학생 기록 저장 함수
export async function saveStudentRecord(studentId, measurementData, sessionId, activityId, csrfToken) {
    try {
        // API URL을 체험 모드에 따라 조건부 변경
        const apiUrl = window.IS_DEMO 
            ? '/physical_education/demo/api/save-measurement/'
            : '/physical_education/api/paps/save-measurement/';
            
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(window.IS_DEMO ? {} : {'X-CSRFToken': csrfToken})
            },
            body: JSON.stringify({
                session_id: sessionId,
                student_id: studentId,
                activity_id: activityId,
                measurement_data: measurementData
            })
        });

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Save error:', error);
        return { success: false, error: '저장 중 오류가 발생했습니다.' };
    }
}

// 편집 모드 전환 함수
export function toggleEditMode(studentElement, isEditing) {
    const displays = studentElement.querySelectorAll('.measurement-display');
    const inputs = studentElement.querySelectorAll('.measurement-input');
    const editBtn = studentElement.querySelector('.edit-btn');
    const saveBtn = studentElement.querySelector('.save-btn');
    const cancelBtn = studentElement.querySelector('.cancel-btn');

    if (isEditing) {
        displays.forEach(display => display.classList.add('hidden'));
        inputs.forEach(input => {
            input.classList.remove('hidden');
            if (input.type !== 'checkbox') {
                input.focus();
                input.select();
            }
        });
        
        if (editBtn) editBtn.classList.add('hidden');
        if (saveBtn) saveBtn.classList.remove('hidden');
        if (cancelBtn) cancelBtn.classList.remove('hidden');
    } else {
        displays.forEach(display => display.classList.remove('hidden'));
        inputs.forEach(input => input.classList.add('hidden'));
        
        if (editBtn) editBtn.classList.remove('hidden');
        if (saveBtn) saveBtn.classList.add('hidden');
        if (cancelBtn) cancelBtn.classList.add('hidden');
    }
}

// 숫자 포맷팅 함수
export function formatNumber(value, decimalPlaces = 1) {
    if (value === null || value === undefined || value === '') {
        return '';
    }
    const num = parseFloat(value);
    if (isNaN(num)) {
        return '';
    }
    return num.toFixed(decimalPlaces);
}

// 입력값 검증 함수
export function validateInput(value, min, max, required = true) {
    if (required && (value === null || value === undefined || value === '')) {
        return { valid: false, error: '값을 입력해주세요.' };
    }
    
    if (value === null || value === undefined || value === '') {
        return { valid: true };
    }

    const num = parseFloat(value);
    if (isNaN(num)) {
        return { valid: false, error: '올바른 숫자를 입력해주세요.' };
    }

    if (num < min || num > max) {
        return { valid: false, error: `${min}~${max} 범위의 값을 입력해주세요.` };
    }

    return { valid: true };
}

// 측정 완료 카운터 업데이트
export function updateMeasuredCount() {
    const measuredCountElement = document.getElementById('measured-count');
    if (!measuredCountElement) return;

    const studentRows = document.querySelectorAll('[data-student-id]');
    let measuredCount = 0;

    studentRows.forEach(row => {
        const displays = row.querySelectorAll('.measurement-display');
        let hasRecord = false;
        
        displays.forEach(display => {
            if (display.textContent && 
                display.textContent !== '미측정' && 
                display.textContent.trim() !== '') {
                hasRecord = true;
            }
        });
        
        if (hasRecord) {
            measuredCount++;
        }
    });

    measuredCountElement.textContent = `${measuredCount}명`;
}

// 학생 행 업데이트 함수
export function updateStudentRow(studentId, measurementData, fieldMappings) {
    const studentElement = document.querySelector(`[data-student-id="${studentId}"]`);
    if (!studentElement) return;

    // 측정값 표시 업데이트
    Object.entries(fieldMappings).forEach(([field, config]) => {
        const display = studentElement.querySelector(`.measurement-display[data-field="${field}"]`);
        const input = studentElement.querySelector(`.measurement-input[data-field="${field}"]`);
        
        if (display && input && measurementData[field] !== undefined) {
            const value = measurementData[field];
            display.textContent = config.formatter ? config.formatter(value) : `${value} ${config.unit || ''}`;
            display.classList.remove('text-gray-500');
            display.classList.add('text-teal-600', 'font-bold');
            
            input.value = value;
        }
    });

    // 버튼 텍스트 및 스타일 변경
    const editBtn = studentElement.querySelector('.edit-btn');
    if (editBtn) {
        editBtn.textContent = '수정';
        editBtn.className = 'edit-btn bg-yellow-400 hover:bg-yellow-500 text-white font-bold py-2 px-4 rounded-lg transition text-sm';
    }
}

// 기본 이벤트 핸들러 설정
export function setupCommonEventHandlers(studentContainer, saveFunction) {
    if (!studentContainer) return;

    studentContainer.addEventListener('click', async (e) => {
        const studentElement = e.target.closest('[data-student-id]');
        if (!studentElement) return;

        const studentId = studentElement.dataset.studentId;

        if (e.target.classList.contains('edit-btn')) {
            toggleEditMode(studentElement, true);
        } 
        else if (e.target.classList.contains('save-btn')) {
            const success = await saveFunction(studentElement, studentId);
            if (success) {
                toggleEditMode(studentElement, false);
                updateMeasuredCount();
            }
        }
        else if (e.target.classList.contains('cancel-btn')) {
            // 원래 값으로 복원
            restoreOriginalValues(studentElement);
            toggleEditMode(studentElement, false);
        }
    });

    studentContainer.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && e.target.classList.contains('measurement-input')) {
            const studentElement = e.target.closest('[data-student-id]');
            const saveBtn = studentElement.querySelector('.save-btn');
            if (saveBtn) {
                saveBtn.click();
            }
        }
    });
}

// 원래 값 복원 함수
function restoreOriginalValues(studentElement) {
    const inputs = studentElement.querySelectorAll('.measurement-input');
    const displays = studentElement.querySelectorAll('.measurement-display');
    
    inputs.forEach((input, index) => {
        const display = displays[index];
        if (display && display.textContent !== '미측정') {
            const originalValue = display.textContent.replace(/[^0-9.-]/g, '');
            if (originalValue) {
                input.value = originalValue;
            } else {
                input.value = '';
            }
        } else {
            input.value = '';
        }
    });
}