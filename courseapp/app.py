"""
אפליקציית Streamlit ללמידה למבחן - ניהול משאבי אנוש
כולל מערכת בחינה אינטראקטיבית
"""
import streamlit as st
import json
import random
from pathlib import Path

st.set_page_config(page_title="ניהול משאבי אנוש", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.stApp,.stMarkdown,p,h1,h2,h3,h4,h5,h6,li,span,div{direction:rtl;text-align:right}
.main .block-container{padding-top:2rem;max-width:1000px}
[data-testid="stSidebar"]{direction:rtl}
[data-testid="stSidebar"] .stMarkdown{direction:rtl;text-align:right}
#MainMenu{visibility:hidden}footer{visibility:hidden}
</style>""", unsafe_allow_html=True)

def get_base_dir(): return Path(__file__).parent.parent
def get_app_dir(): return Path(__file__).parent

def load_exam_questions():
    jp = get_app_dir() / "exam_questions.json"
    if jp.exists():
        with open(jp, "r", encoding="utf-8") as f: return json.load(f)
    return []

def load_summaries():
    sp = get_app_dir() / "summaries"
    if not sp.exists(): return []
    files = sorted(sp.glob("*.md"))
    summaries = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        # Get title from first line
        title = content.split(chr(10))[0].lstrip("# ").strip()
        summaries.append({"title": title, "file": f, "content": content})
    return summaries


def scan_topics(base_dir):
    topics = {}
    bp = Path(base_dir)
    tc = {"נושאים 1 - 3":{"icon":"📚","order":1,"name":"מבוא, מיון והבדלים אינדיבידואליים"},"נושא 4":{"icon":"👥","order":2,"name":"קבוצות בארגון"},"נושא 5 - קונפליקטים":{"icon":"⚡","order":3,"name":"ניהול קונפליקטים"},"נושא 6 - מוטיבציה":{"icon":"🚀","order":4,"name":"מוטיבציה"},"נושא 7 -משוב":{"icon":"💬","order":5,"name":"משוב"},"שינוי כיתה הפוכה":{"icon":"🔄","order":6,"name":"שינוי ארגוני"}}
    for d in sorted(bp.iterdir()):
        if not d.is_dir() or d.name in ("courseapp",".DS_Store","__pycache__","מבחנים"): continue
        cfg = tc.get(d.name, {"icon":"📖","order":99,"name":d.name})
        md = sorted(d.glob("*.md"))
        qf = [f for f in md if "שאלו" in f.stem or "שאלון" in f.stem]
        af = [f for f in md if "תשובו" in f.stem]
        cf = [f for f in md if f not in qf and f not in af]
        if md: topics[d.name] = {"name":cfg["name"],"icon":cfg["icon"],"order":cfg["order"],"path":d,"content_files":cf,"question_files":qf,"answer_files":af,"all_files":md}
    return dict(sorted(topics.items(), key=lambda x: x[1]["order"]))

def load_md(fp):
    try: return Path(fp).read_text(encoding="utf-8")
    except: return "שגיאה בטעינה"

def get_topic_connection(topic):
    c={"מבוא ומיון":"📚 קשור לנושאים 1-2: מבוא ומיון וגיוס. חזור למצגות נושא 1_מבוא ונושא 2_מיון בתיקיית נושאים 1-3.","הבדלים אינדיבידואליים":"👤 קשור לנושא 3: הבדלים אינדיבידואליים ומודל Big Five. חזור למצגת נושא 3_הבדלים אינדיבידואליים.","קבוצות":"👥 קשור לנושא 4: קבוצות בארגון ודינמיקה קבוצתית. חזור למצגות קבוצות חלק 1-4.","קונפליקטים":"⚡ קשור לנושא 5: ניהול קונפליקטים וסגנונות התמודדות. חזור למצגת ניהול קונפליקטים.","מוטיבציה":"🚀 קשור לנושא 6: מוטיבציה ותיאוריות הנעה. חזור למצגת מוטיבציה.","משוב":"💬 קשור לנושא 7: משוב והערכת עובדים. חזור למצגת נושא 7_משוב.","שינוי ארגוני":"🔄 קשור לנושא שינוי ארגוני ומודלים לשינוי. חזור למצגות שינוי ארגוני חלק 1-5.","כללי":"📖 נושא כללי בקורס. חזור לחומרי הלימוד הרלוונטיים."}
    return c.get(topic, c["כללי"])

# Session State
for k,v in [("completed_lessons",set()),("current_topic",None),("current_page","home"),("exam_questions",[]),("exam_idx",0),("exam_wrong",[]),("exam_score",{"correct":0,"wrong":0,"total":0}),("exam_active",False),("exam_answered",False),("exam_retry",False),("exam_selected",None),("exam_force_retry",True),("history",[]),("question_stats",{})]:
    if k not in st.session_state: st.session_state[k] = v

def main():
    topics = scan_topics(get_base_dir())
    exam_q = load_exam_questions()
    with st.sidebar:
        st.markdown("## 🎓 ניהול משאבי אנוש")
        st.markdown("---")
        tl = sum(len(t["all_files"]) for t in topics.values())
        dn = len(st.session_state.completed_lessons)
        st.markdown(f"### 📊 {int(dn/tl*100) if tl else 0}% הושלם")
        st.progress(dn/tl if tl else 0)
        st.markdown("---")
        if st.button("🏠 בית",use_container_width=True): st.session_state.current_page="home"; st.rerun()
        if st.button("📝 בחינה",use_container_width=True): st.session_state.current_page="exam"; st.rerun()
        if st.button("📊 אנליזה",use_container_width=True): st.session_state.current_page="analytics"; st.rerun()
        if st.button("📖 סיכומים",use_container_width=True): st.session_state.current_page="summaries"; st.rerun()
        st.markdown("---")
        for key,t in topics.items():
            if st.button(f"{t['icon']} {t['name']}",key=f"sb_{key}",use_container_width=True):
                st.session_state.current_page="topic"; st.session_state.current_topic=key; st.rerun()
        st.markdown("---")
        if st.button("🔄 אפס",use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
    if st.session_state.current_page=="exam": render_exam(exam_q)
    elif st.session_state.current_page=="analytics": render_analytics()
    elif st.session_state.current_page=="summaries": render_summaries()
    elif st.session_state.current_page=="topic" and st.session_state.current_topic in topics: render_topic(topics[st.session_state.current_topic])
    else: render_home(topics,exam_q)

def render_summaries():
    st.markdown("# 📖 סיכומי הקורס")
    st.markdown("סיכומים מקיפים לכל נושאי הקורס מבוססים על תמלולי ההרצאות והמצגות")
    st.markdown("---")
    summaries = load_summaries()
    if not summaries:
        st.warning("לא נמצאו סיכומים בתיקיית summaries/")
        return
    titles = [s["title"] for s in summaries]
    selected = st.selectbox("בחר נושא:", titles)
    idx = titles.index(selected)
    st.markdown("---")
    st.markdown(summaries[idx]["content"])

def render_home(topics,eq):
    st.markdown("# 🎓 ניהול משאבי אנוש - למידה למבחן")
    # Count questions answered correctly at least once
    mastered = sum(1 for v in st.session_state.question_stats.values() if v["correct"] > 0)
    c1,c2,c3,c4=st.columns(4)
    with c1: st.metric("📚 נושאים",len(topics))
    with c2: st.metric("❓ שאלות במאגר",len(eq))
    with c3: st.metric("✅ נענו נכון",f"{mastered}/{len(eq)}")
    with c4: st.metric("📄 שיעורים",len(st.session_state.completed_lessons))
    st.markdown("---")
    if st.button("🚀 התחל בחינה",use_container_width=True): st.session_state.current_page="exam"; st.rerun()
    if st.session_state.exam_score["total"]>0:
        s=st.session_state.exam_score
        st.info(f"📊 ציון אחרון: {s['correct']}/{s['total']} ({int(s['correct']/s['total']*100)}%)")
    st.markdown("---")
    for key,topic in topics.items():
        n=len(topic["all_files"])
        d=sum(1 for f in topic["all_files"] if str(f) in st.session_state.completed_lessons)
        c1,c2=st.columns([4,1])
        with c1: st.markdown(f"**{topic['icon']} {topic['name']}** — {n} קבצים")
        with c2:
            if st.button("📖",key=f"h_{key}"): st.session_state.current_page="topic"; st.session_state.current_topic=key; st.rerun()
        if n>0: st.progress(d/n)

def render_topic(topic):
    st.markdown(f"# {topic['icon']} {topic['name']}")
    if st.button("← חזרה"): st.session_state.current_page="home"; st.rerun()
    st.markdown("---")
    has_q = bool(topic["question_files"] or topic["answer_files"])
    tabs = st.tabs(["📖 למידה"]+([" 📝 תרגול"] if has_q else []))
    with tabs[0]:
        files=topic["content_files"]
        if not files: st.info("הרץ: python extract_content.py"); return
        if len(files)>1:
            names=[f.stem for f in files]
            sel=st.selectbox("שיעור:",names,key=f"s_{topic['name']}")
            f=files[names.index(sel)]
        else: f=files[0]
        fk=str(f)
        if st.checkbox("סיימתי ✅",value=fk in st.session_state.completed_lessons,key=f"d_{fk}"):
            st.session_state.completed_lessons.add(fk)
        else: st.session_state.completed_lessons.discard(fk)
        st.markdown("---")
        st.markdown(load_md(f))
    if has_q and len(tabs)>1:
        with tabs[1]:
            for qf in topic["question_files"]+topic["answer_files"]:
                st.markdown(f"#### {qf.stem}")
                st.markdown(load_md(qf))

def render_exam(all_q):
    st.markdown("# 📝 מערכת בחינה אינטראקטיבית")
    if not all_q: st.error("הרץ: python parse_exams.py"); return
    if not st.session_state.exam_active:
        st.markdown(f"### מאגר: {len(all_q)} שאלות אמריקאיות ממבחנים קודמים")
        st.markdown("**מאפיינים:** מעקב תשובות • חזרה על טעויות • קישור לחומר הקורס • מדידת הצלחה")
        st.markdown("---")
        num=st.slider("מספר שאלות:",5,len(all_q),min(20,len(all_q)))
        st.session_state.exam_force_retry = st.toggle("🔄 חזרה כפויה על שאלות שגויות", value=st.session_state.exam_force_retry)
        if st.button("🚀 התחל בחינה",use_container_width=True):
            st.session_state.exam_questions=random.sample(all_q,num)
            st.session_state.exam_idx=0; st.session_state.exam_wrong=[]
            st.session_state.exam_score={"correct":0,"wrong":0,"total":num}
            st.session_state.exam_active=True; st.session_state.exam_answered=False
            st.session_state.exam_retry=False; st.session_state.exam_selected=None
            st.rerun()
        if st.session_state.exam_score["total"]>0:
            s=st.session_state.exam_score
            st.success(f"📊 תוצאות אחרונות: {s['correct']}/{s['total']} ({int(s['correct']/s['total']*100)}%)")
        return

    qs=st.session_state.exam_questions
    idx=st.session_state.exam_idx

    if idx>=len(qs):
        if st.session_state.exam_wrong and st.session_state.exam_force_retry:
            st.warning(f"🔄 **חזרה כפויה:** יש {len(st.session_state.exam_wrong)} שאלות שטעית בהן. חובה לענות עליהן שוב!")
            if st.button("▶️ המשך לחזרה על טעויות",use_container_width=True):
                random.shuffle(st.session_state.exam_wrong)
                st.session_state.exam_questions=st.session_state.exam_wrong[:]
                st.session_state.exam_wrong=[]; st.session_state.exam_idx=0
                st.session_state.exam_answered=False; st.session_state.exam_selected=None
                st.session_state.exam_retry=True; st.rerun()
        else:
            s=st.session_state.exam_score
            pct=int(s["correct"]/s["total"]*100) if s["total"]>0 else 0
            st.balloons()
            st.markdown(f"## 🎉 סיימת! ציון סופי: {s['correct']}/{s['total']} ({pct}%)")
            if pct>=90: st.success("מצוין! את/ה מוכן/ה למבחן! 🌟")
            elif pct>=70: st.info("טוב מאוד! עוד קצת תרגול 💪")
            else: st.warning("כדאי לחזור על החומר 📚")
            # Save to history
            if not st.session_state.exam_retry:
                st.session_state.history.append({"correct":s["correct"],"total":s["total"],"pct":pct})
            if st.button("🔄 בחינה חדשה",use_container_width=True):
                st.session_state.exam_active=False; st.rerun()
        return

    # Show current question
    q=qs[idx]
    retry_label = " (חזרה על טעויות)" if st.session_state.exam_retry else ""
    st.markdown(f"### שאלה {idx+1} מתוך {len(qs)}{retry_label}")
    s=st.session_state.exam_score
    st.markdown(f"✅ {s['correct']} נכונות | ❌ {s['wrong']} שגויות")
    st.progress((idx)/len(qs))
    st.markdown("---")
    # Question text
    st.markdown(f"**{q['question']}**")
    st.markdown("")

    # Options as radio buttons
    options = q.get('options', [])
    if not st.session_state.exam_answered:
        selected = st.radio("בחר תשובה:", options, key=f"q_{idx}", index=None)
        if selected and st.button("✔️ בדוק תשובה", use_container_width=True):
            st.session_state.exam_selected = selected
            st.session_state.exam_answered = True
            correct = q.get('correct', '')
            # Track stats
            qkey = q['question'][:60]
            if qkey not in st.session_state.question_stats:
                st.session_state.question_stats[qkey] = {"correct":0,"wrong":0,"topic":q.get("topic",""),"question":q["question"][:100]}
            if selected == correct:
                st.session_state.exam_score['correct'] += 1
                st.session_state.question_stats[qkey]["correct"] += 1
            else:
                st.session_state.exam_score['wrong'] += 1
                st.session_state.exam_wrong.append(q)
                st.session_state.question_stats[qkey]["wrong"] += 1
            st.rerun()
    else:
        selected = st.session_state.exam_selected
        correct = q.get('correct', '')
        is_correct = (selected == correct)

        for opt in options:
            if opt == correct:
                st.success(f"✅ {opt}")
            elif opt == selected and not is_correct:
                st.error(f"❌ {opt}")
            else:
                st.markdown(f"  {opt}")

        st.markdown("---")
        if is_correct:
            st.markdown("### ✅ תשובה נכונה! כל הכבוד!")
        else:
            st.markdown(f"### ❌ טעות! התשובה הנכונה: {correct}")
            st.markdown("*שאלה זו תחזור שוב בסוף הבחינה*")

        # Topic connection
        topic = q.get('topic', 'כללי')
        connection = get_topic_connection(topic)
        st.info(f"🔗 **קשר לחומר הקורס:** {connection}")

        st.markdown("---")
        if st.button("➡️ שאלה הבאה", use_container_width=True):
            st.session_state.exam_idx += 1
            st.session_state.exam_answered = False
            st.session_state.exam_selected = None
            st.rerun()

def render_analytics():
    st.markdown("# 📊 אנליזת ביצועים")
    history = st.session_state.history
    qstats = st.session_state.question_stats

    if not history and not qstats:
        st.info("🔍 אין עדיין נתונים. השלם לפחות בחינה אחת כדי לראות אנליזה.")
        return

    # Overall stats
    st.markdown("## 📈 מגמת ציונים לאורך זמן")
    if history:
        import datetime
        cols = st.columns(3)
        with cols[0]: st.metric("בחינות שהושלמו", len(history))
        with cols[1]: st.metric("ציון אחרון", f"{history[-1]['pct']}%")
        avg = int(sum(h['pct'] for h in history)/len(history))
        with cols[2]: st.metric("ממוצע כללי", f"{avg}%")
        
        # Progress display
        st.markdown("### ציונים לפי ניסיון:")
        for i, h in enumerate(history):
            bar = "█" * (h["pct"]//5) + "░" * (20 - h["pct"]//5)
            st.markdown(f"ניסיון {i+1}: `{bar}` **{h['pct']}%**")
        
        # Improvement indicator
        if len(history) >= 2:
            diff = history[-1]['pct'] - history[0]['pct']
            if diff > 0: st.success(f"📈 שיפור של {diff}% מהניסיון הראשון!")
            elif diff < 0: st.warning(f"📉 ירידה של {abs(diff)}% מהניסיון הראשון. המשך לתרגל!")
            else: st.info("➡️ ציון יציב. נסה להתמקד בנושאים החלשים שלך")
    
    st.markdown("---")

    # Topic analysis
    st.markdown("## 🎯 ביצוע לפי נושא")
    topic_agg = {}
    for k, v in qstats.items():
        t = v.get("topic", "כללי")
        if t not in topic_agg: topic_agg[t] = {"correct":0, "wrong":0}
        topic_agg[t]["correct"] += v["correct"]
        topic_agg[t]["wrong"] += v["wrong"]
    
    if topic_agg:
        for topic in sorted(topic_agg.keys()):
            d = topic_agg[topic]
            total = d["correct"] + d["wrong"]
            pct = int(d["correct"]/total*100) if total > 0 else 0
            col1, col2 = st.columns([3,1])
            with col1:
                color = "🟢" if pct >= 80 else "🟡" if pct >= 60 else "🔴"
                st.markdown(f"{color} **{topic}**: {d['correct']}/{total} ({pct}%)")
            with col2:
                st.progress(pct/100)
    
    st.markdown("---")

    # Weak questions
    st.markdown("## ❌ שאלות בעייתיות (הכי הרבה טעויות)")
    weak = sorted(qstats.items(), key=lambda x: x[1]["wrong"], reverse=True)
    weak_shown = 0
    for k, v in weak:
        if v["wrong"] == 0: continue
        if weak_shown >= 10: break
        total = v["correct"] + v["wrong"]
        fail_rate = int(v["wrong"]/total*100)
        st.markdown(f"**{v['question']}**")
        st.markdown(f"  ❌ {v['wrong']} טעויות | ✅ {v['correct']} נכונות | שיעור כישלון: {fail_rate}% | נושא: _{v.get('topic','')}_")
        st.markdown("---")
        weak_shown += 1
    
    if weak_shown == 0:
        st.success("🎉 אין שאלות בעייתיות! כל הכבוד!")

    # Recommendations
    st.markdown("## 💡 המלצות לשיפור")
    if topic_agg:
        weakest = min(topic_agg.items(), key=lambda x: x[1]["correct"]/(x[1]["correct"]+x[1]["wrong"]+0.01) )
        st.markdown(f"🎯 **הנושא החלש ביותר שלך: {weakest[0]}**")
        st.markdown(f"  → {get_topic_connection(weakest[0])}")
        st.markdown("")
        strongest = max(topic_agg.items(), key=lambda x: x[1]["correct"]/(x[1]["correct"]+x[1]["wrong"]+0.01) )
        st.markdown(f"💪 **הנושא החזק ביותר שלך: {strongest[0]}**")

if __name__ == "__main__":
    main()
