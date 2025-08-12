/**
 * PAPS 측정 계산 함수 모듈
 * 종목별 계산 로직을 포함
 */

// BMI 계산
export function calculateBMI(height, weight) {
    if (!height || !weight || height <= 0 || weight <= 0) {
        return null;
    }
    const heightM = height / 100; // cm를 m로 변환
    return weight / (heightM * heightM);
}

// 최댓값 계산 (악력, 앉아윗몸앞으로굽히기, 제자리멀리뛰기 등)
export function calculateMax(...values) {
    const validValues = values.filter(v => v !== null && v !== undefined && v !== '' && !isNaN(v))
                             .map(v => parseFloat(v));
    
    if (validValues.length === 0) {
        return null;
    }
    
    return Math.max(...validValues);
}

// 종합유연성 총점 계산 (성공한 동작 수)
export function calculateTotalScore(...booleanValues) {
    return booleanValues.filter(v => v === true || v === 'true' || v === 1).length;
}

// 시간 포맷팅 (초를 분.초 형식으로)
export function formatTime(totalSeconds) {
    if (!totalSeconds || totalSeconds <= 0) {
        return '00:00';
    }
    
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// 분.초 형식을 총 초로 변환
export function parseTimeToSeconds(timeString) {
    if (!timeString || typeof timeString !== 'string') {
        return null;
    }
    
    const parts = timeString.split(':');
    if (parts.length !== 2) {
        return null;
    }
    
    const minutes = parseInt(parts[0]);
    const seconds = parseInt(parts[1]);
    
    if (isNaN(minutes) || isNaN(seconds)) {
        return null;
    }
    
    return minutes * 60 + seconds;
}

// PEI 계산 (스텝검사용)
export function calculatePEI(hr1, hr2, hr3, duration = 300, isMaleHighSchool = false) {
    if (!hr1 || !hr2 || !hr3) {
        return null;
    }
    
    const heartRates = [parseFloat(hr1), parseFloat(hr2), parseFloat(hr3)];
    
    if (heartRates.some(hr => isNaN(hr) || hr <= 0)) {
        return null;
    }
    
    const sumHR = heartRates.reduce((sum, hr) => sum + hr, 0);
    
    // 고등학교 남학생의 경우 다른 공식 사용
    if (isMaleHighSchool) {
        return (duration * 100) / (2 * sumHR);
    } else {
        // 초등학교, 중학교, 고등학교 여학생
        return (duration * 100) / (sumHR);
    }
}

// 운동강도 계산
export function calculateExerciseIntensity(avgHeartRate, age) {
    if (!avgHeartRate || !age || avgHeartRate <= 0 || age <= 0) {
        return null;
    }
    
    const maxHeartRate = 220 - age;
    return (avgHeartRate / maxHeartRate) * 100;
}

// 소수점 자리수 포맷팅
export function formatDecimal(value, decimalPlaces = 1) {
    if (value === null || value === undefined || value === '') {
        return '';
    }
    
    const num = parseFloat(value);
    if (isNaN(num)) {
        return '';
    }
    
    return num.toFixed(decimalPlaces);
}

// BMI 등급 분류 (한국 기준)
export function getBMICategory(bmi) {
    if (!bmi || isNaN(bmi)) {
        return '미평가';
    }
    
    if (bmi < 18.5) {
        return '마름';
    } else if (bmi < 23) {
        return '정상';
    } else if (bmi < 25) {
        return '과체중';
    } else if (bmi < 30) {
        return '경도비만';
    } else {
        return '고도비만';
    }
}

// 악력 종합 최고값 계산 (좌우 각 2회 중 최고값들의 합)
export function calculateGripStrengthTotal(leftFirst, leftSecond, rightFirst, rightSecond) {
    const leftMax = calculateMax(leftFirst, leftSecond);
    const rightMax = calculateMax(rightFirst, rightSecond);
    
    if (leftMax === null || rightMax === null) {
        return null;
    }
    
    return leftMax + rightMax;
}