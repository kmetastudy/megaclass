/**
 * PAPS (Physical Activity Promotion System) 자동 계산 로직
 * 
 * 이 모듈은 Backend의 physical_education/utils.py와 동일한 계산 로직을 구현합니다.
 * Frontend와 Backend 간의 일관성을 보장합니다.
 */

window.PAPSCalculations = {
    
    /**
     * 안전한 Decimal 변환 (Python의 safe_decimal과 동일)
     */
    safeDecimal: function(value) {
        if (value === null || value === undefined || value === '') {
            return 0;
        }
        const num = parseFloat(value);
        return isNaN(num) ? 0 : num;
    },

    /**
     * BMI 계산 (Python의 calculate_bmi와 동일)
     * BMI(kg/m²) = 체중(kg) ÷ [신장(m) × 신장(m)]
     * 0.01kg/m² 단위에서 올림하여 0.1kg/m² 단위로 기록
     */
    calculateBMI: function(heightCm, weightKg) {
        heightCm = this.safeDecimal(heightCm);
        weightKg = this.safeDecimal(weightKg);
        
        if (heightCm <= 0) {
            return 0.0;
        }
        
        const heightM = heightCm / 100;
        const bmiRaw = weightKg / (heightM * heightM);
        
        // 0.01 단위에서 올림하여 0.1 단위로 반환
        const bmiRounded = Math.ceil(bmiRaw * 100) / 100;
        return Math.round(bmiRounded * 10) / 10;
    },

    /**
     * PEI (Physical Efficiency Index) 계산 (Python의 calculate_pei와 동일)
     */
    calculatePEI: function(heartRate1, heartRate2, heartRate3, durationSeconds = 300, isMaleHighSchool = false) {
        const D = durationSeconds;
        
        if (isMaleHighSchool) {
            // 고등학생(남): PEI = D × 100 / {5.5 × p} + {0.22 × (300-D)}
            // p: 1회 심박수만 사용
            const p = this.safeDecimal(heartRate1);
            if (p <= 0) {
                return 0.0;
            }
            const pei = (D * 100) / (5.5 * p + 0.22 * (300 - D));
            return Math.ceil(pei * 10) / 10;
        } else {
            // 초등학생, 중학생, 고등학생(여): PEI = D / (2 × P) × 100
            // P: 1회 + 2회 + 3회 심박수 합
            const P = this.safeDecimal(heartRate1) + this.safeDecimal(heartRate2) + this.safeDecimal(heartRate3);
            if (P <= 0) {
                return 0.0;
            }
            const pei = (D / (2 * P)) * 100;
            return Math.ceil(pei * 10) / 10;
        }
    },

    /**
     * 최댓값 계산 (Python의 calculate_max_value와 동일)
     */
    calculateMaxValue: function(...values) {
        const validValues = values.map(v => this.safeDecimal(v)).filter(v => v > 0);
        return validValues.length > 0 ? Math.max(...validValues) : 0;
    },

    /**
     * 총점 계산 (Python의 calculate_total_score와 동일)
     */
    calculateTotalScore: function(...booleanValues) {
        return booleanValues.filter(v => v === true).length;
    },

    /**
     * 운동강도 계산 (Python의 calculate_exercise_intensity와 동일)
     */
    calculateExerciseIntensity: function(avgHeartRate, age) {
        if (age <= 0 || avgHeartRate <= 0) {
            return 0;
        }
        
        // 1단계: 기본 비율 계산
        const ratio = avgHeartRate / (220 - age);
        
        // 2단계: 소수점 3자리에서 올림 (소수점 2자리까지)
        const ratioRounded = Math.ceil(ratio * 100) / 100;
        
        // 3단계: 백분율 변환
        const intensity = Math.floor(ratioRounded * 100);
        
        return Math.min(intensity, 100); // 최대 100%
    },

    /**
     * 학년에서 나이 계산 (Python의 get_age_from_grade와 동일)
     */
    getAgeFromGrade: function(gradeNumber) {
        return gradeNumber + 6;
    },

    /**
     * 측정 데이터 처리 및 자동 계산 수행 (Python의 process_measurement_data와 동일)
     */
    processActivityData: function(activityName, measurementData, studentGrade) {
        const processedData = { ...measurementData };
        
        // 종목별 자동 계산 로직
        switch (activityName) {
            case 'BMI':
                // BMI 계산
                const height = measurementData['bmi_height'];
                const weight = measurementData['bmi_weight'];
                if (height && weight) {
                    processedData['bmi_bmi'] = this.calculateBMI(height, weight);
                } else {
                    // 값이 없으면 계산 결과도 제거
                    if (!height || !weight) {
                        delete processedData['bmi_bmi'];
                    }
                }
                break;
                
            case 'STEP_TEST':
                // PEI 계산
                const hr1 = measurementData['step_test_heart_rate_1'];
                const hr2 = measurementData['step_test_heart_rate_2'];
                const hr3 = measurementData['step_test_heart_rate_3'];
                if (hr1 && hr2 && hr3) {
                    // TODO: 성별 정보가 없어 임시로 학년만으로 고등학교 남학생 판단
                    // 향후 성별 정보 추가 시 수정 필요
                    const isMaleHS = studentGrade >= 10; // 임시로 고등학교 남학생 판단
                    processedData['step_test_pei'] = this.calculatePEI(hr1, hr2, hr3, 300, isMaleHS);
                } else {
                    // 심박수 값 중 하나라도 없으면 PEI 제거
                    if (!hr1 || !hr2 || !hr3) {
                        delete processedData['step_test_pei'];
                    }
                }
                break;
                
            case 'GRIP_STRENGTH':
                // 악력 최댓값 계산
                const gripValues = [
                    measurementData['grip_strength_right_hand_1'],
                    measurementData['grip_strength_left_hand_1'],
                    measurementData['grip_strength_right_hand_2'],
                    measurementData['grip_strength_left_hand_2']
                ];
                if (gripValues.some(v => v !== null && v !== undefined && v !== '')) {
                    processedData['grip_strength_best'] = this.calculateMaxValue(...gripValues);
                } else {
                    delete processedData['grip_strength_best'];
                }
                break;
                
            case 'SIT_REACH':
                // 앉아윗몸앞으로굽히기 최댓값
                const sitReachFirst = measurementData['sit_reach_first_attempt'];
                const sitReachSecond = measurementData['sit_reach_second_attempt'];
                if (sitReachFirst !== null && sitReachFirst !== undefined && sitReachFirst !== '' &&
                    sitReachSecond !== null && sitReachSecond !== undefined && sitReachSecond !== '') {
                    processedData['sit_reach_best_record'] = this.calculateMaxValue(sitReachFirst, sitReachSecond);
                } else {
                    delete processedData['sit_reach_best_record'];
                }
                break;
                
            case 'STANDING_LONG_JUMP':
                // 제자리멀리뛰기 최댓값
                const jumpFirst = measurementData['standing_long_jump_first_attempt'];
                const jumpSecond = measurementData['standing_long_jump_second_attempt'];
                if (jumpFirst !== null && jumpFirst !== undefined && jumpFirst !== '' &&
                    jumpSecond !== null && jumpSecond !== undefined && jumpSecond !== '') {
                    processedData['standing_long_jump_best_record'] = this.calculateMaxValue(jumpFirst, jumpSecond);
                } else {
                    delete processedData['standing_long_jump_best_record'];
                }
                break;
                
            case 'COMPREHENSIVE_FLEXIBILITY':
                // 종합유연성 총점
                const flexibilityFields = [
                    'flexibility_shoulder_left', 'flexibility_shoulder_right', 
                    'flexibility_body_left', 'flexibility_body_right',
                    'flexibility_side_left', 'flexibility_side_right', 
                    'flexibility_lower_body_left', 'flexibility_lower_body_right'
                ];
                const flexibilityValues = flexibilityFields.map(field => measurementData[field] === true);
                processedData['flexibility_total_score'] = this.calculateTotalScore(...flexibilityValues);
                break;
                
            case 'CARDIO_PRECISION_TEST':
                // 심폐지구력정밀평가 운동강도 계산
                const avgHR = measurementData['cardio_precision_avg_heart_rate'];
                if (avgHR) {
                    const age = this.getAgeFromGrade(studentGrade);
                    processedData['cardio_precision_avg_intensity'] = this.calculateExerciseIntensity(avgHR, age);
                } else {
                    delete processedData['cardio_precision_avg_intensity'];
                }
                break;
                
            case 'BODY_FAT_RATE_TEST':
                // 체지방률평가 BMI 계산
                const bodyFatHeight = measurementData['body_fat_rate_test_height'];
                const bodyFatWeight = measurementData['body_fat_rate_test_weight'];
                if (bodyFatHeight && bodyFatWeight) {
                    processedData['body_fat_rate_test_bmi'] = this.calculateBMI(bodyFatHeight, bodyFatWeight);
                } else {
                    if (!bodyFatHeight || !bodyFatWeight) {
                        delete processedData['body_fat_rate_test_bmi'];
                    }
                }
                break;
        }
        
        return processedData;
    },

    /**
     * 특정 학생의 자동 계산 수행 (기존 performAutoCalculation 대체)
     */
    performAutoCalculation: function(studentId, activityName, studentGrade, studentsData) {
        if (!studentsData || !studentsData[studentId]) {
            return {};
        }
        
        const studentActivityData = studentsData[studentId];
        if (!studentActivityData) {
            return {};
        }
        
        // 활동별 측정 데이터가 있는지 확인
        let measurementData = {};
        for (const activityId in studentActivityData) {
            measurementData = { ...measurementData, ...studentActivityData[activityId] };
        }
        
        return this.processActivityData(activityName, measurementData, studentGrade);
    }
};

console.log('PAPS Calculations module loaded successfully');