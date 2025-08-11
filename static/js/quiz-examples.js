/**
 * Quiz Examples Interactive Component
 * Handles Embla Carousel and quiz interactions
 */

class QuizExamples {
    constructor() {
        this.emblaApi = null;
        this.currentSlideIndex = 0;
        this.autoplayPlugin = null;
        
        // Quiz data and correct answers
        this.quizData = {
            ox: {
                correct: 'X',
                explanation: 'WHO는 건강을 신체적, 정신적, 사회적 안녕을 모두 포함하는 완전한 상태로 정의합니다.'
            },
            choice: {
                correct: '4',
                explanation: '경제적 안녕은 WHO가 정의한 건강의 3요소(신체적, 정신적, 사회적 안녕)에 포함되지 않습니다.'
            },
            line_matching: {
                correct: {
                    'left-1': 'right-1', // 신체적 건강 -> 몸이 튼튼한 것
                    'left-2': 'right-2', // 정신적 건강 -> 마음이 안정된 상태
                    'left-3': 'right-3'  // 사회적 건강 -> 친구들과 잘 어울리는 것
                },
                explanation: '신체적 건강-몸이 튼튼한 것, 정신적 건강-마음이 안정된 상태, 사회적 건강-친구들과 잘 어울리는 것'
            },
            drag_drop: {
                correct: {
                    1: '배', // 첫 번째 빈칸
                    2: '등'  // 두 번째 빈칸
                },
                explanation: '올바른 자세를 위해서는 배에 힘을 주고, 등을 펴는 것이 중요합니다.'
            },
            selection: {
                correct: 'good',
                explanation: '건강한 생활 습관은 신체적, 정신적 건강뿐만 아니라 사회적 관계 형성에도 긍정적인 영향을 미칩니다.'
            }
        };
        
        // State tracking
        this.quizStates = {};
        this.lineMatchingConnections = {};
        this.dragDropAnswers = {};
        
        this.init();
    }
    
    init() {
        this.setupEmblaCarousel();
        this.setupQuizInteractions();
        this.setupNavigation();
        this.initializeQuizStates();
        
        // Initial slide configuration
        setTimeout(() => {
            this.handleSlideChange();
        }, 100);
    }
    
    setupEmblaCarousel() {
        const emblaNode = document.querySelector('.embla.quiz-carousel');
        if (!emblaNode) return;
        
        // Initialize autoplay plugin
        this.autoplayPlugin = EmblaCarouselAutoplay({
            delay: 5000,
            stopOnInteraction: true,
            stopOnMouseEnter: true
        });
        
        // Initialize Embla
        this.emblaApi = EmblaCarousel(emblaNode, {
            align: 'start',
            loop: true,
            skipSnaps: false,
            startIndex: 0,
            watchDrag: false  // Disable drag for all slides initially
        }, [this.autoplayPlugin]);
        
        // Setup event listeners
        this.emblaApi.on('select', this.onSlideSelect.bind(this));
        this.emblaApi.on('init', this.updateDots.bind(this));
        this.emblaApi.on('select', this.updateDots.bind(this));
        this.emblaApi.on('select', this.handleSlideChange.bind(this));
    }
    
    setupNavigation() {
        // Previous/Next buttons
        const prevBtn = document.querySelector('.embla__prev');
        const nextBtn = document.querySelector('.embla__next');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                this.emblaApi?.scrollPrev();
                this.pauseAutoplay();
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.emblaApi?.scrollNext();
                this.pauseAutoplay();
            });
        }
        
        // Tab navigation
        document.querySelectorAll('.quiz-nav-tab').forEach((tab, index) => {
            tab.addEventListener('click', () => {
                this.emblaApi?.scrollTo(index);
                this.updateTabStates(index);
                this.pauseAutoplay();
            });
        });
        
        // Dot navigation
        document.querySelectorAll('.embla__dot').forEach((dot, index) => {
            dot.addEventListener('click', () => {
                this.emblaApi?.scrollTo(index);
                this.pauseAutoplay();
            });
        });
    }
    
    setupQuizInteractions() {
        this.setupOXQuiz();
        this.setupChoiceQuiz();
        this.setupLineMatchingQuiz();
        this.setupDragDropQuiz();
        this.setupSelectionQuiz();
        this.setupSubmitButtons();
    }
    
    setupOXQuiz() {
        document.querySelectorAll('.ox-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const slide = e.target.closest('.quiz-slide');
                const answer = e.target.getAttribute('data-answer');
                
                // Clear previous selections
                slide.querySelectorAll('.ox-option').forEach(opt => opt.classList.remove('selected'));
                
                // Select current option
                e.target.classList.add('selected');
                
                // Update state and enable submit
                this.updateQuizState(slide, { selectedAnswer: answer });
            });
        });
    }
    
    setupChoiceQuiz() {
        document.querySelectorAll('.choice-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const slide = e.target.closest('.quiz-slide');
                const answer = e.target.getAttribute('data-answer');
                
                // Clear previous selections
                slide.querySelectorAll('.choice-option').forEach(opt => opt.classList.remove('selected'));
                
                // Select current option
                e.target.classList.add('selected');
                
                // Update state and enable submit
                this.updateQuizState(slide, { selectedAnswer: answer });
            });
        });
    }
    
    setupLineMatchingQuiz() {
        let selectedLeft = null;
        
        document.querySelectorAll('.left-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // Clear previous selections
                document.querySelectorAll('.left-item').forEach(i => i.classList.remove('selected'));
                document.querySelectorAll('.right-item').forEach(i => i.classList.remove('selected'));
                
                // Select this item
                e.currentTarget.classList.add('selected');
                selectedLeft = e.currentTarget.getAttribute('data-id');
            });
        });
        
        document.querySelectorAll('.right-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!selectedLeft) return;
                
                const rightId = e.currentTarget.getAttribute('data-id');
                const slide = e.currentTarget.closest('.quiz-slide');
                
                // Create connection
                this.createConnection(selectedLeft, rightId, slide);
                
                // Update connections object
                this.lineMatchingConnections[selectedLeft] = rightId;
                
                // Clear selections
                document.querySelectorAll('.left-item, .right-item').forEach(i => i.classList.remove('selected'));
                selectedLeft = null;
                
                // Check if all connections are made
                if (Object.keys(this.lineMatchingConnections).length === 3) {
                    this.updateQuizState(slide, { connections: this.lineMatchingConnections });
                }
            });
        });
    }
    
    createConnection(leftId, rightId, slide) {
        const leftItem = slide.querySelector(`[data-id="${leftId}"]`);
        const rightItem = slide.querySelector(`[data-id="${rightId}"]`);
        const svg = slide.querySelector('.connection-lines');
        
        if (!leftItem || !rightItem || !svg) return;
        
        // Remove existing connection from this left item
        const existingLine = svg.querySelector(`[data-left="${leftId}"]`);
        if (existingLine) {
            existingLine.remove();
        }
        
        // Get positions as percentages
        const leftY = this.getItemPosition(leftItem, slide);
        const rightY = this.getItemPosition(rightItem, slide);
        
        // Create new line with proper coordinates
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('data-left', leftId);
        line.setAttribute('data-right', rightId);
        line.setAttribute('x1', '25');  // Start from right edge of left column
        line.setAttribute('y1', leftY);
        line.setAttribute('x2', '75');  // End at left edge of right column
        line.setAttribute('y2', rightY);
        line.setAttribute('stroke', '#3B82F6');
        line.setAttribute('stroke-width', '2');
        line.setAttribute('stroke-linecap', 'round');
        line.classList.add('connection-line');
        
        svg.appendChild(line);
    }
    
    getItemPosition(item, slide) {
        const container = slide.querySelector('.line-matching-container');
        const containerRect = container.getBoundingClientRect();
        const itemRect = item.getBoundingClientRect();
        
        // Calculate relative position within the line matching container
        const relativeTop = itemRect.top - containerRect.top + itemRect.height / 2;
        const containerHeight = containerRect.height;
        
        // Convert to percentage for SVG viewBox (0-100)
        return Math.max(5, Math.min(95, (relativeTop / containerHeight * 100)));
    }
    
    setupDragDropQuiz() {
        let draggedElement = null;
        
        document.querySelectorAll('.drag-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.stopPropagation();
                draggedElement = e.target;
                e.target.classList.add('dragging');
            });
            
            item.addEventListener('dragend', (e) => {
                e.stopPropagation();
                e.target.classList.remove('dragging');
                draggedElement = null;
            });
            
            // Touch support for mobile
            item.addEventListener('touchstart', (e) => {
                e.stopPropagation();
                draggedElement = e.target;
                e.target.classList.add('dragging');
            });
            
            // Mouse events for better interaction
            item.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                draggedElement = e.target;
                e.target.classList.add('dragging');
            });
            
            item.addEventListener('mouseup', (e) => {
                e.stopPropagation();
                if (draggedElement === e.target) {
                    e.target.classList.remove('dragging');
                }
            });
        });
        
        document.querySelectorAll('.drop-zone').forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.add('drag-over');
            });
            
            zone.addEventListener('dragleave', (e) => {
                e.stopPropagation();
                zone.classList.remove('drag-over');
            });
            
            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!draggedElement) return;
                
                const value = draggedElement.getAttribute('data-value');
                const target = e.target.getAttribute('data-target');
                const slide = e.target.closest('.quiz-slide');
                
                // Update drop zone content
                e.target.textContent = value;
                e.target.classList.remove('drag-over');
                e.target.classList.add('filled');
                
                // Hide dragged item
                draggedElement.style.opacity = '0.3';
                draggedElement.draggable = false;
                draggedElement.classList.remove('dragging');
                draggedElement = null;
                
                // Update answers object
                this.dragDropAnswers[target] = value;
                
                // Check if all zones are filled
                if (Object.keys(this.dragDropAnswers).length === 2) {
                    this.updateQuizState(slide, { answers: this.dragDropAnswers });
                }
            });
            
            // Click alternative for touch devices
            zone.addEventListener('click', (e) => {
                e.stopPropagation();
                if (!draggedElement) return;
                
                const value = draggedElement.getAttribute('data-value');
                const target = e.target.getAttribute('data-target');
                const slide = e.target.closest('.quiz-slide');
                
                // Update drop zone content
                e.target.textContent = value;
                e.target.classList.add('filled');
                
                // Hide dragged item
                draggedElement.style.opacity = '0.3';
                draggedElement.draggable = false;
                draggedElement.classList.remove('dragging');
                draggedElement = null;
                
                // Update answers object
                this.dragDropAnswers[target] = value;
                
                // Check if all zones are filled
                if (Object.keys(this.dragDropAnswers).length === 2) {
                    this.updateQuizState(slide, { answers: this.dragDropAnswers });
                }
            });
        });
    }
    
    setupSelectionQuiz() {
        document.querySelectorAll('.selection-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const slide = e.target.closest('.quiz-slide');
                const group = e.target.closest('.selection-group');
                const value = e.target.getAttribute('data-value');
                
                // Clear previous selections in this group
                group.querySelectorAll('.selection-option').forEach(opt => opt.classList.remove('selected'));
                
                // Select current option
                e.target.classList.add('selected');
                
                // Update state and enable submit
                this.updateQuizState(slide, { selectedAnswer: value });
            });
        });
    }
    
    setupSubmitButtons() {
        document.querySelectorAll('.quiz-submit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const slide = e.target.closest('.quiz-slide');
                const quizType = slide.getAttribute('data-quiz-type');
                this.checkAnswer(slide, quizType);
            });
        });
    }
    
    updateQuizState(slide, newState) {
        const quizType = slide.getAttribute('data-quiz-type');
        this.quizStates[quizType] = { ...this.quizStates[quizType], ...newState };
        
        // Enable submit button
        const submitBtn = slide.querySelector('.quiz-submit-btn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.add('enabled');
        }
    }
    
    checkAnswer(slide, quizType) {
        const state = this.quizStates[quizType];
        const correctData = this.quizData[quizType];
        let isCorrect = false;
        
        // Check answer based on quiz type
        switch (quizType) {
            case 'ox':
            case 'choice':
            case 'selection':
                isCorrect = state.selectedAnswer === correctData.correct;
                break;
                
            case 'line_matching':
                isCorrect = this.checkLineMatchingAnswer(state.connections, correctData.correct);
                break;
                
            case 'drag_drop':
                isCorrect = this.checkDragDropAnswer(state.answers, correctData.correct);
                break;
        }
        
        this.showResult(slide, isCorrect, correctData.explanation);
        
        // Disable submit button
        const submitBtn = slide.querySelector('.quiz-submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.style.display = 'none';
        }
    }
    
    checkLineMatchingAnswer(userConnections, correctConnections) {
        if (!userConnections || Object.keys(userConnections).length !== 3) return false;
        
        for (const [left, right] of Object.entries(correctConnections)) {
            if (userConnections[left] !== right) return false;
        }
        return true;
    }
    
    checkDragDropAnswer(userAnswers, correctAnswers) {
        if (!userAnswers || Object.keys(userAnswers).length !== 2) return false;
        
        for (const [target, answer] of Object.entries(correctAnswers)) {
            if (userAnswers[target] !== answer) return false;
        }
        return true;
    }
    
    showResult(slide, isCorrect, explanation) {
        const resultSection = slide.querySelector('.quiz-result-section');
        const feedback = slide.querySelector('.quiz-feedback');
        const explanationEl = slide.querySelector('.quiz-explanation');
        
        if (!resultSection || !feedback || !explanationEl) return;
        
        // Show result section
        resultSection.classList.remove('hidden');
        
        // Set feedback
        if (isCorrect) {
            feedback.innerHTML = '<div class="correct-feedback"><i class="fas fa-check-circle text-green-500 mr-2"></i><span class="text-green-600 font-bold">정답입니다!</span></div>';
        } else {
            feedback.innerHTML = '<div class="incorrect-feedback"><i class="fas fa-times-circle text-red-500 mr-2"></i><span class="text-red-600 font-bold">틀렸습니다.</span></div>';
        }
        
        // Set explanation
        explanationEl.innerHTML = `<strong>해설:</strong> ${explanation}`;
        
        // Add animation
        resultSection.classList.add('fade-in');
        
        // Highlight correct answers
        this.highlightCorrectAnswers(slide, isCorrect);
    }
    
    highlightCorrectAnswers(slide, userIsCorrect) {
        const quizType = slide.getAttribute('data-quiz-type');
        
        if (!userIsCorrect) {
            // Highlight correct answers when user got it wrong
            switch (quizType) {
                case 'ox':
                case 'choice':
                case 'selection':
                    const correctValue = this.quizData[quizType].correct;
                    const correctOption = slide.querySelector(`[data-answer="${correctValue}"]`);
                    if (correctOption) correctOption.classList.add('correct-answer');
                    break;
                    
                case 'line_matching':
                    this.highlightCorrectConnections(slide);
                    break;
                    
                case 'drag_drop':
                    this.highlightCorrectDropZones(slide);
                    break;
            }
        }
    }
    
    highlightCorrectConnections(slide) {
        const svg = slide.querySelector('.connection-lines');
        const correctConnections = this.quizData.line_matching.correct;
        
        // Remove existing lines and add correct ones
        svg.innerHTML = '';
        
        for (const [leftId, rightId] of Object.entries(correctConnections)) {
            this.createConnection(leftId, rightId, slide);
        }
        
        // Style correct lines
        svg.querySelectorAll('.connection-line').forEach(line => {
            line.setAttribute('stroke', '#10B981');
            line.setAttribute('stroke-width', '3');
        });
    }
    
    highlightCorrectDropZones(slide) {
        const correctAnswers = this.quizData.drag_drop.correct;
        
        for (const [target, value] of Object.entries(correctAnswers)) {
            const zone = slide.querySelector(`[data-target="${target}"]`);
            if (zone) {
                zone.textContent = value;
                zone.classList.add('correct-answer', 'filled');
            }
        }
    }
    
    onSlideSelect() {
        const selectedIndex = this.emblaApi?.selectedScrollSnap() ?? 0;
        this.currentSlideIndex = selectedIndex;
        this.updateTabStates(selectedIndex);
    }
    
    handleSlideChange() {
        const selectedIndex = this.emblaApi?.selectedScrollSnap() ?? 0;
        const slides = document.querySelectorAll('.quiz-slide');
        const currentSlide = slides[selectedIndex];
        
        if (currentSlide) {
            const quizType = currentSlide.getAttribute('data-quiz-type');
            
            // Enable or disable carousel drag based on quiz type
            if (quizType === 'drag_drop') {
                // For drag & drop slides, keep drag disabled to prevent conflicts
                this.emblaApi.reInit({ watchDrag: false });
            } else {
                // For other slides, enable drag
                this.emblaApi.reInit({ watchDrag: true });
            }
        }
    }
    
    updateTabStates(activeIndex) {
        document.querySelectorAll('.quiz-nav-tab').forEach((tab, index) => {
            if (index === activeIndex) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
    }
    
    updateDots() {
        const selectedIndex = this.emblaApi?.selectedScrollSnap() ?? 0;
        
        document.querySelectorAll('.embla__dot').forEach((dot, index) => {
            if (index === selectedIndex) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }
    
    pauseAutoplay() {
        if (this.autoplayPlugin) {
            this.autoplayPlugin.stop();
            // Resume after 3 seconds
            setTimeout(() => {
                if (this.autoplayPlugin) {
                    this.autoplayPlugin.play();
                }
            }, 3000);
        }
    }
    
    initializeQuizStates() {
        // Initialize empty states for each quiz type
        const quizTypes = ['ox', 'choice', 'line_matching', 'drag_drop', 'selection'];
        quizTypes.forEach(type => {
            this.quizStates[type] = {};
        });
        
        // Reset connections and answers
        this.lineMatchingConnections = {};
        this.dragDropAnswers = {};
    }
    
    resetQuiz(quizType) {
        // Reset specific quiz state
        this.quizStates[quizType] = {};
        
        if (quizType === 'line_matching') {
            this.lineMatchingConnections = {};
        }
        
        if (quizType === 'drag_drop') {
            this.dragDropAnswers = {};
        }
        
        // Reset UI for the specific quiz
        const slide = document.querySelector(`[data-quiz-type="${quizType}"]`);
        if (slide) {
            // Reset selections
            slide.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
            slide.querySelectorAll('.filled').forEach(el => el.classList.remove('filled'));
            slide.querySelectorAll('.correct-answer').forEach(el => el.classList.remove('correct-answer'));
            
            // Reset result section
            const resultSection = slide.querySelector('.quiz-result-section');
            if (resultSection) {
                resultSection.classList.add('hidden');
            }
            
            // Reset submit button
            const submitBtn = slide.querySelector('.quiz-submit-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.remove('enabled');
                submitBtn.style.display = 'block';
            }
            
            // Reset specific UI elements
            if (quizType === 'line_matching') {
                const svg = slide.querySelector('.connection-lines');
                if (svg) svg.innerHTML = '';
            }
            
            if (quizType === 'drag_drop') {
                slide.querySelectorAll('.drop-zone').forEach(zone => {
                    zone.textContent = zone.textContent.match(/\[빈칸\d\]/)?.[0] || '[빈칸]';
                });
                slide.querySelectorAll('.drag-item').forEach(item => {
                    item.style.opacity = '1';
                    item.draggable = true;
                });
            }
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new QuizExamples();
});