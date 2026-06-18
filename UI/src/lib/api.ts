import { useAuth, useClerk } from "@clerk/nextjs";
import { useCallback, useMemo } from "react";
import { Platform, MatchMode, ContentType } from "./enums";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type GetToken = () => Promise<string | null>;

type ApiAuthHandlers = {
  getToken: GetToken;
  onUnauthorized: () => Promise<void>;
};

export class ApiUnauthorizedError extends Error {
  constructor() {
    super("Session expired or unauthorized");
    this.name = "ApiUnauthorizedError";
  }
}

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

class ApiService {
  private async getHeaders(auth: ApiAuthHandlers): Promise<HeadersInit> {
    const token = await auth.getToken();
    if (!token) {
      await auth.onUnauthorized();
      throw new ApiUnauthorizedError();
    }

    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  }

  private async request(
    auth: ApiAuthHandlers,
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> {
    const response = await fetch(input, init);

    if (response.status === 401) {
      await auth.onUnauthorized();
      throw new ApiUnauthorizedError();
    }

    return response;
  }

  private async parseJson<T>(response: Response, fallbackMessage: string): Promise<T> {
    if (!response.ok) {
      throw new Error(fallbackMessage);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  async createKeyword(request: KeywordRequest, auth: ApiAuthHandlers): Promise<Keyword> {
    const endpoint = request.platform
      ? `${API_BASE_URL}/api/platforms/${request.platform}/keywords`
      : `${API_BASE_URL}/api/keywords`;

    const response = await this.request(auth, endpoint, {
      method: "POST",
      headers: await this.getHeaders(auth),
      body: JSON.stringify(request),
    });

    return this.parseJson(response, "Failed to create keyword");
  }

  async getUserKeywords(auth: ApiAuthHandlers, platform?: string): Promise<Keyword[]> {
    const endpoint = platform
      ? `${API_BASE_URL}/api/platforms/${platform}/keywords`
      : `${API_BASE_URL}/api/keywords`;

    const response = await this.request(auth, endpoint, {
      method: "GET",
      headers: await this.getHeaders(auth),
    });

    return this.parseJson(response, "Failed to fetch keywords");
  }

  async updateKeyword(
    id: string,
    request: KeywordRequest,
    auth: ApiAuthHandlers
  ): Promise<Keyword> {
    const endpoint = request.platform
      ? `${API_BASE_URL}/api/platforms/${request.platform}/keywords/${id}`
      : `${API_BASE_URL}/api/keywords/${id}`;

    const response = await this.request(auth, endpoint, {
      method: "PUT",
      headers: await this.getHeaders(auth),
      body: JSON.stringify(request),
    });

    return this.parseJson(response, "Failed to update keyword");
  }

  async deleteKeyword(
    id: string,
    auth: ApiAuthHandlers,
    platform?: string
  ): Promise<void> {
    const endpoint = platform
      ? `${API_BASE_URL}/api/platforms/${platform}/keywords/${id}`
      : `${API_BASE_URL}/api/keywords/${id}`;

    const response = await this.request(auth, endpoint, {
      method: "DELETE",
      headers: await this.getHeaders(auth),
    });

    await this.parseJson(response, "Failed to delete keyword");
  }

  async toggleKeyword(
    id: string,
    auth: ApiAuthHandlers,
    platform?: string
  ): Promise<Keyword> {
    const endpoint = platform
      ? `${API_BASE_URL}/api/platforms/${platform}/keywords/${id}/toggle`
      : `${API_BASE_URL}/api/keywords/${id}/toggle`;

    const response = await this.request(auth, endpoint, {
      method: "PATCH",
      headers: await this.getHeaders(auth),
    });

    return this.parseJson(response, "Failed to toggle keyword");
  }
}

export const apiService = new ApiService();

export function useApi() {
  const { getToken, signOut } = useAuth();
  const { redirectToSignIn } = useClerk();

  const onUnauthorized = useCallback(async () => {
    await signOut();
    redirectToSignIn();
  }, [signOut, redirectToSignIn]);

  const auth = useMemo(
    () => ({ getToken, onUnauthorized }),
    [getToken, onUnauthorized]
  );

  return {
    createKeyword: (request: KeywordRequest) =>
      apiService.createKeyword(request, auth),
    getUserKeywords: (platform?: string) =>
      apiService.getUserKeywords(auth, platform),
    updateKeyword: (id: string, request: KeywordRequest) =>
      apiService.updateKeyword(id, request, auth),
    deleteKeyword: (id: string, platform?: string) =>
      apiService.deleteKeyword(id, auth, platform),
    toggleKeyword: (id: string, platform?: string) =>
      apiService.toggleKeyword(id, auth, platform),
  };
}
