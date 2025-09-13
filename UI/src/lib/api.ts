import { useUser } from "@clerk/nextjs";
import { Platform, MatchMode, ContentType } from "./enums";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface KeywordRequest {
  keyword: string;
  platform: Platform;
  platformSpecificFilters?: string[];
  platformConfig?: Record<string, unknown>;
  checkFrequency?: number;
  emailNotifications?: boolean;
  slackNotifications?: boolean;
  caseSensitive?: boolean;
  matchMode?: MatchMode;
  contentTypes?: ContentType[];
}

export interface Keyword {
  id: string;
  keyword: string;
  userId: string;
  platform: Platform;
  platformSpecificFilters?: string[];
  platformConfig?: Record<string, unknown>;
  checkFrequency?: number;
  emailNotifications?: boolean;
  slackNotifications?: boolean;
  caseSensitive?: boolean;
  matchMode?: MatchMode;
  contentTypes?: ContentType[];
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ProxyItem {
  id: string;
  url: string;
  is_active: boolean;
  last_failed_at?: string;
  cooldown_until?: string;
  created_at: string;
  updated_at: string;
}

class ApiService {
  private async getHeaders(userId?: string): Promise<HeadersInit> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    if (userId) {
      headers["X-User-ID"] = userId;
    }

    return headers;
  }

  // Proxies
  async listProxies(): Promise<ProxyItem[]> {
    const response = await fetch(`${API_BASE_URL}/api/proxies`, {
      method: "GET",
      headers: await this.getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to load proxies");
    return response.json();
  }

  async createProxy(url: string): Promise<ProxyItem> {
    const response = await fetch(`${API_BASE_URL}/api/proxies`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: JSON.stringify({ url, is_active: true }),
    });
    if (!response.ok) throw new Error("Failed to create proxy");
    return response.json();
  }

  async deleteProxy(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/proxies/${id}`, {
      method: "DELETE",
      headers: await this.getHeaders(),
    });
    if (!response.ok) throw new Error("Failed to delete proxy");
  }

  async uploadProxiesCsv(text: string): Promise<{ created: number; total: number }> {
    const response = await fetch(`${API_BASE_URL}/api/proxies/upload-csv`, {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: text,
    });
    if (!response.ok) throw new Error("Failed to upload proxies");
    return response.json();
  }

  // Platform-specific endpoints
  async createKeyword(
    request: KeywordRequest,
    userId: string
  ): Promise<Keyword> {
    const endpoint = request.platform
      ? `${API_BASE_URL}/api/platforms/${request.platform}/keywords`
      : `${API_BASE_URL}/api/keywords`;

    const response = await fetch(endpoint, {
      method: "POST",
      headers: await this.getHeaders(userId),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error("Failed to create keyword");
    }

    return response.json();
  }

  async getUserKeywords(userId: string, platform?: string): Promise<Keyword[]> {
    const endpoint = platform
      ? `${API_BASE_URL}/api/platforms/${platform}/keywords`
      : `${API_BASE_URL}/api/keywords`;

    const response = await fetch(endpoint, {
      method: "GET",
      headers: await this.getHeaders(userId),
    });

    if (!response.ok) {
      console.log(response.json())
      throw new Error("Failed to fetch keywords");
    }

    return response.json();
  }

  async updateKeyword(
    id: string,
    request: KeywordRequest,
    userId: string
  ): Promise<Keyword> {
    const endpoint = request.platform
      ? `${API_BASE_URL}/api/platforms/${request.platform}/keywords/${id}`
      : `${API_BASE_URL}/api/keywords/${id}`;

    const response = await fetch(endpoint, {
      method: "PUT",
      headers: await this.getHeaders(userId),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error("Failed to update keyword");
    }

    return response.json();
  }

  async deleteKeyword(
    id: string,
    userId: string,
    platform?: string
  ): Promise<void> {
    const endpoint = platform
      ? `${API_BASE_URL}/api/platforms/${platform}/keywords/${id}`
      : `${API_BASE_URL}/api/keywords/${id}`;

    const response = await fetch(endpoint, {
      method: "DELETE",
      headers: await this.getHeaders(userId),
    });

    if (!response.ok) {
      throw new Error("Failed to delete keyword");
    }
  }

  async toggleKeyword(
    id: string,
    userId: string,
    platform?: string
  ): Promise<Keyword> {
    const endpoint = platform
      ? `${API_BASE_URL}/api/platforms/${platform}/keywords/${id}/toggle`
      : `${API_BASE_URL}/api/keywords/${id}/toggle`;

    const response = await fetch(endpoint, {
      method: "PATCH",
      headers: await this.getHeaders(userId),
    });

    if (!response.ok) {
      throw new Error("Failed to toggle keyword");
    }

    return response.json();
  }
}

export const apiService = new ApiService();

// Hook to use API with current user
export function useApi() {
  const { user } = useUser();

  return {
    // proxies
    listProxies: () => apiService.listProxies(),
    createProxy: (url: string) => apiService.createProxy(url),
    deleteProxy: (id: string) => apiService.deleteProxy(id),
    uploadProxiesCsv: (text: string) => apiService.uploadProxiesCsv(text),

    // keywords
    createKeyword: (request: KeywordRequest) =>
      apiService.createKeyword(request, user?.id || ""),
    getUserKeywords: (platform?: string) =>
      apiService.getUserKeywords(user?.id || "", platform),
    updateKeyword: (id: string, request: KeywordRequest) =>
      apiService.updateKeyword(id, request, user?.id || ""),
    deleteKeyword: (id: string, platform?: string) =>
      apiService.deleteKeyword(id, user?.id || "", platform),
    toggleKeyword: (id: string, platform?: string) =>
      apiService.toggleKeyword(id, user?.id || "", platform),
  };
}
