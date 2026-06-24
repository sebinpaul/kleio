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
      <DialogContent className="sm:max-w-md bg-white shadow-xl border border-slate-200">
        <DialogHeader>
          <DialogTitle className="text-slate-900">Delete Keyword</DialogTitle>
          <DialogDescription className="text-slate-600">
            Are you sure you want to delete the keyword{" "}
            <span className="font-semibold text-slate-900">
              &ldquo;{keyword?.keyword}&rdquo;
            </span>
            ? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="flex gap-3 sm:justify-end">
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