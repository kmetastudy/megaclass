/**
 * PAPS 측정 타이머 모듈
 * 시간 측정이 필요한 종목들을 위한 타이머 기능
 */

// 개별 타이머 클래스
export class IndividualTimer {
    constructor(displayElement, onUpdate = null, onComplete = null) {
        this.displayElement = displayElement;
        this.onUpdate = onUpdate;
        this.onComplete = onComplete;
        this.startTime = null;
        this.intervalId = null;
        this.isRunning = false;
        this.elapsedTime = 0;
    }

    start() {
        if (this.isRunning) return;
        
        this.startTime = Date.now() - this.elapsedTime;
        this.isRunning = true;
        
        this.intervalId = setInterval(() => {
            this.elapsedTime = Date.now() - this.startTime;
            this.updateDisplay();
            
            if (this.onUpdate) {
                this.onUpdate(this.elapsedTime);
            }
        }, 10); // 10ms 간격으로 업데이트
    }

    stop() {
        if (!this.isRunning) return;
        
        clearInterval(this.intervalId);
        this.isRunning = false;
        
        if (this.onComplete) {
            this.onComplete(this.elapsedTime);
        }
        
        return this.elapsedTime;
    }

    reset() {
        this.stop();
        this.elapsedTime = 0;
        this.updateDisplay();
    }

    updateDisplay() {
        if (this.displayElement) {
            const seconds = Math.floor(this.elapsedTime / 1000);
            const milliseconds = Math.floor((this.elapsedTime % 1000) / 10);
            this.displayElement.textContent = `${seconds}.${milliseconds.toString().padStart(2, '0')}`;
        }
    }

    getElapsedSeconds() {
        return Math.floor(this.elapsedTime / 1000);
    }

    getElapsedTime() {
        return this.elapsedTime;
    }
}

// 그룹 타이머 클래스 (여러 학생이 함께 측정)
export class GroupTimer {
    constructor(displayElement, onUpdate = null) {
        this.displayElement = displayElement;
        this.onUpdate = onUpdate;
        this.startTime = null;
        this.intervalId = null;
        this.isRunning = false;
        this.elapsedTime = 0;
        this.participants = new Map(); // studentId -> finishTime
    }

    start() {
        if (this.isRunning) return;
        
        this.startTime = Date.now();
        this.isRunning = true;
        this.participants.clear();
        
        this.intervalId = setInterval(() => {
            this.elapsedTime = Date.now() - this.startTime;
            this.updateDisplay();
            
            if (this.onUpdate) {
                this.onUpdate(this.elapsedTime);
            }
        }, 10);
    }

    stop() {
        if (!this.isRunning) return;
        
        clearInterval(this.intervalId);
        this.isRunning = false;
        
        return this.elapsedTime;
    }

    reset() {
        this.stop();
        this.elapsedTime = 0;
        this.participants.clear();
        this.updateDisplay();
    }

    // 참가자 완주 기록
    finishParticipant(studentId) {
        if (!this.isRunning) return null;
        
        const finishTime = this.elapsedTime;
        this.participants.set(studentId, finishTime);
        
        return Math.floor(finishTime / 1000); // 초 단위로 반환
    }

    // 참가자의 완주 시간 조회
    getParticipantTime(studentId) {
        const finishTime = this.participants.get(studentId);
        return finishTime ? Math.floor(finishTime / 1000) : null;
    }

    // 모든 참가자 완료 여부 확인
    allParticipantsFinished(expectedCount) {
        return this.participants.size >= expectedCount;
    }

    updateDisplay() {
        if (this.displayElement) {
            const totalSeconds = Math.floor(this.elapsedTime / 1000);
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;
            const milliseconds = Math.floor((this.elapsedTime % 1000) / 10);
            
            this.displayElement.textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(2, '0')}`;
        }
    }

    getCurrentTime() {
        return this.elapsedTime;
    }

    getCurrentSeconds() {
        return Math.floor(this.elapsedTime / 1000);
    }
}

// 랩 타이머 클래스 (오래달리기용)
export class LapTimer extends GroupTimer {
    constructor(displayElement, onUpdate = null, onLap = null) {
        super(displayElement, onUpdate);
        this.onLap = onLap;
        this.laps = new Map(); // studentId -> [lap1Time, lap2Time, ...]
    }

    // 랩 기록
    recordLap(studentId) {
        if (!this.isRunning) return null;
        
        const lapTime = this.elapsedTime;
        
        if (!this.laps.has(studentId)) {
            this.laps.set(studentId, []);
        }
        
        this.laps.get(studentId).push(lapTime);
        
        if (this.onLap) {
            this.onLap(studentId, this.laps.get(studentId).length, Math.floor(lapTime / 1000));
        }
        
        return Math.floor(lapTime / 1000);
    }

    // 학생의 랩 타임들 조회
    getStudentLaps(studentId) {
        const laps = this.laps.get(studentId) || [];
        return laps.map(lap => Math.floor(lap / 1000));
    }

    // 학생의 마지막 랩 타임 조회
    getLastLap(studentId) {
        const laps = this.laps.get(studentId) || [];
        if (laps.length === 0) return null;
        
        return Math.floor(laps[laps.length - 1] / 1000);
    }

    reset() {
        super.reset();
        this.laps.clear();
    }
}

// 타이머 유틸리티 함수들
export function formatTimerDisplay(milliseconds) {
    const totalSeconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const ms = Math.floor((milliseconds % 1000) / 10);
    
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
}

export function formatSimpleTime(seconds) {
    if (!seconds || seconds <= 0) return '0.00';
    
    return seconds.toFixed(2);
}

// 타이머 버튼 상태 관리
export function updateTimerButton(button, isRunning) {
    if (!button) return;
    
    if (isRunning) {
        button.textContent = '정지';
        button.classList.remove('bg-green-500', 'hover:bg-green-600');
        button.classList.add('bg-red-500', 'hover:bg-red-600');
    } else {
        button.textContent = '시작';
        button.classList.remove('bg-red-500', 'hover:bg-red-600');
        button.classList.add('bg-green-500', 'hover:bg-green-600');
    }
}