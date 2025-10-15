/**
 * API Client
 * 모든 HTTP 요청을 처리하는 공통 클라이언트
 * CSRF 토큰 자동 처리, 에러 핸들링 통합
 */

class ApiClient {
  constructor() {
    this.baseHeaders = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
  }

  /**
   * CSRF 토큰 가져오기
   */
  getCsrfToken() {
    const tokenElement = document.querySelector("[name=csrfmiddlewaretoken]");
    return tokenElement ? tokenElement.value : "";
  }

  /**
   * 공통 요청 메서드
   */
  async request(url, options = {}) {
    const config = {
      headers: {
        ...this.baseHeaders,
        "X-CSRFToken": this.getCsrfToken(),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.error || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError("네트워크 오류가 발생했습니다.", 0, error);
    }
  }

  /**
   * GET 요청
   */
  async get(url, options = {}) {
    const { params, ...restOptions } = options;
    const queryString = params
      ? "?" + new URLSearchParams(params).toString()
      : "";
    return this.request(url + queryString, {
      method: "GET",
      ...restOptions,
    });
  }

  /**
   * POST 요청
   */
  async post(url, data = {}, options = {}) {
    return this.request(url, {
      method: "POST",
      body: JSON.stringify(data),
      ...options,
    });
  }

  /**
   * DELETE 요청
   */
  async delete(url, options = {}) {
    return this.request(url, {
      method: "DELETE",
      ...options,
    });
  }
}

/**
 * API 에러 클래스
 */
class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }

  isValidationError() {
    return this.status === 400;
  }

  isUnauthorized() {
    return this.status === 401 || this.status === 403;
  }

  isNotFound() {
    return this.status === 404;
  }

  isServerError() {
    return this.status >= 500;
  }
}

// Singleton 인스턴스
export const apiClient = new ApiClient();
export { ApiError };
