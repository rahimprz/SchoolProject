# Run this script to check if your URLs are correctly registered
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.urls import get_resolver

def list_urls():
    """List all registered URL patterns in the project"""
    resolver = get_resolver()
    
    print("=== REGISTERED URL PATTERNS ===")
    for url_pattern in resolver.url_patterns:
        if hasattr(url_pattern, 'url_patterns'):
            # This is an include() pattern
            for included_pattern in url_pattern.url_patterns:
                print(f"  - {included_pattern.pattern} -> {included_pattern.callback.__name__ if hasattr(included_pattern, 'callback') else 'include'}")
        else:
            # This is a direct pattern
            print(f"- {url_pattern.pattern} -> {url_pattern.callback.__name__ if hasattr(url_pattern, 'callback') else 'unknown'}")
    
    # Specifically check for award_points and deduct_points
    award_points_found = False
    deduct_points_found = False
    
    for url_pattern in resolver.url_patterns:
        if hasattr(url_pattern, 'url_patterns'):
            for included_pattern in url_pattern.url_patterns:
                if hasattr(included_pattern, 'callback'):
                    if included_pattern.callback.__name__ == 'award_points':
                        award_points_found = True
                        print(f"\nFound award_points at: {included_pattern.pattern}")
                    elif included_pattern.callback.__name__ == 'deduct_points':
                        deduct_points_found = True
                        print(f"Found deduct_points at: {included_pattern.pattern}")
    
    if not award_points_found:
        print("\nWARNING: award_points URL not found!")
    if not deduct_points_found:
        print("WARNING: deduct_points URL not found!")

if __name__ == "__main__":
    list_urls()
