/**
 * 포인트 정책 관리 모듈
 * 정책 생성, 수정, 삭제 및 DOM 업데이트 처리
 */

import { apiClient, ApiError } from "/static/js/shared/api/api-client.js";

// ============================================================================
// API 호출 함수들
// ============================================================================

/**
 * 포인트 정책 생성 API 호출
 * @param {Object} data - 정책 데이터
 * @returns {Promise<Object>} API 응답
 */
async function createPolicyApi(data) {
  return await apiClient.post("/api/points/policies/create/", data);
}

/**
 * 포인트 정책 수정 API 호출
 * @param {string} policyId - 정책 UUID
 * @param {Object} data - 수정할 데이터
 * @returns {Promise<Object>} API 응답
 */
async function updatePolicyApi(policyId, data) {
  return await apiClient.post(`/api/points/policies/${policyId}/update/`, data);
}

/**
 * 포인트 정책 삭제 API 호출
 * @param {string} policyId - 정책 UUID
 * @returns {Promise<Object>} API 응답
 */
async function deletePolicyApi(policyId) {
  return await apiClient.delete(`/api/points/policies/${policyId}/delete/`);
}

// ============================================================================
// 이벤트 핸들러들
// ============================================================================

/**
 * 정책 생성 처리
 */
async function handleCreatePolicy() {
  const form = document.getElementById("create-policy-form");
  const formData = new FormData(form);
  const button = document.querySelector('[data-action="save-create"]');

  try {
    // 로딩 상태 시작
    setButtonLoading(button, true);

    // API 호출
    const response = await createPolicyApi({
      name: formData.get("name"),
      default_point_value: parseInt(formData.get("default_point_value")),
      description: formData.get("description") || "",
      is_active: formData.get("is_active") !== null,
    });

    // 성공 처리
    showToast("success", "정책 생성 완료", response.message);
    document.getElementById("create-policy-dialog").close();
    form.reset();

    // DOM 업데이트 - 새 카드 추가
    addPolicyCard(response.data);
  } catch (error) {
    handleApiError(error);
  } finally {
    setButtonLoading(button, false);
  }
}

/**
 * 정책 수정 처리
 */
async function handleEditPolicy() {
  const form = document.getElementById("edit-policy-form");
  const formData = new FormData(form);
  const policyId = document.getElementById("edit-policy-id").value;
  const button = document.querySelector('[data-action="save-edit"]');

  try {
    setButtonLoading(button, true);

    const response = await updatePolicyApi(policyId, {
      name: formData.get("name"),
      default_point_value: parseInt(formData.get("default_point_value")),
      description: formData.get("description") || "",
      is_active: formData.get("is_active") !== null,
    });

    showToast("success", "정책 수정 완료", response.message);
    document.getElementById("edit-policy-dialog").close();

    // DOM 업데이트 - 카드 내용 변경
    updatePolicyCard(policyId, response.data);
  } catch (error) {
    handleApiError(error);
  } finally {
    setButtonLoading(button, false);
  }
}

/**
 * 정책 삭제 처리
 */
async function handleDeletePolicy() {
  const policyId = document.getElementById("delete-policy-id").value;
  const button = document.querySelector('[data-action="confirm-delete"]');

  try {
    setButtonLoading(button, true);

    const response = await deletePolicyApi(policyId);

    showToast("success", "정책 삭제 완료", response.message);
    document.getElementById("delete-policy-dialog").close();

    // DOM 업데이트 - 카드 제거
    removePolicyCard(policyId);
  } catch (error) {
    handleApiError(error);
  } finally {
    setButtonLoading(button, false);
  }
}

// ============================================================================
// Dialog 관리 함수들
// ============================================================================

/**
 * 수정 Dialog 열기
 * @param {HTMLElement} policyCard - 정책 카드 요소
 */
function openEditDialog(policyCard) {
  // 개별 data-* 속성에서 정책 정보 가져오기
  const policyId = policyCard.dataset.policyId;
  const policyName = policyCard.dataset.policyName;
  const policyValue = parseInt(policyCard.dataset.policyValue);
  const policyDescription = policyCard.dataset.policyDescription || "";
  const policyActive = policyCard.dataset.policyActive === "true";

  // 폼에 데이터 채우기
  document.getElementById("edit-policy-id").value = policyId;
  document.getElementById("edit-name").value = policyName;
  document.getElementById("edit-point-value").value = policyValue;
  document.getElementById("edit-description").value = policyDescription;
  document.getElementById("edit-is-active").checked = policyActive;

  // Dialog 열기
  document.getElementById("edit-policy-dialog").showModal();
}

/**
 * 삭제 확인 Dialog 열기
 * @param {string} policyId - 정책 UUID
 * @param {string} policyName - 정책 이름
 */
function openDeleteDialog(policyId, policyName) {
  document.getElementById("delete-policy-id").value = policyId;
  document.getElementById(
    "delete-policy-message"
  ).textContent = `"${policyName}" 정책을 삭제하시겠습니까?`;

  document.getElementById("delete-policy-dialog").showModal();
}

// ============================================================================
// DOM 업데이트 함수들
// ============================================================================

/**
 * 새 정책 카드를 그리드에 추가
 * @param {Object} policyData - 정책 데이터
 */
function addPolicyCard(policyData) {
  const grid = document.querySelector(".policy-card-container");

  // Empty state 제거
  const emptyState = grid.querySelector(".col-span-full");
  if (emptyState) {
    emptyState.remove();
  }

  // 새 카드 HTML 생성
  const cardHTML = createPolicyCardHTML(policyData);

  // 그리드 맨 앞에 추가
  grid.insertAdjacentHTML("afterbegin", cardHTML);

  // Lucide 아이콘 재초기화
  lucide.createIcons();
}

/**
 * 기존 정책 카드 업데이트
 * @param {string} policyId - 정책 UUID
 * @param {Object} policyData - 업데이트된 정책 데이터
 */
function updatePolicyCard(policyId, policyData) {
  const card = document.querySelector(`[data-policy-id="${policyId}"]`);
  if (!card) return;

  // 카드 내용 업데이트
  card.querySelector("h3").textContent = policyData.name;
  card.querySelector(".text-3xl").innerHTML = formatPointValue(
    policyData.default_point_value
  );
  card.querySelector(".text-sm").textContent =
    policyData.description || "설명 없음";

  // 활성 상태 뱃지 업데이트
  const badge = card.querySelector(".badge");
  if (policyData.is_active) {
    badge.className = "badge badge-primary";
    badge.textContent = "활성";
  } else {
    badge.className = "badge badge-secondary";
    badge.textContent = "비활성";
  }

  // 개별 data-* 속성 업데이트
  card.dataset.policyId = policyData.id;
  card.dataset.policyName = policyData.name;
  card.dataset.policyValue = policyData.default_point_value;
  card.dataset.policyDescription = policyData.description || "";
  card.dataset.policyActive = policyData.is_active;

  // Lucide 아이콘 재초기화
  lucide.createIcons();
}

/**
 * 정책 카드 제거
 * @param {string} policyId - 정책 UUID
 */
function removePolicyCard(policyId) {
  const card = document.querySelector(`[data-policy-id="${policyId}"]`);
  if (card) {
    card.remove();
    checkEmptyState();
  }
}

/**
 * Empty state 확인 및 표시
 */
function checkEmptyState() {
  const grid = document.querySelector(".policy-card-container");
  const cards = grid.querySelectorAll(".card[data-policy-id]");

  if (cards.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full text-center py-12">
        <i data-lucide="inbox" class="w-16 h-16 mx-auto mb-4 text-gray-400"></i>
        <p class="text-gray-500 text-lg">아직 정책이 없습니다</p>
        <p class="text-gray-400 text-sm mt-2">새 정책을 추가하여 시작하세요.</p>
      </div>
    `;
    lucide.createIcons();
  }
}

/**
 * 정책 카드 HTML 템플릿 생성
 * @param {Object} policy - 정책 데이터
 * @returns {string} 카드 HTML
 */
function createPolicyCardHTML(policy) {
  const badgeClass = policy.is_active ? "badge-primary" : "badge-secondary";
  const badgeText = policy.is_active ? "활성" : "비활성";

  return `
    <div class="card"
         data-policy-id="${policy.id}"
         data-policy-name="${policy.name}"
         data-policy-value="${policy.default_point_value}"
         data-policy-description="${policy.description || ""}"
         data-policy-active="${policy.is_active}">
      <header>
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold">${policy.name}</h3>
          <span class="badge ${badgeClass}">${badgeText}</span>
        </div>
      </header>

      <section>
        <div class="mb-4">
          <p class="text-3xl font-bold text-gray-900">
            ${formatPointValue(policy.default_point_value)}
          </p>
        </div>
        <p class="text-sm text-gray-600">
          ${policy.description || "설명 없음"}
        </p>
      </section>

      <footer class="flex gap-2">
        <button
          type="button"
          class="btn-outline flex-1"
          data-action="edit-policy"
          data-policy-id="${policy.id}">
          <i data-lucide="edit" class="w-4 h-4"></i>
          <span>수정</span>
        </button>
        <button
          type="button"
          class="btn-destructive flex-1"
          data-action="delete-policy"
          data-policy-id="${policy.id}"
          data-policy-name="${policy.name}">
          <i data-lucide="trash-2" class="w-4 h-4"></i>
          <span>삭제</span>
        </button>
      </footer>
    </div>
  `;
}

// ============================================================================
// 유틸리티 함수들
// ============================================================================

/**
 * 포인트 값에 따라 색상이 적용된 HTML 반환
 * @param {number} value - 포인트 값
 * @returns {string} 포맷된 HTML
 */
function formatPointValue(value) {
  if (value > 0) {
    return `<span class="text-emerald-600">+${value}P</span>`;
  } else if (value < 0) {
    return `<span class="text-red-600">${value}P</span>`;
  } else {
    return `<span class="text-gray-600">${value}P</span>`;
  }
}

/**
 * 버튼 로딩 상태 설정
 * @param {HTMLButtonElement} button - 버튼 요소
 * @param {boolean} isLoading - 로딩 상태
 */
function setButtonLoading(button, isLoading) {
  if (isLoading) {
    button.disabled = true;
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = "<span>처리 중...</span>";
  } else {
    button.disabled = false;
    button.innerHTML = button.dataset.originalText;
  }
}

/**
 * API 에러 처리
 * @param {Error|ApiError} error - 에러 객체
 */
function handleApiError(error) {
  if (error instanceof ApiError) {
    if (error.isValidationError()) {
      showToast("error", "입력 오류", error.message);
    } else if (error.isUnauthorized()) {
      showToast("error", "권한 없음", "교사 권한이 필요합니다.");
    } else if (error.isNotFound()) {
      showToast("error", "찾을 수 없음", "정책을 찾을 수 없습니다.");
    } else if (error.isServerError()) {
      showToast("error", "서버 오류", "잠시 후 다시 시도해주세요.");
    } else {
      showToast("error", "오류", error.message);
    }
  } else {
    showToast("error", "네트워크 오류", "연결을 확인해주세요.");
  }
}

/**
 * Basecoat Toast 메시지 표시
 * @param {string} category - success, error, warning, info
 * @param {string} title - 제목
 * @param {string} description - 설명
 */
function showToast(category, title, description) {
  document.dispatchEvent(
    new CustomEvent("basecoat:toast", {
      detail: {
        config: {
          category,
          title,
          description: description || "",
          duration: 3000,
        },
      },
    })
  );
}

// ============================================================================
// 초기화 함수 (이벤트 위임)
// ============================================================================

/**
 * 정책 관리 페이지 초기화
 * 모든 이벤트 리스너 등록 및 이벤트 위임 설정
 */
export function initPolicyManagement() {
  // 생성 Dialog 열기
  const createBtn = document.querySelector(
    '[data-action="open-create-dialog"]'
  );
  createBtn?.addEventListener("click", () => {
    document.getElementById("create-policy-dialog").showModal();
  });

  // 생성 저장
  const createSaveBtn = document.querySelector('[data-action="save-create"]');
  createSaveBtn?.addEventListener("click", handleCreatePolicy);

  // 수정 저장
  const editSaveBtn = document.querySelector('[data-action="save-edit"]');
  editSaveBtn?.addEventListener("click", handleEditPolicy);

  // 삭제 확인
  const deleteConfirmBtn = document.querySelector(
    '[data-action="confirm-delete"]'
  );
  deleteConfirmBtn?.addEventListener("click", handleDeletePolicy);

  // 이벤트 위임 - 동적으로 추가되는 카드에도 작동
  document.addEventListener("click", (e) => {
    // 수정 버튼 클릭
    const editBtn = e.target.closest('[data-action="edit-policy"]');
    if (editBtn) {
      const policyCard = editBtn.closest(".card");
      openEditDialog(policyCard);
      return;
    }

    // 삭제 버튼 클릭
    const deleteBtn = e.target.closest('[data-action="delete-policy"]');
    if (deleteBtn) {
      const policyId = deleteBtn.dataset.policyId;
      const policyName = deleteBtn.dataset.policyName;
      openDeleteDialog(policyId, policyName);
      return;
    }
  });

  // Lucide 아이콘 초기화
  lucide.createIcons();
}
