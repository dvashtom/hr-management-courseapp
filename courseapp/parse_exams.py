"""
סקריפט לחילוץ שאלות מבחן מקבצי DOCX ושמירתן כ-JSON.
מזהה תשובות נכונות לפי הדגשה (highlight) בקובץ המקור.
"""
import json
import re
import os
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.enum.text import WD_COLOR_INDEX
except ImportError:
    print("Error: python-docx not installed. Run: pip install python-docx")
    sys.exit(1)


def is_highlighted(paragraph):
    """Check if any run in the paragraph is highlighted"""
    for run in paragraph.runs:
        if run.font.highlight_color and run.font.highlight_color != WD_COLOR_INDEX.AUTO:
            return True
    return False


def is_bold_paragraph(paragraph):
    """Check if paragraph has bold text"""
    for run in paragraph.runs:
        if run.bold and run.text.strip():
            return True
    return False


def is_question_line(text):
    """Detect if a line is a question"""
    text = text.strip()
    if not text:
        return False
    # Patterns: "שאלה X", starts without א./ב./ג./ד./ה., not an option
    if text.startswith('שאלה'):
        return True
    # Lines that are questions but don't start with option letters
    if re.match(r'^(א|ב|ג|ד|ה)[\.\)]', text):
        return False
    # If it ends with question-like patterns or is long enough and not an option
    if len(text) > 30 and not re.match(r'^(א|ב|ג|ד|ה)[\.\s]', text):
        return True
    return False


def is_option_line(text):
    """Detect if a line is an answer option"""
    text = text.strip()
    if not text:
        return False
    # Match: א. / א) / א / ב. / ג. etc.
    if re.match(r'^(א|ב|ג|ד|ה)[\.\)\s]', text):
        return True
    # Also match combined answers like א+ב, א+ג+ד
    if re.match(r'^(א|ב|ג|ד|ה)\s*\+\s*(א|ב|ג|ד|ה)', text):
        return True
    # "כל התשובות" or "אף תשובה"
    if text.startswith('כל התשובות') or text.startswith('אף תשובה'):
        return True
    return False


def get_option_letter(text):
    """Extract option letter from text"""
    text = text.strip()
    m = re.match(r'^(א|ב|ג|ד|ה)[\.\)\s]', text)
    if m:
        return m.group(1)
    # Combined answers
    if re.match(r'^(א|ב|ג|ד|ה)\s*\+', text):
        return text.split('.')[0].split(')')[0].strip() if '.' in text or ')' in text else text.strip()
    return text[:1]


def extract_questions_from_docx(filepath):
    """Extract multiple choice questions from a DOCX file"""
    try:
        doc = Document(filepath)
    except Exception as e:
        print(f"  ⚠️ Error opening {filepath}: {e}")
        return []

    questions = []
    current_question = None
    current_options = []
    correct_answer = None
    
    paragraphs = doc.paragraphs
    
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        text = p.text.strip()
        highlighted = is_highlighted(p)
        
        if not text:
            i += 1
            continue
        
        # Skip meta/comment lines
        if any(skip in text for skip in ['אהלן חברים', 'נא לרשום', 'האם מישהו', 
                                          'אין הערות', 'אני עשיתי', 'גם אני',
                                          'לא רואים טוב', 'תשובה בטוחה']):
            i += 1
            continue
            
        # Check if this is a question line
        if is_question_line(text) and not is_option_line(text):
            # Save previous question if exists
            if current_question and current_options:
                questions.append({
                    'question': current_question,
                    'options': current_options,
                    'correct': correct_answer,
                    'source': Path(filepath).stem
                })
            
            # Clean question text
            q_text = text
            # Remove "שאלה X - " prefix
            q_text = re.sub(r'^שאלה\s*\d*\s*[-:–]\s*', '', q_text)
            # Remove contributor names like "יואש:" etc
            q_text = re.sub(r'^[\w]+\s*:', '', q_text).strip()
            if not q_text:
                q_text = text
            
            current_question = q_text
            current_options = []
            correct_answer = None
            
        elif is_option_line(text) and current_question:
            option_text = text
            current_options.append(option_text)
            
            if highlighted:
                correct_answer = option_text
                
        elif current_question and highlighted and not current_options:
            # This might be a highlighted answer that's also the first option
            current_options.append(text)
            correct_answer = text
            
        elif current_question and current_options and highlighted:
            # Could be an answer line not matching option pattern
            correct_answer = text
            if text not in current_options:
                current_options.append(text)
        
        i += 1
    
    # Don't forget last question
    if current_question and current_options:
        questions.append({
            'question': current_question,
            'options': current_options,
            'correct': correct_answer,
            'source': Path(filepath).stem
        })
    
    return questions


def map_question_to_topic(question_text):
    """Map a question to a course topic based on keywords"""
    text = question_text.lower() if question_text else ''
    
    topic_keywords = {
        'מבוא ומיון': ['מיון', 'גיוס', 'ראיון', 'מרכזי הערכה', 'מועמד', 'תקפות', 'מהימנות',
                       'אולריך', 'מנדט', 'משאבי אנוש', 'פסיכומטרי', 'סוציומטרי'],
        'הבדלים אינדיבידואליים': ['אישיות', 'חמשת הגדולים', 'big five', 'מוחצנות', 'נעימות',
                                   'מצפוניות', 'נוירוטיות', 'פתיחות', 'הולנד', 'קריירה'],
        'קבוצות': ['קבוצ', 'צוות', 'נורמ', 'לכידות', 'groupthink', 'חשיבה קבוצתית',
                   'תפקידים בקבוצה', 'דינמיקה'],
        'קונפליקטים': ['קונפליקט', 'סכסוך', 'התנגדות', 'מו"מ', 'משא ומתן'],
        'מוטיבציה': ['מוטיבציה', 'מאסלו', 'הרצברג', 'ציפיות', 'תגמול', 'שכר',
                     'הנעה', 'צרכים', 'מטרות'],
        'משוב': ['משוב', 'הערכ', 'דירוג', 'הערכת עובדים', 'ביצועים', '360',
                 'התפלגות מאולצת', 'feedback'],
        'שינוי ארגוני': ['שינוי', 'לוין', 'קוטר', 'התנגדות לשינוי', 'הקפאה',
                         'שינוי ארגוני', 'תרבות ארגונית', 'הדרכה'],
    }
    
    for topic, keywords in topic_keywords.items():
        for kw in keywords:
            if kw in text:
                return topic
    
    return 'כללי'


def main():
    base_dir = Path(__file__).parent.parent
    exams_dir = base_dir / 'מבחנים' / 'Archive'
    
    if not exams_dir.exists():
        print(f"❌ תיקיית מבחנים לא נמצאה: {exams_dir}")
        return
    
    print("🎓 חילוץ שאלות מבחן - ניהול משאבי אנוש")
    print(f"📁 תיקיית מבחנים: {exams_dir}")
    print("=" * 60)
    
    all_questions = []
    
    # Process files with answers (highlighted)
    answer_files = [
        '2011 סמס קיץ שרון ברקן עם תשובות.docx',
        '2014B-A מבחן 2014 מועד א סמסטר תשובות.docx',
        'פתרון.docx',
    ]
    
    # Also try all docx files
    for f in sorted(exams_dir.glob('*.docx')):
        if f.name.startswith('~'):
            continue
        print(f"  📄 מעבד: {f.name}")
        questions = extract_questions_from_docx(str(f))
        print(f"     → {len(questions)} שאלות נמצאו")
        all_questions.extend(questions)
    
    # Remove duplicates based on question text
    seen = set()
    unique_questions = []
    for q in all_questions:
        q_key = q['question'][:50]
        if q_key not in seen and q['correct']:  # Only keep questions with known answers
            seen.add(q_key)
            # Add topic mapping
            q['topic'] = map_question_to_topic(q['question'])
            unique_questions.append(q)
    
    print(f"\n{'=' * 60}")
    print(f"📊 סיכום:")
    print(f"   שאלות סה\"כ (עם תשובות): {len(unique_questions)}")
    
    # Topic distribution
    topics = {}
    for q in unique_questions:
        topics[q['topic']] = topics.get(q['topic'], 0) + 1
    print(f"   חלוקה לפי נושאים:")
    for topic, count in sorted(topics.items()):
        print(f"     {topic}: {count}")
    
    # Save to JSON
    output_path = Path(__file__).parent / 'exam_questions.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unique_questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ נשמר: {output_path}")
    print(f"   {len(unique_questions)} שאלות מוכנות למערכת הבחינה")


if __name__ == "__main__":
    main()