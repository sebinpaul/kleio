export enum Platform {
  REDDIT = "reddit",
  HACKERNEWS = "hackernews",
  TWITTER = "twitter",
  YOUTUBE = "youtube",
  BOTH = "both",
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
  [Platform.YOUTUBE]: "YouTube",
  [Platform.BOTH]: "Both",
};

export const PlatformFilterLabels: Record<Platform, string> = {
  [Platform.REDDIT]: "Subreddits",
  [Platform.HACKERNEWS]: "Story filters",
  [Platform.TWITTER]: "From accounts",
  [Platform.YOUTUBE]: "Channels",
  [Platform.BOTH]: "Sources",
};

export const PlatformPlaceholders: Record<Platform, string> = {
  [Platform.REDDIT]: "technology",
  [Platform.HACKERNEWS]: "startup",
  [Platform.TWITTER]: "elonmusk",
  [Platform.YOUTUBE]: "mkbhd",
  [Platform.BOTH]: "source-name",
};

export const PlatformDescriptions: Record<Platform, string> = {
  [Platform.REDDIT]: "Limit monitoring to specific subreddits. Leave empty to scan all public subreddits.",
  [Platform.HACKERNEWS]: "Optional source filters for Hacker News. Leave empty to monitor all stories.",
  [Platform.TWITTER]: "Limit monitoring to tweets from specific accounts (without @). Leave empty to search all public tweets for your keyword.",
  [Platform.YOUTUBE]: "Limit monitoring to specific YouTube channels. Leave empty to search all videos.",
  [Platform.BOTH]: "Limit monitoring to specific sources. Leave empty to monitor everywhere.",
};

export const PlatformFilterTooltips: Record<Platform, string> = {
  [Platform.REDDIT]: "Only monitor posts and comments in these subreddits. Example: technology, programming.",
  [Platform.HACKERNEWS]: "Optional filters for Hacker News content sources.",
  [Platform.TWITTER]: "Only notify you when these accounts post tweets matching your keyword. This is not for hashtag tracking — your main keyword is still searched across tweet text.",
  [Platform.YOUTUBE]: "Only monitor videos published by these channels.",
  [Platform.BOTH]: "Optional source filters applied across platforms.",
};

export const CaseSensitivityLabels: Record<CaseSensitivity, string> = {
  [CaseSensitivity.CASE_INSENSITIVE]: "Case Insensitive",
  [CaseSensitivity.CASE_SENSITIVE]: "Case Sensitive",
  [CaseSensitivity.SMART_CASE]: "Smart Case",
};

export const MatchModeLabels: Record<MatchMode, string> = {
  [MatchMode.EXACT]: "Exact Match",
  [MatchMode.CONTAINS]: "Contains",
  [MatchMode.WORD_BOUNDARY]: "Whole Word",
  [MatchMode.STARTS_WITH]: "Starts With",
  [MatchMode.ENDS_WITH]: "Ends With",
};

export const MatchModeDescriptions: Record<MatchMode, string> = {
  [MatchMode.EXACT]: "The entire text must exactly equal your keyword.",
  [MatchMode.CONTAINS]: "Matches when your keyword appears anywhere in the text.",
  [MatchMode.WORD_BOUNDARY]: "Matches only when your keyword appears as a complete word (e.g. \"python\" won't match \"pythonic\").",
  [MatchMode.STARTS_WITH]: "Matches when the text starts with your keyword.",
  [MatchMode.ENDS_WITH]: "Matches when the text ends with your keyword.",
};

export const ContentTypeLabels: Record<ContentType, string> = {
  [ContentType.TITLES]: "Post Titles",
  [ContentType.BODY]: "Post Body",
  [ContentType.COMMENTS]: "Comments",
};

export const ContentTypeDescriptions: Record<ContentType, string> = {
  [ContentType.TITLES]: "Monitor titles of posts, stories, or videos.",
  [ContentType.BODY]: "Monitor the main body text of posts or descriptions.",
  [ContentType.COMMENTS]: "Monitor replies and comments on posts.",
};

export function getMatchModeLabel(matchMode?: MatchMode): string {
  if (matchMode === MatchMode.WORD_BOUNDARY) return "Whole words only";
  if (matchMode === MatchMode.EXACT) return "Exact";
  if (matchMode === MatchMode.STARTS_WITH) return "Starts with";
  if (matchMode === MatchMode.ENDS_WITH) return "Ends with";
  return "Contains";
}

export const FIELD_TOOLTIPS = {
  keyword: "The primary term you want to track mentions of across the selected platform.",
  excludedKeywords: "If any of these words appear in the same content as your main keyword, you will not be notified. Useful to filter noise like \"python snake\" when tracking the Python language.",
  excludedSubreddits: "Never notify for mentions found in these subreddits, even if your keyword matches.",
  includedUsers: "Only notify when the author is one of these users. Leave empty to allow all authors.",
  excludedUsers: "Never notify when the author is one of these users.",
  includedLanguages: "Only notify when content is detected in these languages. Leave empty to allow all languages. Requires at least ~20 characters of text for detection.",
  excludedLanguages: "Never notify when content is detected in these languages. Short text may not be filtered if language cannot be detected.",
  caseSensitive: "When enabled, \"Python\" will only match \"Python\", not \"python\" or \"PYTHON\".",
  wholeWordsOnly: "When enabled, \"python\" matches \"I love python\" but not \"pythonic\" — the keyword must be a complete word.",
  contentTypes: "Choose which parts of a post to scan for your keyword.",
};

export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "es", label: "Spanish" },
  { code: "fr", label: "French" },
  { code: "de", label: "German" },
  { code: "pt", label: "Portuguese" },
  { code: "it", label: "Italian" },
  { code: "nl", label: "Dutch" },
  { code: "pl", label: "Polish" },
  { code: "sv", label: "Swedish" },
  { code: "ru", label: "Russian" },
  { code: "ar", label: "Arabic" },
  { code: "hi", label: "Hindi" },
  { code: "ja", label: "Japanese" },
  { code: "ko", label: "Korean" },
  { code: "zh", label: "Chinese" },
];

export const DEFAULT_CONTENT_TYPES: Record<Platform, ContentType[]> = {
  [Platform.REDDIT]: [ContentType.TITLES, ContentType.BODY, ContentType.COMMENTS],
  [Platform.HACKERNEWS]: [ContentType.TITLES, ContentType.BODY, ContentType.COMMENTS],
  [Platform.TWITTER]: [ContentType.TITLES, ContentType.BODY, ContentType.COMMENTS],
  [Platform.YOUTUBE]: [ContentType.TITLES, ContentType.BODY, ContentType.COMMENTS],
  [Platform.BOTH]: [ContentType.TITLES, ContentType.BODY, ContentType.COMMENTS],
};

export function getAvailableContentTypes(platform: Platform): ContentType[] {
  return DEFAULT_CONTENT_TYPES[platform] ?? DEFAULT_CONTENT_TYPES[Platform.REDDIT];
}

export function showPlatformSourceFilters(platform: Platform): boolean {
  return platform !== Platform.HACKERNEWS;
}
