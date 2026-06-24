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
  excludedKeywords?: string[];
  excludedSubreddits?: string[];
  includedUsers?: string[];
  excludedUsers?: string[];
  includedLanguages?: string[];
  excludedLanguages?: string[];
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
  excludedKeywords?: string[];
  excludedSubreddits?: string[];
  includedUsers?: string[];
  excludedUsers?: string[];
  includedLanguages?: string[];
  excludedLanguages?: string[];
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

export interface MentionTimelinePoint {
  date: string;
  count: number;
}

export interface KeywordAnalyticsRow extends Keyword {
  lastMentionAt: string | null;
  totalMentions: number;
  mentionsLast7Days: number;
  mentionsPrior7Days: number;
  mentionsInWindow: number;
  trend: "up" | "down" | "flat";
  timeline: MentionTimelinePoint[];
}

export interface KeywordAnalytics {
  summary: {
    totalKeywords: number;
    activeKeywords: number;
    totalMentions: number;
    mentionsLast7Days: number;
    mentionsPrior7Days: number;
    mentionsInWindow: number;
    mentionsPriorWindow: number;
    keywordsAddedLast7Days: number;
    keywordsAddedPrior7Days: number;
    windowDays: number;
  };
  keywords: KeywordAnalyticsRow[];
}

export interface Mention {
  id: string;
  keywordId: string;
  keyword: string;
  userId: string;
  content: string;
  title: string;
  author: string;
  sourceUrl: string;
  platform: Platform;
  subreddit: string;
  contentType: string;
  matchedText: string;
  mentionDate: string | null;
  discoveredAt: string | null;
  platformScore: number | null;
  platformCommentsCount: number | null;
  detectedLanguage: string;
  isRead: boolean;
  isArchived: boolean;
}

export interface MentionsListResponse {
  mentions: Mention[];
  total: number;
  limit: number;
  offset: number;
}

export interface UserNotificationSettings {
  emailNotifications: boolean;
  notificationFrequency: string;
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
      let message = fallbackMessage;
      if (response.status === 429) {
        message = "Too many requests. Please wait a moment and try again.";
      }
      try {
        const body = await response.json();
        if (typeof body?.error === "string") {
          message = body.error;
        } else if (typeof body?.detail === "string") {
          message = body.detail;
        }
      } catch {
        // use fallback
      }
      throw new Error(message);
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

  async getKeywordAnalytics(
    auth: ApiAuthHandlers,
    days?: number,
    platform?: string
  ): Promise<KeywordAnalytics> {
    const params = new URLSearchParams();
    if (days) params.set("days", String(days));
    if (platform) params.set("platform", platform);
    const query = params.toString() ? `?${params.toString()}` : "";
    const response = await this.request(
      auth,
      `${API_BASE_URL}/api/keywords/analytics${query}`,
      {
        method: "GET",
        headers: await this.getHeaders(auth),
      }
    );

    return this.parseJson(response, "Failed to fetch keyword analytics");
  }

  async getMentions(
    auth: ApiAuthHandlers,
    options?: {
      platform?: string;
      keywordId?: string;
      limit?: number;
      offset?: number;
      q?: string;
      status?: "active" | "unread" | "archived" | "all";
    }
  ): Promise<MentionsListResponse> {
    const params = new URLSearchParams();
    if (options?.limit) params.set("limit", String(options.limit));
    if (options?.offset) params.set("offset", String(options.offset));
    if (options?.keywordId) params.set("keywordId", options.keywordId);
    if (options?.q) params.set("q", options.q);
    if (options?.status) params.set("status", options.status);

    const platform = options?.platform;
    const query = params.toString() ? `?${params.toString()}` : "";
    const endpoint = platform
      ? `${API_BASE_URL}/api/platforms/${platform}/mentions${query}`
      : `${API_BASE_URL}/api/mentions${query}`;

    const response = await this.request(auth, endpoint, {
      method: "GET",
      headers: await this.getHeaders(auth),
    });

    return this.parseJson(response, "Failed to fetch mentions");
  }

  async updateMention(
    auth: ApiAuthHandlers,
    id: string,
    data: { isRead?: boolean; isArchived?: boolean }
  ): Promise<Mention> {
    const response = await this.request(auth, `${API_BASE_URL}/api/mentions/${id}`, {
      method: "PATCH",
      headers: await this.getHeaders(auth),
      body: JSON.stringify(data),
    });
    return this.parseJson(response, "Failed to update mention");
  }

  async getNotificationSettings(auth: ApiAuthHandlers): Promise<UserNotificationSettings> {
    const response = await this.request(
      auth,
      `${API_BASE_URL}/api/user/notification-settings`,
      { method: "GET", headers: await this.getHeaders(auth) }
    );
    return this.parseJson(response, "Failed to fetch notification settings");
  }

  async updateNotificationSettings(
    auth: ApiAuthHandlers,
    data: { emailNotifications: boolean }
  ): Promise<UserNotificationSettings> {
    const response = await this.request(
      auth,
      `${API_BASE_URL}/api/user/notification-settings`,
      {
        method: "PATCH",
        headers: await this.getHeaders(auth),
        body: JSON.stringify(data),
      }
    );
    return this.parseJson(response, "Failed to update notification settings");
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

  return useMemo(
    () => ({
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
      getKeywordAnalytics: (days?: number, platform?: string) =>
        apiService.getKeywordAnalytics(auth, days, platform),
      getMentions: (options?: {
        platform?: string;
        keywordId?: string;
        limit?: number;
        offset?: number;
        q?: string;
        status?: "active" | "unread" | "archived" | "all";
      }) => apiService.getMentions(auth, options),
      updateMention: (id: string, data: { isRead?: boolean; isArchived?: boolean }) =>
        apiService.updateMention(auth, id, data),
      getNotificationSettings: () => apiService.getNotificationSettings(auth),
      updateNotificationSettings: (data: { emailNotifications: boolean }) =>
        apiService.updateNotificationSettings(auth, data),
    }),
    [auth]
  );
}
