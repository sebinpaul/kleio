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
import { useApi, KeywordRequest } from "@/lib/api";

type AddKeywordModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onKeywordAdded: () => void;
  platform?: string;
};

export default function AddKeywordModal({
  isOpen,
  onClose,
  onKeywordAdded,
  platform,
}: AddKeywordModalProps) {
  const api = useApi();
  const [keyword, setKeyword] = useState("");
  const [platformFilters, setPlatformFilters] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getPlatformLabel = () => {
    switch (platform) {
      case "reddit":
        return "Subreddits";
      case "hackernews":
        return "Categories";
      case "twitter":
        return "Hashtags";
      case "linkedin":
        return "Companies";
      default:
        return "Filters";
    }
  };

  const getPlatformPlaceholder = () => {
    switch (platform) {
      case "reddit":
        return "technology, programming, java (comma separated)";
      case "hackernews":
        return "tech, startup, ai (comma separated)";
      case "twitter":
        return "#tech, #programming, #ai (comma separated)";
      case "linkedin":
        return "Google, Microsoft, Apple (comma separated)";
      default:
        return "filter1, filter2, filter3 (comma separated)";
    }
  };

  const getPlatformDescription = () => {
    switch (platform) {
      case "reddit":
        return "Leave empty to monitor all public subreddits";
      case "hackernews":
        return "Leave empty to monitor all stories";
      case "twitter":
        return "Leave empty to monitor all tweets";
      case "linkedin":
        return "Leave empty to monitor all posts";
      default:
        return "Leave empty to monitor all sources";
    }
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
        platform: platform || "general",
        platformSpecificFilters: filterList.length > 0 ? filterList : undefined,
        emailNotifications: true,
        slackNotifications: false,
      };

      await api.createKeyword(request);

      setKeyword("");
      setPlatformFilters("");
      onClose();
      onKeywordAdded?.();
    } catch (err) {
      console.error("Error creating keyword:", err);
      setError("Failed to create keyword. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setKeyword("");
    setPlatformFilters("");
    setError(null);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            Add New{" "}
            {platform
              ? platform.charAt(0).toUpperCase() + platform.slice(1)
              : ""}{" "}
            Keyword
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="text-sm text-destructive bg-destructive/10 p-3 rounded">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="keyword">Keyword *</Label>
            <Input
              id="keyword"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Enter keyword to monitor"
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="platformFilters">
              {getPlatformLabel()} (Optional)
            </Label>
            <Input
              id="platformFilters"
              value={platformFilters}
              onChange={(e) => setPlatformFilters(e.target.value)}
              placeholder={getPlatformPlaceholder()}
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              {getPlatformDescription()}
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              className="flex-1"
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isLoading || !keyword.trim()}
              className="flex-1"
            >
              {isLoading ? "Adding..." : "Add Keyword"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
