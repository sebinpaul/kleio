"use client";

import { ReactNode } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import KeywordList from "./KeywordList";
import AddKeywordModal from "./AddKeywordModal";

interface PlatformStats {
  title: string;
  value: string | number;
  description: string;
}

interface PlatformDashboardProps {
  platform: {
    id: string;
    name: string;
    icon: ReactNode;
    description: string;
    color: string;
  };
  stats: PlatformStats[];
  isAddModalOpen: boolean;
  onAddModalOpen: () => void;
  onAddModalClose: () => void;
  onKeywordAdded: () => void;
}

export default function PlatformDashboard({
  platform,
  stats,
  isAddModalOpen,
  onAddModalOpen,
  onAddModalClose,
  onKeywordAdded,
}: PlatformDashboardProps) {
  return (
    <div className="space-y-6">
      {/* Platform Header */}
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className={platform.color}>{platform.icon}</div>
            <h1 className="text-3xl font-bold">{platform.name}</h1>
          </div>
          <p className="text-muted-foreground">{platform.description}</p>
        </div>
        <Button onClick={onAddModalOpen}>Add {platform.name} Keyword</Button>
      </div>

      {/* Platform Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Platform Keywords */}
      <Card>
        <CardHeader>
          <CardTitle>{platform.name} Keywords</CardTitle>
          <CardDescription>
            Manage your {platform.name} keyword monitoring
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge variant="outline">{platform.name}</Badge>
              <span className="text-sm text-muted-foreground">
                Platform-specific keywords
              </span>
            </div>
            <KeywordList platform={platform.id} />
          </div>
        </CardContent>
      </Card>

      <AddKeywordModal
        isOpen={isAddModalOpen}
        onClose={onAddModalClose}
        platform={platform.id}
        onKeywordAdded={onKeywordAdded}
      />
    </div>
  );
}
