from datetime import datetime, timedelta

def calculate_next_revision(last_reviewed, level):
    """
    Spaced repetition logic using a simplified Leitner system or similar.
    Intervals: 1 day, 3 days, 7 days, 14 days, 30 days.
    """
    intervals = [1, 3, 7, 14, 30]
    if level < len(intervals):
        days = intervals[level]
    else:
        days = intervals[-1]
    
    return last_reviewed + timedelta(days=days)

def get_revision_schedule(notes):
    """
    Filters notes that are due for revision today.
    """
    today = datetime.utcnow().date()
    due_notes = []
    
    for note in notes:
        # Assuming note object has 'last_reviewed' and 'level'
        next_date = calculate_next_revision(note.last_reviewed, note.level).date()
        if next_date <= today:
            due_notes.append(note)
            
    return due_notes
