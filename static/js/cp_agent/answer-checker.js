// static/js/cp_agent/answer-checker.js - 정답 체크 시스템

/**
 * 정답 체크 시스템
 */
window.CPAgent.AnswerChecker = {
    
    /**
     * 문항의 정답을 체크하고 결과를 표시
     */
    checkAnswer: function(questionElement = null) {
        debugLog('ANSWER_CHECKER', '정답 체크 시작');
        
        const container = questionElement || document.getElementById('previewContent');
        if (!container) {
            debugLog('ANSWER_CHECKER', '문항 컨테이너를 찾을 수 없음');
            return null;
        }
        
        // 현재 답안 데이터 가져오기
        let answerData;
        try {
            answerData = JSON.parse(answerEditor.getValue() || '{}');
        } catch (e) {
            debugLog('ANSWER_CHECKER', '답안 데이터 파싱 오류', e);
            return null;
        }
        
        if (!answerData.correct) {
            debugLog('ANSWER_CHECKER', '정답 데이터가 없음');
            return null;
        }
        
        const questionType = this.detectQuestionType(container, answerData);
        debugLog('ANSWER_CHECKER', '문항 타입 감지', questionType);
        
        let result;
        switch (questionType) {
            case 'multiple_choice':
                result = this.checkMultipleChoice(container, answerData);
                break;
            case 'true_false':
                result = this.checkTrueFalse(container, answerData);
                break;
            case 'short_answer':
                result = this.checkShortAnswer(container, answerData);
                break;
            case 'essay':
                result = this.checkEssay(container, answerData);
                break;
            case 'matching':
                result = this.checkMatching(container, answerData);
                break;
            default:
                debugLog('ANSWER_CHECKER', '지원하지 않는 문항 타입', questionType);
                return null;
        }
        
        if (result) {
            this.displayResult(container, result);
        }
        
        return result;
    },
    
    /**
     * 문항 타입 자동 감지
     */
    detectQuestionType: function(container, answerData) {
        // 답안 데이터에서 타입 확인
        if (answerData.type) {
            return answerData.type;
        }
        
        // HTML 구조에서 추론
        const radioInputs = container.querySelectorAll('input[type="radio"]');
        const checkboxInputs = container.querySelectorAll('input[type="checkbox"]');
        const textInputs = container.querySelectorAll('input[type="text"], textarea');
        const selectElements = container.querySelectorAll('select');
        
        if (radioInputs.length > 0) {
            return 'multiple_choice';
        } else if (checkboxInputs.length > 0) {
            return 'multiple_select';
        } else if (textInputs.length === 1) {
            return 'short_answer';
        } else if (textInputs.length > 1) {
            return 'essay';
        } else if (selectElements.length > 0) {
            return 'matching';
        }
        
        return 'unknown';
    },
    
    /**
     * 객관식 문항 체크
     */
    checkMultipleChoice: function(container, answerData) {
        const radioInputs = container.querySelectorAll('input[type="radio"]');
        const correctAnswer = String(answerData.correct).toLowerCase();
        
        let selectedValue = null;
        let isCorrect = false;
        
        // 선택된 답안 찾기
        radioInputs.forEach(input => {
            if (input.checked) {
                selectedValue = String(input.value).toLowerCase();
            }
        });
        
        if (selectedValue !== null) {
            isCorrect = selectedValue === correctAnswer;
        }
        
        return {
            type: 'multiple_choice',
            isCorrect: isCorrect,
            userAnswer: selectedValue,
            correctAnswer: correctAnswer,
            explanation: answerData.explanation || '',
            hasAnswer: selectedValue !== null
        };
    },
    
    /**
     * 참/거짓 문항 체크
     */
    checkTrueFalse: function(container, answerData) {
        const radioInputs = container.querySelectorAll('input[type="radio"]');
        const correctAnswer = String(answerData.correct).toLowerCase();
        
        let selectedValue = null;
        
        radioInputs.forEach(input => {
            if (input.checked) {
                selectedValue = String(input.value).toLowerCase();
            }
        });
        
        const isCorrect = selectedValue !== null && 
                         (selectedValue === correctAnswer || 
                          (correctAnswer === 'true' && ['true', 't', '참', '1'].includes(selectedValue)) ||
                          (correctAnswer === 'false' && ['false', 'f', '거짓', '0'].includes(selectedValue)));
        
        return {
            type: 'true_false',
            isCorrect: isCorrect,
            userAnswer: selectedValue,
            correctAnswer: correctAnswer,
            explanation: answerData.explanation || '',
            hasAnswer: selectedValue !== null
        };
    },
    
    /**
     * 단답형 문항 체크
     */
    checkShortAnswer: function(container, answerData) {
        const textInput = container.querySelector('input[type="text"], textarea');
        if (!textInput) return null;
        
        const userAnswer = textInput.value.trim();
        const correctAnswers = Array.isArray(answerData.correct) ? 
                              answerData.correct : [answerData.correct];
        
        // 정답 배열에서 하나라도 일치하면 정답
        const isCorrect = correctAnswers.some(correct => {
            const normalizedCorrect = String(correct).trim().toLowerCase();
            const normalizedUser = userAnswer.toLowerCase();
            
            // 완전 일치 또는 부분 일치 (설정에 따라)
            return normalizedUser === normalizedCorrect ||
                   (answerData.partial_match && normalizedUser.includes(normalizedCorrect));
        });
        
        return {
            type: 'short_answer',
            isCorrect: isCorrect,
            userAnswer: userAnswer,
            correctAnswer: correctAnswers,
            explanation: answerData.explanation || '',
            hasAnswer: userAnswer.length > 0
        };
    },
    
    /**
     * 서술형 문항 체크 (키워드 기반)
     */
    checkEssay: function(container, answerData) {
        const textareas = container.querySelectorAll('textarea');
        const textInputs = container.querySelectorAll('input[type="text"]');
        const allInputs = [...textareas, ...textInputs];
        
        if (allInputs.length === 0) return null;
        
        const userAnswers = allInputs.map(input => input.value.trim());
        const keywords = answerData.keywords || [];
        
        let keywordScore = 0;
        if (keywords.length > 0) {
            const fullText = userAnswers.join(' ').toLowerCase();
            keywordScore = keywords.filter(keyword => 
                fullText.includes(keyword.toLowerCase())
            ).length / keywords.length;
        }
        
        return {
            type: 'essay',
            isCorrect: keywordScore >= (answerData.threshold || 0.5),
            userAnswer: userAnswers,
            keywordScore: keywordScore,
            keywords: keywords,
            explanation: answerData.explanation || '',
            hasAnswer: userAnswers.some(answer => answer.length > 0)
        };
    },
    
    /**
     * 매칭 문항 체크
     */
    checkMatching: function(container, answerData) {
        const selects = container.querySelectorAll('select');
        const correctMatches = answerData.matches || {};
        
        let correctCount = 0;
        let totalCount = 0;
        const userMatches = {};
        
        selects.forEach((select, index) => {
            const key = select.dataset.key || index;
            const selectedValue = select.value;
            
            userMatches[key] = selectedValue;
            
            if (correctMatches[key]) {
                totalCount++;
                if (selectedValue === correctMatches[key]) {
                    correctCount++;
                }
            }
        });
        
        const isCorrect = totalCount > 0 && correctCount === totalCount;
        
        return {
            type: 'matching',
            isCorrect: isCorrect,
            userAnswer: userMatches,
            correctAnswer: correctMatches,
            score: totalCount > 0 ? correctCount / totalCount : 0,
            explanation: answerData.explanation || '',
            hasAnswer: Object.keys(userMatches).some(key => userMatches[key])
        };
    },
    
    /**
     * 결과 표시
     */
    displayResult: function(container, result) {
        // 기존 결과 제거
        const existingResult = container.querySelector('.answer-result');
        if (existingResult) {
            existingResult.remove();
        }
        
        // 결과 HTML 생성
        const resultHtml = this.createResultHtml(result);
        
        // 결과 추가
        const resultDiv = document.createElement('div');
        resultDiv.className = 'answer-result mt-4 p-4 rounded-lg border-2';
        resultDiv.style.borderColor = result.isCorrect ? '#10B981' : '#EF4444';
        resultDiv.style.backgroundColor = result.isCorrect ? '#F0FDF4' : '#FEF2F2';
        resultDiv.innerHTML = resultHtml;
        
        container.appendChild(resultDiv);
        
        // 애니메이션 효과
        resultDiv.style.opacity = '0';
        setTimeout(() => {
            resultDiv.style.transition = 'opacity 0.3s ease-in-out';
            resultDiv.style.opacity = '1';
        }, 10);
        
        debugLog('ANSWER_CHECKER', '결과 표시 완료', result);
    },
    
    /**
     * 결과 HTML 생성
     */
    createResultHtml: function(result) {
        const isCorrect = result.isCorrect;
        const icon = isCorrect ? 
            '<i class="fas fa-check-circle text-green-600"></i>' : 
            '<i class="fas fa-times-circle text-red-600"></i>';
        
        const status = isCorrect ? 
            '<span class="text-green-800 font-semibold">정답입니다!</span>' : 
            '<span class="text-red-800 font-semibold">오답입니다.</span>';
        
        let html = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0 mt-1">${icon}</div>
                <div class="flex-1">
                    <div class="mb-2">${status}</div>
        `;
        
        // 타입별 세부 정보
        switch (result.type) {
            case 'multiple_choice':
            case 'true_false':
                if (result.hasAnswer) {
                    html += `<p class="text-sm mb-2">선택한 답: <strong>${result.userAnswer}</strong></p>`;
                }
                if (!isCorrect) {
                    html += `<p class="text-sm mb-2">정답: <strong>${result.correctAnswer}</strong></p>`;
                }
                break;
                
            case 'short_answer':
                if (result.hasAnswer) {
                    html += `<p class="text-sm mb-2">입력한 답: <strong>${result.userAnswer}</strong></p>`;
                }
                if (!isCorrect) {
                    html += `<p class="text-sm mb-2">정답: <strong>${Array.isArray(result.correctAnswer) ? result.correctAnswer.join(', ') : result.correctAnswer}</strong></p>`;
                }
                break;
                
            case 'essay':
                if (result.keywordScore !== undefined) {
                    html += `<p class="text-sm mb-2">키워드 점수: <strong>${Math.round(result.keywordScore * 100)}%</strong></p>`;
                }
                break;
                
            case 'matching':
                html += `<p class="text-sm mb-2">정답률: <strong>${Math.round(result.score * 100)}%</strong></p>`;
                break;
        }
        
        // 해설 표시
        if (result.explanation) {
            html += `
                <div class="mt-3 pt-3 border-t border-gray-300">
                    <p class="text-sm font-medium text-gray-700 mb-1">해설:</p>
                    <p class="text-sm text-gray-600">${result.explanation}</p>
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
        
        return html;
    },
    
    /**
     * 문항에 체크 버튼 추가
     */
    addCheckButton: function(container = null) {
        const targetContainer = container || document.getElementById('previewContent');
        if (!targetContainer) return;
        
        // 기존 버튼 제거
        const existingBtn = targetContainer.querySelector('.check-answer-btn');
        if (existingBtn) {
            existingBtn.remove();
        }
        
        // 체크 버튼 생성
        const checkBtn = document.createElement('button');
        checkBtn.className = 'check-answer-btn mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition';
        checkBtn.innerHTML = '<i class="fas fa-check mr-2"></i>정답 확인';
        checkBtn.onclick = () => this.checkAnswer(targetContainer);
        
        targetContainer.appendChild(checkBtn);
    },
    
    /**
     * 자동 체크 모드 토글
     */
    toggleAutoCheck: function() {
        const container = document.getElementById('previewContent');
        if (!container) return;
        
        // 입력 요소들에 이벤트 리스너 추가/제거
        const inputs = container.querySelectorAll('input, textarea, select');
        
        if (container.dataset.autoCheck === 'true') {
            // 자동 체크 비활성화
            container.dataset.autoCheck = 'false';
            inputs.forEach(input => {
                input.removeEventListener('change', this.autoCheckHandler);
                input.removeEventListener('input', this.autoCheckHandler);
            });
            showToast('자동 체크가 비활성화되었습니다', 'info');
        } else {
            // 자동 체크 활성화
            container.dataset.autoCheck = 'true';
            inputs.forEach(input => {
                input.addEventListener('change', this.autoCheckHandler);
                input.addEventListener('input', this.autoCheckHandler);
            });
            showToast('자동 체크가 활성화되었습니다', 'success');
        }
    },
    
    /**
     * 자동 체크 핸들러
     */
    autoCheckHandler: function() {
        const container = document.getElementById('previewContent');
        if (container && container.dataset.autoCheck === 'true') {
            // 디바운싱 적용
            clearTimeout(window.autoCheckTimeout);
            window.autoCheckTimeout = setTimeout(() => {
                CPAgent.AnswerChecker.checkAnswer(container);
            }, 500);
        }
    }
};