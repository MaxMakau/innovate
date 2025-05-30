import collections
from courses.models import Module, Lesson # IMPORTANT: Replace 'your_app_name'

print("--- Starting Lesson Order Duplicates Fix Script ---")

# Get all modules
modules = Module.objects.all()

fixed_modules_count = 0
total_duplicates_found = 0

for module in modules:
    print(f"\nChecking Module: '{module.title}' (ID: {module.id}) in Course: '{module.course.title}'")
    
    # Get all lessons for the current module, ordered by their current 'order'
    lessons_in_module = list(Lesson.objects.filter(module=module).order_by('order'))
    
    # Use a Counter to find duplicate order values
    order_counts = collections.Counter(lesson.order for lesson in lessons_in_module)
    
    duplicates = {order: count for order, count in order_counts.items() if count > 1}

    if duplicates:
        print(f"  !!! Found DUPLICATE order values in this module: {duplicates}")
        total_duplicates_found += sum(count - 1 for count in duplicates.values()) # Count actual duplicates

        # Re-order lessons sequentially to ensure uniqueness
        print("  Attempting to re-assign unique order values for lessons in this module...")
        
        # Sort lessons by their current order, then by ID to ensure a consistent re-ordering
        lessons_in_module.sort(key=lambda l: (l.order, l.id))
        
        reordered_count = 0
        for i, lesson in enumerate(lessons_in_module):
            new_order = i + 1 # Assign new sequential order starting from 1
            if lesson.order != new_order:
                lesson.order = new_order
                lesson.save(update_fields=['order'])
                reordered_count += 1
                print(f"    - Lesson '{lesson.title}' (ID: {lesson.id}) order changed to {new_order}")
        
        if reordered_count > 0:
            print(f"  Successfully re-ordered {reordered_count} lessons in module '{module.title}'.")
            fixed_modules_count += 1
        else:
            print("  No lessons needed re-ordering despite duplicates (might be a logical issue or already fixed).")
    else:
        print("  No duplicate order values found in this module. All good.")

print(f"\n--- Script Finished ---")
print(f"Total modules with fixed duplicates: {fixed_modules_count}")
print(f"Total duplicate entries found and corrected: {total_duplicates_found}")

if total_duplicates_found > 0:
    print("\nIMPORTANT: Duplicate order values were found and corrected.")
    print("Please run 'python manage.py makemigrations' and then 'python manage.py migrate' again.")
else:
    print("\nNo duplicate lesson orders were found. If you are still facing migration issues,")
    print("the constraint might be on a different model or there's another issue.")

