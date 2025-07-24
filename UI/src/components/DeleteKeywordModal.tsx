"use client";

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Keyword } from "@/lib/api";

type DeleteKeywordModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  keyword?: Keyword;
  isLoading?: boolean;
};

export default function DeleteKeywordModal({
  isOpen,
  onClose,
  onConfirm,
  keyword,
  isLoading = false,
}: DeleteKeywordModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Keyword</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete the keyword{" "}
            <span className="font-semibold text-foreground">
              &ldquo;{keyword?.keyword}&rdquo;
            </span>
            ? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="flex gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 sm:flex-none"
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 sm:flex-none"
          >
            {isLoading ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 