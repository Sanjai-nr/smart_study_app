import random

def generate_quiz(text):
    """
    Generates a simple quiz based on the provided text.
    In a production app, you might use an LLM (OpenAI/Gemini) to generate better questions.
    """
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    
    if not sentences:
        return [{"question": "Not enough content to generate a quiz.", "options": ["OK", "Try again", "More text", "Finish"], "answer": "OK"}]
    
    quiz = []
    # Pick up to 5 random sentences to turn into questions
    sample_count = min(len(sentences), 5)
    selected_sentences = random.sample(sentences, sample_count)
    
    for sentence in selected_sentences:
        words = sentence.split()
        # Find a suitable keyword to "hide" (nouns/verbs usually)
        # For simplicity, we'll just pick a word longer than 5 chars
        potential_keywords = [w.strip(',()') for w in words if len(w) > 5]
        
        if potential_keywords:
            keyword = random.choice(potential_keywords)
            question = sentence.replace(keyword, "__________")
            
            # Create dummy options
            options = [keyword]
            other_words = list(set([w.strip(',()') for w in text.split() if len(w) > 5 and w != keyword]))
            if len(other_words) >= 3:
                options.extend(random.sample(other_words, 3))
            else:
                options.extend(["Option A", "Option B", "Option C"])
            
            random.shuffle(options)
            quiz.append({
                "question": question,
                "options": options,
                "answer": keyword
            })
            
    return quiz
