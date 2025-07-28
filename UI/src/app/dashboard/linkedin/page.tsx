"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import KeywordModal from "@/components/KeywordModal";
import KeywordList from "@/components/KeywordList";
import { Keyword } from "@/lib/api";
import { Platform, ContentType } from "@/lib/enums";

// Define Mention type for now
interface Mention {
  id: string;
  keyword_id: string;
  user_id: string;
  content: string;
  title: string;
  author: string;
  source_url: string;
  platform: string;
  subreddit: string;
  content_type: string;
  matched_text: string;
  match_position: number;
  match_confidence: number;
  mention_date: string;
  discovered_at: string;
  platform_item_id?: string;
  platform_score?: number;
  platform_comments_count?: number;
}

export default function LinkedInDashboard() {
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [mentions, setMentions] = useState<Mention[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchLinkedInData();
  }, []);

  const fetchLinkedInData = async () => {
    try {
      setIsLoading(true);
      
      // Fetch LinkedIn keywords
      const keywordsResponse = await fetch('/api/keywords', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform: Platform.LINKEDIN })
      });
      
      if (keywordsResponse.ok) {
        const keywordsData = await keywordsResponse.json();
        setKeywords(keywordsData.keywords || []);
      }

      // Fetch LinkedIn mentions
      const mentionsResponse = await fetch('/api/mentions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform: Platform.LINKEDIN })
      });
      
      if (mentionsResponse.ok) {
        const mentionsData = await mentionsResponse.json();
        setMentions(mentionsData.mentions || []);
      }
    } catch (error) {
      console.error('Error fetching LinkedIn data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeywordAdded = () => {
    fetchLinkedInData();
    setIsModalOpen(false);
  };

  const handleKeywordDeleted = () => {
    fetchLinkedInData();
  };

  const getContentTypeLabel = (contentType: string) => {
    switch (contentType) {
      case ContentType.BODY:
        return 'Post Content';
      case ContentType.COMMENTS:
        return 'Comments';
      case ContentType.TITLES:
        return 'Post Title';
      default:
        return contentType;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">LinkedIn Monitoring</h1>
            <p className="text-muted-foreground">
              Monitor LinkedIn mentions and track your keywords
            </p>
          </div>
          <Button disabled>Loading...</Button>
        </div>
        <div className="grid gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Loading...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">LinkedIn Monitoring</h1>
          <p className="text-muted-foreground">
            Monitor LinkedIn mentions and track your keywords
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          Add LinkedIn Keyword
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Keywords</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{keywords.length}</div>
            <p className="text-xs text-muted-foreground">
              Active LinkedIn keywords
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Mentions</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mentions.length}</div>
            <p className="text-xs text-muted-foreground">
              LinkedIn mentions found
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today&apos;s Mentions</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mentions.filter(m => {
                const today = new Date();
                const mentionDate = new Date(m.mention_date);
                return mentionDate.toDateString() === today.toDateString();
              }).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Mentions from today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </CardHeader>
          <CardContent>
            <Badge className="bg-yellow-100 text-yellow-800">
              Coming Soon
            </Badge>
            <p className="text-xs text-muted-foreground mt-1">
              Platform in development
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>LinkedIn Keywords</CardTitle>
            <CardDescription>
              Manage your LinkedIn monitoring keywords
            </CardDescription>
          </CardHeader>
          <CardContent>
            <KeywordList
              platform={Platform.LINKEDIN}
              onRefresh={handleKeywordDeleted}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Mentions</CardTitle>
            <CardDescription>
              Latest LinkedIn mentions of your keywords
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mentions.slice(0, 5).map((mention) => (
                <div key={mention.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline">
                          {getContentTypeLabel(mention.content_type)}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {mention.author}
                        </span>
                      </div>
                      <p className="text-sm mb-2 line-clamp-2">
                        {mention.content}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{new Date(mention.mention_date).toLocaleDateString()}</span>
                        <span>•</span>
                        <span>Score: {mention.platform_score || 0}</span>
                        <span>•</span>
                        <span>Comments: {mention.platform_comments_count || 0}</span>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" asChild>
                      <a href={mention.source_url} target="_blank" rel="noopener noreferrer">
                        View
                      </a>
                    </Button>
                  </div>
                </div>
              ))}
              {mentions.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <svg className="w-12 h-12 mx-auto mb-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <p>No LinkedIn mentions found yet</p>
                  <p className="text-sm">Add keywords to start monitoring</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <KeywordModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onKeywordSaved={handleKeywordAdded}
        platform={Platform.LINKEDIN}
      />
    </div>
  );
} 