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
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useApi, KeywordRequest, Keyword } from "@/lib/api";
import { 
  Platform, PlatformLabels, PlatformFilterLabels, PlatformPlaceholders, PlatformDescriptions,
  MatchMode, ContentType, ContentTypeLabels
} from "@/lib/enums";
import { Badge } from "@/components/ui/badge";

type KeywordModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onKeywordSaved: () => void;
  platform?: string;
  keyword?: Keyword; // For editing mode (undefined for add mode)
};

type WizardStep = 1 | 2 | 3;

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
  const [platformFilters, setPlatformFilters] = useState(
    editKeyword?.platformSpecificFilters?.join(", ") || ""
  );
  
  // Advanced matching options
  const [caseSensitive, setCaseSensitive] = useState(editKeyword?.caseSensitive || false);
  const [matchMode, setMatchMode] = useState<MatchMode>(editKeyword?.matchMode || MatchMode.CONTAINS);
  const [contentTypes, setContentTypes] = useState<ContentType[]>(
    editKeyword?.contentTypes || [ContentType.TITLES, ContentType.BODY, ContentType.COMMENTS]
  );
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Reset form when editKeyword changes
  React.useEffect(() => {
    if (editKeyword) {
      setKeyword(editKeyword.keyword);
      setPlatformFilters(editKeyword.platformSpecificFilters?.join(", ") || "");
      setCaseSensitive(editKeyword.caseSensitive || false);
      setMatchMode(editKeyword.matchMode || MatchMode.CONTAINS);
      setContentTypes(editKeyword.contentTypes || [ContentType.TITLES, ContentType.BODY, ContentType.COMMENTS]);
    } else {
      setKeyword("");
      setPlatformFilters("");
      setCaseSensitive(false);
      setMatchMode(MatchMode.CONTAINS);
      setContentTypes([ContentType.TITLES, ContentType.BODY, ContentType.COMMENTS]);
    }
    setCurrentStep(1);
    setError(null);
  }, [editKeyword]);

  // Reset wizard step when modal opens/closes
  React.useEffect(() => {
    if (isOpen) {
      setCurrentStep(1);
      setError(null);
    }
  }, [isOpen]);

  const getPlatformLabel = () => {
    if (!platform) return "Filters";
    return PlatformFilterLabels[platform as Platform] || "Filters";
  };

  const getPlatformPlaceholder = () => {
    if (!platform) return "filter1, filter2, filter3 (comma separated)";
    return PlatformPlaceholders[platform as Platform] || "filter1, filter2, filter3 (comma separated)";
  };

  const getPlatformDescription = () => {
    if (!platform) return "Leave empty to monitor all sources";
    return PlatformDescriptions[platform as Platform] || "Leave empty to monitor all sources";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const filterList = platformFilters
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const request: KeywordRequest = {
        keyword: keyword.trim(),
        platform: (platform as Platform) || Platform.BOTH,
        platformSpecificFilters: filterList.length > 0 ? filterList : undefined,
        caseSensitive: caseSensitive,
        matchMode: matchMode,
        contentTypes: contentTypes,
        emailNotifications: true,
        slackNotifications: false,
      };

      if (editKeyword) {
        // Update existing keyword
        await api.updateKeyword(editKeyword.id, request);
      } else {
        // Create new keyword
        await api.createKeyword(request);
      }

      setKeyword("");
      setPlatformFilters("");
      onClose();
      onKeywordSaved?.();
    } catch (err) {
      console.error(editKeyword ? "Error updating keyword:" : "Error creating keyword:", err);
      setError(editKeyword ? "Failed to update keyword. Please try again." : "Failed to create keyword. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setKeyword("");
    setPlatformFilters("");
    setCaseSensitive(false);
    setMatchMode(MatchMode.CONTAINS);
    setContentTypes([ContentType.TITLES, ContentType.BODY, ContentType.COMMENTS]);
    setError(null);
    onClose();
  };

  // Wizard navigation logic
  const nextStep = () => {
    if (currentStep < 3) setCurrentStep((prev) => (prev + 1) as WizardStep);
  };
  const prevStep = () => {
    if (currentStep > 1) setCurrentStep((prev) => (prev - 1) as WizardStep);
  };

  // Check if next step should be disabled
  const isNextDisabled = () => {
    if (currentStep === 1) {
      return !keyword.trim(); // Disable if keyword is empty or only whitespace
    }
    return false; // Allow navigation for other steps
  };



  const renderNavigation = () => (
    <div className="flex justify-between pt-6">
      <Button
        type="button"
        variant="outline"
        onClick={currentStep === 1 ? handleClose : prevStep}
        className="h-12 text-base font-medium"
        disabled={isLoading}
      >
        {currentStep === 1 ? "Cancel" : "Back"}
      </Button>
      <div className="flex space-x-3">
        {currentStep < 3 && (
          <Button
            type="button"
            onClick={nextStep}
            disabled={isNextDisabled()}
            className="h-12 text-base font-medium"
          >
            Next
          </Button>
        )}
        {currentStep === 3 && (
          <Button
            type="submit"
            disabled={isLoading}
            className="h-12 text-base font-medium"
          >
            {isLoading ? (editKeyword ? "Updating..." : "Adding...") : (editKeyword ? "Update Keyword" : "Add Keyword")}
          </Button>
        )}
      </div>
    </div>
  );

  // Step-specific content
  const renderStepContent = () => {
    if (currentStep === 1) {
      return (
        <div className="space-y-6 bg-slate-50 p-6 rounded-xl border border-slate-200">
          <div className="space-y-3">
            <Label htmlFor="keyword" className="text-lg font-semibold text-slate-900">Keyword *</Label>
            <Input
              id="keyword"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Enter keyword to monitor (e.g., 'your brand name')"
              required
              disabled={isLoading}
              className={`text-lg h-14 bg-white border-2 font-medium ${
                currentStep === 1 && !keyword.trim() 
                  ? 'border-red-400 focus:border-red-500 focus:ring-red-200' 
                  : 'border-slate-300 focus:border-indigo-500 focus:ring-indigo-200'
              }`}
            />
            {currentStep === 1 && !keyword.trim() && (
              <p className="text-sm text-red-600 font-medium">
                ⚠️ Keyword is required to continue
              </p>
            )}
          </div>
          <div className="space-y-3">
            <Label htmlFor="platformFilters" className="text-base font-medium">
              {getPlatformLabel()} (Optional)
            </Label>
            <Input
              id="platformFilters"
              value={platformFilters}
              onChange={(e) => setPlatformFilters(e.target.value)}
              placeholder={getPlatformPlaceholder()}
              disabled={isLoading}
              className="text-base h-12"
            />
            <p className="text-sm text-muted-foreground leading-relaxed">
              {getPlatformDescription()}
            </p>
          </div>
        </div>
      );
    }
    if (currentStep === 2) {
      return (
        <div className="space-y-6">
          {/* Case Sensitivity */}
          <div className="space-y-3">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={caseSensitive}
                onChange={e => setCaseSensitive(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span className="text-base font-medium">Case Sensitive</span>
            </label>
            <p className="text-sm text-muted-foreground ml-7">
              When enabled, &quot;Python&quot; will only match &quot;Python&quot;, not &quot;python&quot; or &quot;PYTHON&quot;
            </p>
          </div>
          {/* Match Mode */}
          <div className="space-y-3">
            <label htmlFor="matchMode" className="text-base font-medium block">Match Mode</label>
            <select
              id="matchMode"
              className="w-full border rounded-lg px-4 py-3 text-base focus:ring-2 focus:ring-primary focus:border-primary"
              value={matchMode}
              onChange={e => setMatchMode(e.target.value as MatchMode)}
            >
              {Object.values(MatchMode).map(mode => (
                <option key={mode} value={mode}>
                  {mode.charAt(0).toUpperCase() + mode.slice(1).replace(/_/g, ' ')}
                </option>
              ))}
            </select>
            <p className="text-sm text-muted-foreground">
              How the keyword should be matched in content
            </p>
          </div>
          {/* Content Types */}
          <div className="space-y-3">
            <label className="text-base font-medium block">Content Types to Monitor</label>
            <div className="space-y-3">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={contentTypes.includes(ContentType.TITLES)}
                  onChange={e => {
                    if (e.target.checked) {
                      setContentTypes([...contentTypes, ContentType.TITLES]);
                    } else {
                      setContentTypes(contentTypes.filter(ct => ct !== ContentType.TITLES));
                    }
                  }}
                  className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <span className="text-base">{ContentTypeLabels[ContentType.TITLES]}</span>
              </label>
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={contentTypes.includes(ContentType.BODY)}
                  onChange={e => {
                    if (e.target.checked) {
                      setContentTypes([...contentTypes, ContentType.BODY]);
                    } else {
                      setContentTypes(contentTypes.filter(ct => ct !== ContentType.BODY));
                    }
                  }}
                  className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <span className="text-base">{ContentTypeLabels[ContentType.BODY]}</span>
              </label>
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={contentTypes.includes(ContentType.COMMENTS)}
                  onChange={e => {
                    if (e.target.checked) {
                      setContentTypes([...contentTypes, ContentType.COMMENTS]);
                    } else {
                      setContentTypes(contentTypes.filter(ct => ct !== ContentType.COMMENTS));
                    }
                  }}
                  className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <span className="text-base">{ContentTypeLabels[ContentType.COMMENTS]}</span>
              </label>
            </div>
            <p className="text-sm text-muted-foreground">
              Select which types of content to monitor for this keyword
            </p>
          </div>
        </div>
      );
    }
    if (currentStep === 3) {
      return (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Keyword Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Keyword</label>
                  <p className="text-base font-medium">{keyword}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Platform</label>
                  <p className="text-base font-medium">
                    {platform ? PlatformLabels[platform as Platform] : "All Platforms"}
                  </p>
                </div>
                {platformFilters && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Filters</label>
                    <p className="text-base">{platformFilters}</p>
                  </div>
                )}
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Advanced Settings</label>
                  <div className="space-y-2 mt-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">Case Sensitive:</span>
                      <Badge variant={caseSensitive ? "default" : "secondary"}>
                        {caseSensitive ? "Yes" : "No"}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">Match Mode:</span>
                      <Badge variant="outline">
                        {matchMode.charAt(0).toUpperCase() + matchMode.slice(1).replace(/_/g, ' ')}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm">Content Types:</span>
                      <div className="flex space-x-1">
                        {contentTypes.map(type => (
                          <Badge key={type} variant="outline" className="text-xs">
                            {ContentTypeLabels[type]}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }
    return null;
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-2xl bg-white shadow-xl border border-slate-200">
        {/* Simple, Clean Header */}
        <DialogHeader className="border-b border-slate-200 pb-4 mb-6">
          <DialogTitle className="text-2xl font-semibold text-slate-900">
            {editKeyword ? "Edit Keyword" : "Add New Keyword"}
          </DialogTitle>
          <p className="text-slate-600 mt-1">
            {editKeyword 
              ? `Update monitoring settings for "${editKeyword.keyword}"`
              : `Set up keyword monitoring for ${platform ? PlatformLabels[platform as Platform] || platform.charAt(0).toUpperCase() + platform.slice(1) : "your platform"}`
            }
          </p>
        </DialogHeader>

        {/* Step Indicator - More Visible */}
        <div className="mb-8">
          <div className="flex items-center justify-between max-w-md mx-auto">
            {[1, 2, 3].map((step, index) => (
              <React.Fragment key={step}>
                <div className="flex flex-col items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold border-2 transition-all ${
                      currentStep >= step
                        ? "bg-indigo-600 border-indigo-600 text-white"
                        : "bg-white border-slate-300 text-slate-400"
                    }`}
                  >
                    {currentStep > step ? (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      step
                    )}
                  </div>
                  <div className="text-xs mt-2 font-medium text-slate-600">
                    {step === 1 ? "Basic Info" : step === 2 ? "Settings" : "Review"}
                  </div>
                </div>
                {index < 2 && (
                  <div className={`flex-1 h-0.5 mx-3 ${
                    currentStep > step ? "bg-indigo-600" : "bg-slate-200"
                  }`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
        
        {/* Form Content */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="text-sm text-red-700 bg-red-50 p-4 rounded-lg border border-red-200">
              {error}
            </div>
          )}

          {renderStepContent()}
          {renderNavigation()}
        </form>
      </DialogContent>
    </Dialog>
  );
}
