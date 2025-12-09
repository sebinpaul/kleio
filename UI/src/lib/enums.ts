export enum Platform {
  REDDIT = "reddit",
  HACKERNEWS = "hackernews",
  TWITTER = "twitter",
  FACEBOOK = "facebook",
  LINKEDIN = "linkedin",
  QUORA = "quora",
  YOUTUBE = "youtube",
  BOTH = "both", // For keywords that monitor multiple platforms
}

export enum NotificationFrequency {
  INSTANT = "instant",
  HOURLY = "hourly",
  DAILY = "daily",
}

export enum CaseSensitivity {
  CASE_INSENSITIVE = "case_insensitive",
  CASE_SENSITIVE = "case_sensitive",
  SMART_CASE = "smart_case",
}

export enum MatchMode {
  EXACT = "exact",
  CONTAINS = "contains",
  WORD_BOUNDARY = "word_boundary",
  STARTS_WITH = "starts_with",
  ENDS_WITH = "ends_with",
}

export enum ContentType {
  TITLES = "titles",
  BODY = "body",
  COMMENTS = "comments",
}

export const PlatformLabels: Record<Platform, string> = {
  [Platform.REDDIT]: "Reddit",
  [Platform.HACKERNEWS]: "Hacker News",
  [Platform.TWITTER]: "Twitter",
  [Platform.FACEBOOK]: "Facebook",
  [Platform.LINKEDIN]: "LinkedIn",
  [Platform.QUORA]: "Quora",
  [Platform.YOUTUBE]: "YouTube",
  [Platform.BOTH]: "Both",
};

export const PlatformFilterLabels: Record<Platform, string> = {
  [Platform.REDDIT]: "Subreddits",
  [Platform.HACKERNEWS]: "Categories",
  [Platform.TWITTER]: "Hashtags",
  [Platform.FACEBOOK]: "Pages",
  [Platform.LINKEDIN]: "Companies",
  [Platform.QUORA]: "Topics",
  [Platform.YOUTUBE]: "Channels",
  [Platform.BOTH]: "Filters",
};

export const PlatformPlaceholders: Record<Platform, string> = {
  [Platform.REDDIT]: "technology, programming, java (comma separated)",
  [Platform.HACKERNEWS]: "tech, startup, ai (comma separated)",
  [Platform.TWITTER]: "#tech, #programming, #ai (comma separated)",
  [Platform.FACEBOOK]: "cnn, nasa, page slugs (comma separated)",
  [Platform.LINKEDIN]: "Google, Microsoft, Apple (comma separated)",
  [Platform.QUORA]: "topic URLs or leave empty (comma separated)",
  [Platform.YOUTUBE]: "channels or leave empty (comma separated)",
  [Platform.BOTH]: "filter1, filter2, filter3 (comma separated)",
};

export const PlatformDescriptions: Record<Platform, string> = {
  [Platform.REDDIT]: "Leave empty to monitor all public subreddits",
  [Platform.HACKERNEWS]: "Leave empty to monitor all stories",
  [Platform.TWITTER]: "Leave empty to monitor all tweets",
  [Platform.FACEBOOK]: "Provide Page IDs/usernames/URLs in Settings",
  [Platform.LINKEDIN]: "Leave empty to monitor all posts",
  [Platform.QUORA]: "Leave empty to monitor search; add topics in Settings",
  [Platform.YOUTUBE]: "Leave empty to monitor all videos",
  [Platform.BOTH]: "Leave empty to monitor all sources",
};

export const CaseSensitivityLabels: Record<CaseSensitivity, string> = {
  [CaseSensitivity.CASE_INSENSITIVE]: "Case Insensitive",
  [CaseSensitivity.CASE_SENSITIVE]: "Case Sensitive",
  [CaseSensitivity.SMART_CASE]: "Smart Case",
};

export const MatchModeLabels: Record<MatchMode, string> = {
  [MatchMode.EXACT]: "Exact Match",
  [MatchMode.CONTAINS]: "Contains",
  [MatchMode.WORD_BOUNDARY]: "Word Boundary",
  [MatchMode.STARTS_WITH]: "Starts With",
  [MatchMode.ENDS_WITH]: "Ends With",
};

export const ContentTypeLabels: Record<ContentType, string> = {
  [ContentType.TITLES]: "Post Titles",
  [ContentType.BODY]: "Post Body",
  [ContentType.COMMENTS]: "Comments",
}; 