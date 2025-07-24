from django.core.management.base import BaseCommand
from tracker.models import Keyword
from tracker.enums import (
    MatchModeChoices, ContentTypeChoices, DEFAULT_CONTENT_TYPES, 
    PlatformChoices
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate existing keywords to include enhanced matching fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get all existing keywords
        keywords = Keyword.objects.all()
        total_keywords = keywords.count()
        
        self.stdout.write(f"Found {total_keywords} keywords to migrate")
        
        migrated_count = 0
        skipped_count = 0
        
        for keyword in keywords:
            try:
                # Check if keyword already has the new fields
                if hasattr(keyword, 'case_sensitive') and hasattr(keyword, 'match_mode') and hasattr(keyword, 'content_types'):
                    # Check if fields have default values (need migration)
                    needs_migration = (
                        keyword.case_sensitive is None or
                        keyword.match_mode is None or
                        keyword.content_types is None or
                        len(keyword.content_types) == 0
                    )
                    
                    if not needs_migration:
                        skipped_count += 1
                        continue
                
                # Set default values for new fields
                if not hasattr(keyword, 'case_sensitive') or keyword.case_sensitive is None:
                    keyword.case_sensitive = False
                
                if not hasattr(keyword, 'match_mode') or keyword.match_mode is None:
                    keyword.match_mode = MatchModeChoices.CONTAINS[0]
                
                if not hasattr(keyword, 'content_types') or keyword.content_types is None or len(keyword.content_types) == 0:
                    # Get default content types for the platform
                    default_types = DEFAULT_CONTENT_TYPES.get(keyword.platform, [ContentTypeChoices.TITLES[0], ContentTypeChoices.COMMENTS[0]])
                    keyword.content_types = [choice[0] for choice in default_types]
                
                if not dry_run:
                    keyword.save()
                
                migrated_count += 1
                self.stdout.write(f"✓ Migrated keyword: {keyword.keyword} ({keyword.platform})")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error migrating keyword {keyword.keyword}: {str(e)}")
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("MIGRATION SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Total keywords: {total_keywords}")
        self.stdout.write(f"Migrated: {migrated_count}")
        self.stdout.write(f"Skipped (already migrated): {skipped_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nThis was a dry run. Run without --dry-run to apply changes."))
        else:
            self.stdout.write(self.style.SUCCESS("\nMigration completed successfully!")) 