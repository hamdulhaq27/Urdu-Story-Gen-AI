"""
CSV Merger Script for Story Collections
Merges Rekhta stories (250) with UrduPoint stories (250) into a single CSV
"""

import csv
import json
from pathlib import Path


def merge_story_csvs(csv1_path, csv2_path, output_path):
    """
    Merge two story CSV files into one.
    
    Args:
        csv1_path: Path to first CSV (UrduPoint stories)
        csv2_path: Path to second CSV (Rekhta stories)
        output_path: Path for merged output CSV
    """
    
    print("="*60)
    print("STORY CSV MERGER")
    print("="*60)
    
    # Read first CSV
    print(f"\n1. Reading first CSV: {csv1_path}")
    stories = []
    
    try:
        with open(csv1_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stories.append(row)
        print(f"   ✓ Loaded {len(stories)} stories from first CSV")
    except FileNotFoundError:
        print(f"   ✗ File not found: {csv1_path}")
        return False
    except Exception as e:
        print(f"   ✗ Error reading first CSV: {e}")
        return False
    
    # Read second CSV
    print(f"\n2. Reading second CSV: {csv2_path}")
    new_stories = []
    
    try:
        with open(csv2_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                new_stories.append(row)
        print(f"   ✓ Loaded {len(new_stories)} stories from second CSV")
    except FileNotFoundError:
        print(f"   ✗ File not found: {csv2_path}")
        return False
    except Exception as e:
        print(f"   ✗ Error reading second CSV: {e}")
        return False
    
    # Renumber story IDs for second set
    print(f"\n3. Renumbering story IDs for second set...")
    starting_id = len(stories) + 1
    
    for i, story in enumerate(new_stories):
        old_id = story.get('story_id', '')
        new_id = f"STORY_{starting_id + i:04d}"
        story['story_id'] = new_id
        
        if i < 5:  # Show first 5 for debugging
            print(f"   {old_id} → {new_id}")
    
    if len(new_stories) > 5:
        print(f"   ... and {len(new_stories) - 5} more")
    
    # Merge
    print(f"\n4. Merging stories...")
    all_stories = stories + new_stories
    print(f"   ✓ Total stories: {len(all_stories)}")
    
    # Save merged CSV
    print(f"\n5. Saving merged CSV: {output_path}")
    
    try:
        # Get fieldnames from first story
        fieldnames = list(all_stories[0].keys())
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for story in all_stories:
                writer.writerow(story)
        
        print(f"   ✓ Saved successfully!")
        
        # Also save JSON backup
        json_path = Path(output_path).with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_stories, f, ensure_ascii=False, indent=2)
        print(f"   ✓ JSON backup saved: {json_path}")
        
    except Exception as e:
        print(f"   ✗ Error saving merged CSV: {e}")
        return False
    
    # Print statistics
    print("\n" + "="*60)
    print("MERGE COMPLETE")
    print("="*60)
    print(f"First CSV:  {len(stories)} stories")
    print(f"Second CSV: {len(new_stories)} stories")
    print(f"Total:      {len(all_stories)} stories")
    print("="*60)
    
    return True


def main():
    """Main function - Edit the paths below to match your files"""
    
    # ===== EDIT THESE PATHS =====
    csv1 = "raw_stories/urdupoint_stories.csv"           # First CSV (UrduPoint)
    csv2 = "rekhta_stories/rekhta_stories.csv"           # Second CSV (Rekhta)
    output = "merged_stories/all_stories.csv"            # Output path
    # ============================
    
    # Create output directory
    output_dir = Path(output).parent
    output_dir.mkdir(exist_ok=True)
    
    print("\nFile paths:")
    print(f"  First CSV:  {csv1}")
    print(f"  Second CSV: {csv2}")
    print(f"  Output CSV: {output}")
    print()
    
    # Merge
    success = merge_story_csvs(csv1, csv2, output)
    
    if success:
        print(f"\n✓ Success! Merged file saved to: {output}")
    else:
        print("\n✗ Merge failed. Check the error messages above.")


if __name__ == "__main__":
    main()