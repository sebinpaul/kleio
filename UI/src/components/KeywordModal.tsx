"use client";
import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useApi, KeywordRequest, Keyword, ApiUnauthorizedError } from "@/lib/api";
import {
  Platform,
  PlatformLabels,
  PlatformFilterLabels,
  PlatformPlaceholders,
  PlatformDescriptions,
  PlatformFilterTooltips,
  MatchMode,
  ContentType,
  ContentTypeLabels,
  ContentTypeDescriptions,
  FIELD_TOOLTIPS,
  SUPPORTED_LANGUAGES,
  getAvailableContentTypes,
  showPlatformSourceFilters,
} from "@/lib/enums";
import { Badge } from "@/components/ui/badge";
import ChipInput from "@/components/ChipInput";
import FieldLabel from "@/components/FieldLabel";
import LanguageMultiSelect from "@/components/LanguageMultiSelect";

type KeywordModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onKeywordSaved: () => void;
  platform?: string;
  keyword?: Keyword;
};

type WizardStep = 1 | 2 | 3 | 4;

const STEPS = [
  { id: 1 as WizardStep, label: "Keyword" },
  { id: 2 as WizardStep, label: "Filters" },
  { id: 3 as WizardStep, label: "Matching" },
  { id: 4 as WizardStep, label: "Review" },
];

const stripPrefix = (value: string) =>
  value.trim().replace(/^@/, "").replace(/^r\//i, "");

function getDefaultContentTypes(platform?: string): ContentType[] {
  const key = (platform as Platform) || Platform.REDDIT;
  return getAvailableContentTypes(key);
}

function sanitizeContentTypes(types: ContentType[] | undefined, platform: Platform): ContentType[] {
  const allowed = getAvailableContentTypes(platform);
  const filtered = (types || []).filter((t) => allowed.includes(t));
  return filtered.length > 0 ? filtered : [...allowed];
}

function formatLanguageList(codes: string[]): string {
  if (!codes.length) return "None";
  const labels = new Map(SUPPORTED_LANGUAGES.map((lang) => [lang.code, lang.label]));
  return codes.map((code) => labels.get(code) || code).join(", ");
}

function ChipList({ items }: { items: string[] }) {
  if (!items.length) return <span className="text-slate-500">None</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item) => (
        <Badge key={item} variant="outline">{item}</Badge>
      ))}
    </div>
  );
}

export default function KeywordModal({
  isOpen,
  onClose,
  onKeywordSaved,
  platform,
  keyword: editKeyword,
}: KeywordModalProps) {
  const api = useApi();
  const [currentStep, setCurrentStep] = useState<WizardStep>(1);
  const [keyword, setKeyword] = useState(editKeyword?.keyword || "");
  const [platformFilters, setPlatformFilters] = useState<string[]>(
    editKeyword?.platformSpecificFilters || []
  );
  const [excludedKeywords, setExcludedKeywords] = useState<string[]>(
    editKeyword?.excludedKeywords || []
  );
  const [excludedSubreddits, setExcludedSubreddits] = useState<string[]>(
    editKeyword?.excludedSubreddits || []
  );
  const [includedUsers, setIncludedUsers] = useState<string[]>(
    editKeyword?.includedUsers || []
  );
  const [excludedUsers, setExcludedUsers] = useState<string[]>(
    editKeyword?.excludedUsers || []
  );
  const [includedLanguages, setIncludedLanguages] = useState<string[]>(
    editKeyword?.includedLanguages || []
  );
  const [excludedLanguages, setExcludedLanguages] = useState<string[]>(
    editKeyword?.excludedLanguages || []
  );
  const [caseSensitive, setCaseSensitive] = useState(editKeyword?.caseSensitive || false);
  const [wholeWordsOnly, setWholeWordsOnly] = useState(
    editKeyword?.matchMode === MatchMode.WORD_BOUNDARY
  );
  const [contentTypes, setContentTypes] = useState<ContentType[]>(
    editKeyword?.contentTypes || getDefaultContentTypes(platform)
  );
  const [emailNotifications, setEmailNotifications] = useState(
    editKeyword?.emailNotifications ?? true
  );
  const [slackNotifications, setSlackNotifications] = useState(
    editKeyword?.slackNotifications ?? false
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activePlatform =
    (editKeyword?.platform as Platform) ||
    (platform as Platform) ||
    Platform.REDDIT;
  const isReddit = activePlatform === Platform.REDDIT;
  const showSourceFilters = showPlatformSourceFilters(activePlatform);
  const availableContentTypes = getAvailableContentTypes(activePlatform);

  const resetForm = (source?: Keyword) => {
    if (source) {
      setKeyword(source.keyword);
      setPlatformFilters(source.platformSpecificFilters || []);
      setExcludedKeywords(source.excludedKeywords || []);
      setExcludedSubreddits(source.excludedSubreddits || []);
      setIncludedUsers(source.includedUsers || []);
      setExcludedUsers(source.excludedUsers || []);
      setIncludedLanguages(source.includedLanguages || []);
      setExcludedLanguages(source.excludedLanguages || []);
      setCaseSensitive(source.caseSensitive || false);
      setWholeWordsOnly(source.matchMode === MatchMode.WORD_BOUNDARY);
      setContentTypes(sanitizeContentTypes(source.contentTypes, source.platform as Platform));
      setEmailNotifications(source.emailNotifications ?? true);
      setSlackNotifications(source.slackNotifications ?? false);
    } else {
      setKeyword("");
      setPlatformFilters([]);
      setExcludedKeywords([]);
      setExcludedSubreddits([]);
      setIncludedUsers([]);
      setExcludedUsers([]);
      setIncludedLanguages([]);
      setExcludedLanguages([]);
      setCaseSensitive(false);
      setWholeWordsOnly(false);
      setContentTypes(getDefaultContentTypes(platform));
      setEmailNotifications(true);
      setSlackNotifications(false);
    }
    setCurrentStep(1);
    setError(null);
  };

  React.useEffect(() => {
    resetForm(editKeyword);
  }, [editKeyword, platform]);

  React.useEffect(() => {
    if (isOpen) {
      setCurrentStep(1);
      setError(null);
    }
  }, [isOpen]);

  const buildRequest = (): KeywordRequest => ({
    keyword: keyword.trim(),
    platform: activePlatform,
    platformSpecificFilters: platformFilters,
    excludedKeywords: excludedKeywords,
    excludedSubreddits: excludedSubreddits,
    includedUsers: includedUsers,
    excludedUsers: excludedUsers,
    includedLanguages: includedLanguages,
    excludedLanguages: excludedLanguages,
    caseSensitive,
    matchMode: wholeWordsOnly ? MatchMode.WORD_BOUNDARY : MatchMode.CONTAINS,
    contentTypes,
    emailNotifications,
    slackNotifications,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (contentTypes.length === 0) {
      setError("Select at least one content type to monitor.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const request = buildRequest();
      if (editKeyword) {
        await api.updateKeyword(editKeyword.id, request);
      } else {
        await api.createKeyword(request);
      }
      resetForm();
      onClose();
      onKeywordSaved?.();
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
      console.error(editKeyword ? "Error updating keyword:" : "Error creating keyword:", err);
      setError(
        err instanceof Error
          ? err.message
          : editKeyword
            ? "Failed to update keyword. Please try again."
            : "Failed to create keyword. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const nextStep = () => {
    if (currentStep === 3 && contentTypes.length === 0) {
      setError("Select at least one content type to monitor.");
      return;
    }
    setError(null);
    if (currentStep < 4) setCurrentStep((prev) => (prev + 1) as WizardStep);
  };

  const prevStep = () => {
    setError(null);
    if (currentStep > 1) setCurrentStep((prev) => (prev - 1) as WizardStep);
  };

  const isNextDisabled = () => {
    if (currentStep === 1) return !keyword.trim();
    if (currentStep === 3) return contentTypes.length === 0;
    return false;
  };

  const toggleContentType = (type: ContentType, checked: boolean) => {
    if (checked) {
      setContentTypes((prev) => (prev.includes(type) ? prev : [...prev, type]));
    } else {
      setContentTypes((prev) => prev.filter((item) => item !== type));
    }
  };

  const renderStepContent = () => {
    if (currentStep === 1) {
      return (
        <div className="space-y-5">
          <div className="space-y-2">
            <FieldLabel
              htmlFor="keyword"
              label="Keyword"
              tooltip={FIELD_TOOLTIPS.keyword}
              required
            />
            <Input
              id="keyword"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="e.g. your brand name"
              required
              disabled={isLoading}
              className={`h-11 bg-white border-2 font-medium ${
                !keyword.trim()
                  ? "border-red-400 focus:border-red-500 focus:ring-red-200"
                  : "border-slate-300 focus:border-indigo-500 focus:ring-indigo-200"
              }`}
            />
            {!keyword.trim() && (
              <p className="text-sm text-red-600">Keyword is required to continue</p>
            )}
          </div>

          {showSourceFilters ? (
            <div className="space-y-2">
              <FieldLabel
                htmlFor="platformFilters"
                label={`${PlatformFilterLabels[activePlatform]} (optional)`}
                tooltip={PlatformFilterTooltips[activePlatform]}
              />
              <ChipInput
                id="platformFilters"
                values={platformFilters}
                onChange={setPlatformFilters}
                placeholder={`Add ${PlatformPlaceholders[activePlatform]} and press Enter`}
                disabled={isLoading}
                normalize={stripPrefix}
              />
              <p className="text-sm text-slate-500">{PlatformDescriptions[activePlatform]}</p>
            </div>
          ) : (
            <p className="text-sm text-slate-500 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
              Hacker News monitors all public stories and comments for your keyword — no source filters needed.
            </p>
          )}
        </div>
      );
    }

    if (currentStep === 2) {
      return (
        <div className="space-y-5">
          <p className="text-sm text-slate-500">
            All fields below are optional. Skip any you don&apos;t need.
          </p>

          <div className="space-y-2">
            <FieldLabel
              htmlFor="excludedKeywords"
              label="Excluded keywords"
              tooltip={FIELD_TOOLTIPS.excludedKeywords}
            />
            <ChipInput
              id="excludedKeywords"
              values={excludedKeywords}
              onChange={setExcludedKeywords}
              placeholder="Add word and press Enter"
              disabled={isLoading}
            />
          </div>

          {isReddit && (
            <div className="space-y-2">
              <FieldLabel
                htmlFor="excludedSubreddits"
                label="Excluded subreddits"
                tooltip={FIELD_TOOLTIPS.excludedSubreddits}
              />
              <ChipInput
                id="excludedSubreddits"
                values={excludedSubreddits}
                onChange={setExcludedSubreddits}
                placeholder="Add subreddit and press Enter"
                disabled={isLoading}
                normalize={stripPrefix}
              />
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <FieldLabel
                htmlFor="includedUsers"
                label="Included users"
                tooltip={FIELD_TOOLTIPS.includedUsers}
              />
              <ChipInput
                id="includedUsers"
                values={includedUsers}
                onChange={setIncludedUsers}
                placeholder="Username + Enter"
                disabled={isLoading}
                normalize={stripPrefix}
              />
            </div>
            <div className="space-y-2">
              <FieldLabel
                htmlFor="excludedUsers"
                label="Excluded users"
                tooltip={FIELD_TOOLTIPS.excludedUsers}
              />
              <ChipInput
                id="excludedUsers"
                values={excludedUsers}
                onChange={setExcludedUsers}
                placeholder="Username + Enter"
                disabled={isLoading}
                normalize={stripPrefix}
              />
            </div>
          </div>

          <LanguageMultiSelect
            id="includedLanguages"
            label="Included languages"
            tooltip={FIELD_TOOLTIPS.includedLanguages}
            selected={includedLanguages}
            onChange={setIncludedLanguages}
            disabled={isLoading}
          />

          <LanguageMultiSelect
            id="excludedLanguages"
            label="Excluded languages"
            tooltip={FIELD_TOOLTIPS.excludedLanguages}
            selected={excludedLanguages}
            onChange={setExcludedLanguages}
            disabled={isLoading}
          />
        </div>
      );
    }

    if (currentStep === 3) {
      return (
        <div className="space-y-5">
          <div className="space-y-2">
            <FieldLabel label="Whole words only" tooltip={FIELD_TOOLTIPS.wholeWordsOnly} />
            <label className="flex items-center gap-3 cursor-pointer rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
              <input
                type="checkbox"
                checked={wholeWordsOnly}
                onChange={(e) => setWholeWordsOnly(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-sm text-slate-700">
                Match only when the keyword is a complete word (e.g. &quot;python&quot; matches &quot;I love python&quot;, not &quot;pythonic&quot;)
              </span>
            </label>
          </div>

          <div className="space-y-2">
            <FieldLabel label="Case sensitive" tooltip={FIELD_TOOLTIPS.caseSensitive} />
            <label className="flex items-center gap-3 cursor-pointer rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
              <input
                type="checkbox"
                checked={caseSensitive}
                onChange={(e) => setCaseSensitive(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-sm text-slate-700">
                Require exact letter casing when matching
              </span>
            </label>
          </div>

          <div className="space-y-2">
            <FieldLabel label="Content types" tooltip={FIELD_TOOLTIPS.contentTypes} />
            <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
              {availableContentTypes.map((type) => (
                <label key={type} className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={contentTypes.includes(type)}
                    onChange={(e) => toggleContentType(type, e.target.checked)}
                    className="mt-0.5 w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>
                    <span className="text-sm font-medium text-slate-800 block">
                      {ContentTypeLabels[type]}
                    </span>
                    <span className="text-xs text-slate-500">
                      {ContentTypeDescriptions[type]}
                    </span>
                  </span>
                </label>
              ))}
            </div>
            {contentTypes.length === 0 && (
              <p className="text-sm text-red-600">Select at least one content type</p>
            )}
          </div>

          <div className="space-y-2 pt-1 border-t border-slate-100">
            <FieldLabel label="Notifications" tooltip="Choose how you want to be alerted for this keyword" />
            <label className="flex items-center gap-3 cursor-pointer rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
              <input
                type="checkbox"
                checked={emailNotifications}
                onChange={(e) => setEmailNotifications(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-sm text-slate-700">Email alerts for new mentions</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 opacity-60">
              <input
                type="checkbox"
                checked={slackNotifications}
                onChange={(e) => setSlackNotifications(e.target.checked)}
                disabled
                className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-sm text-slate-700">Slack alerts (coming soon)</span>
            </label>
          </div>
        </div>
      );
    }

    return (
      <Card className="border-slate-200 shadow-none">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <div>
              <p className="text-slate-500">Keyword</p>
              <p className="font-medium text-slate-900">{keyword}</p>
            </div>
            <div>
              <p className="text-slate-500">Platform</p>
              <p className="font-medium text-slate-900">{PlatformLabels[activePlatform]}</p>
            </div>
            <div className="col-span-2">
              {showSourceFilters && (
                <>
                  <p className="text-slate-500">{PlatformFilterLabels[activePlatform]}</p>
                  <ChipList items={platformFilters} />
                </>
              )}
            </div>
            <div className="col-span-2">
              <p className="text-slate-500">Excluded keywords</p>
              <ChipList items={excludedKeywords} />
            </div>
            {isReddit && (
              <div className="col-span-2">
                <p className="text-slate-500">Excluded subreddits</p>
                <ChipList items={excludedSubreddits} />
              </div>
            )}
            <div>
              <p className="text-slate-500">Included users</p>
              <ChipList items={includedUsers} />
            </div>
            <div>
              <p className="text-slate-500">Excluded users</p>
              <ChipList items={excludedUsers} />
            </div>
            <div className="col-span-2">
              <p className="text-slate-500">Included languages</p>
              <p className="text-slate-700">{formatLanguageList(includedLanguages) || "All"}</p>
            </div>
            <div className="col-span-2">
              <p className="text-slate-500">Excluded languages</p>
              <p className="text-slate-700">{formatLanguageList(excludedLanguages)}</p>
            </div>
            <div>
              <p className="text-slate-500">Case sensitive</p>
              <Badge variant={caseSensitive ? "default" : "secondary"}>
                {caseSensitive ? "Yes" : "No"}
              </Badge>
            </div>
            <div>
              <p className="text-slate-500">Matching</p>
              <Badge variant="outline">
                {wholeWordsOnly ? "Whole words only" : "Contains"}
              </Badge>
            </div>
            <div className="col-span-2">
              <p className="text-slate-500 mb-1">Content types</p>
              <div className="flex flex-wrap gap-1">
                {contentTypes.map((type) => (
                  <Badge key={type} variant="outline" className="text-xs">
                    {ContentTypeLabels[type]}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-slate-500">Email alerts</p>
              <Badge variant={emailNotifications ? "default" : "secondary"}>
                {emailNotifications ? "On" : "Off"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="!flex !flex-col gap-0 p-0 top-[5vh] translate-y-0 sm:max-w-xl w-[calc(100%-2rem)] max-h-[90dvh] overflow-hidden bg-white shadow-xl border border-slate-200">
        {/* Fixed header */}
        <DialogHeader className="shrink-0 px-5 pt-5 pb-3 border-b border-slate-200 pr-12">
          <DialogTitle className="text-lg font-semibold text-slate-900">
            {editKeyword ? "Edit Keyword" : "Add New Keyword"}
          </DialogTitle>
          <p className="text-sm text-slate-500">
            {editKeyword
              ? `Update settings for "${editKeyword.keyword}"`
              : `Monitor on ${PlatformLabels[activePlatform]}`}
          </p>
        </DialogHeader>

        {/* Compact stepper */}
        <div className="shrink-0 px-5 py-3 border-b border-slate-100 bg-slate-50/80">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className="flex flex-col items-center min-w-0">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold border-2 ${
                      currentStep >= step.id
                        ? "bg-indigo-600 border-indigo-600 text-white"
                        : "bg-white border-slate-300 text-slate-400"
                    }`}
                  >
                    {currentStep > step.id ? "✓" : step.id}
                  </div>
                  <span className="text-[10px] mt-1 font-medium text-slate-500 truncate max-w-[4.5rem] text-center">
                    {step.label}
                  </span>
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-1 mb-4 ${
                      currentStep > step.id ? "bg-indigo-600" : "bg-slate-200"
                    }`}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Scrollable body + fixed footer */}
        <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
          <div className="flex-1 overflow-y-auto px-5 py-4 min-h-0">
            {error && (
              <div className="text-sm text-red-700 bg-red-50 p-3 rounded-lg border border-red-200 mb-4">
                {error}
              </div>
            )}
            {renderStepContent()}
          </div>

          <div className="shrink-0 flex justify-between gap-3 px-5 py-4 border-t border-slate-200 bg-white">
            <Button
              type="button"
              variant="outline"
              onClick={currentStep === 1 ? handleClose : prevStep}
              className="h-10 border border-slate-300 text-slate-700 bg-white hover:bg-slate-50"
              disabled={isLoading}
            >
              {currentStep === 1 ? "Cancel" : "Back"}
            </Button>
            {currentStep < 4 ? (
              <Button
                type="button"
                onClick={nextStep}
                disabled={isNextDisabled()}
                className="h-10 bg-indigo-600 text-white hover:bg-indigo-700 border border-indigo-600"
              >
                Next
              </Button>
            ) : (
              <Button
                type="submit"
                disabled={isLoading}
                className="h-10 bg-indigo-600 text-white hover:bg-indigo-700 border border-indigo-600"
              >
                {isLoading ? (editKeyword ? "Updating..." : "Adding...") : (editKeyword ? "Update" : "Add Keyword")}
              </Button>
            )}
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
