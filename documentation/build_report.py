from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re, os, json, textwrap

ROOT = Path(r"C:\Users\chatu\OneDrive\Pictures\podcast_summarisation_project")
OUT = ROOT / "documentation"
ASSETS = Path(os.environ.get("TEMP", ".")) / "podly_report_assets"
OUT.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)
DOCX_PATH = OUT / "Podcast_Summarisation_and_Chapter_Generator_Project_Report.docx"

NAVY = "17324D"
TEAL = "258C83"
PALE = "EAF3F2"
INK = "24313D"
MUTED = "5E6B75"
RULE = "DCE5E8"
GOLD = "D79A32"
WHITE = "FFFFFF"

# ---------- Diagram helpers ----------
FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
BOLD_PATH = r"C:\Windows\Fonts\arialbd.ttf"
def fnt(size, bold=False):
    path = BOLD_PATH if bold else FONT_PATH
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def rounded_box(draw, box, title, subtitle="", fill="#EAF3F2", outline="#258C83", title_color="#17324D", width=3):
    draw.rounded_rectangle(box, radius=22, fill=fill, outline=outline, width=width)
    x1,y1,x2,y2 = box
    font_title = fnt(27, True)
    font_sub = fnt(19)
    lines = textwrap.wrap(title, width=max(12, int((x2-x1)/17)))
    total_h = len(lines)*34 + (28 if subtitle else 0)
    y = y1 + (y2-y1-total_h)//2
    for line in lines:
        bb=draw.textbbox((0,0),line,font=font_title)
        draw.text((x1+(x2-x1-(bb[2]-bb[0]))/2,y),line,font=font_title,fill=title_color)
        y += 34
    if subtitle:
        for line in textwrap.wrap(subtitle, width=max(18, int((x2-x1)/13))):
            bb=draw.textbbox((0,0),line,font=font_sub)
            draw.text((x1+(x2-x1-(bb[2]-bb[0]))/2,y),line,font=font_sub,fill="#52616C")
            y += 25

def arrow(draw, a, b, label="", color="#536B7A", width=4, dash=False):
    draw.line([a,b], fill=color, width=width)
    import math
    ang=math.atan2(b[1]-a[1],b[0]-a[0])
    size=15
    p1=(b[0]-size*math.cos(ang-0.48), b[1]-size*math.sin(ang-0.48))
    p2=(b[0]-size*math.cos(ang+0.48), b[1]-size*math.sin(ang+0.48))
    draw.polygon([b,p1,p2],fill=color)
    if label:
        mx=(a[0]+b[0])//2; my=(a[1]+b[1])//2-18
        bb=draw.textbbox((0,0),label,font=fnt(17))
        draw.rounded_rectangle((mx-(bb[2]-bb[0])//2-8,my-3,mx+(bb[2]-bb[0])//2+8,my+25),radius=6,fill="#FFFFFF")
        draw.text((mx-(bb[2]-bb[0])//2,my),label,font=fnt(17),fill="#40515D")

def canvas(name, title, subtitle=""):
    im=Image.new("RGB",(1600,900),"#F7FAFA")
    d=ImageDraw.Draw(im)
    d.text((70,38),title,font=fnt(38,True),fill="#17324D")
    if subtitle: d.text((72,89),subtitle,font=fnt(21),fill="#61717C")
    d.line((70,132,1530,132),fill="#D9E4E7",width=2)
    return im,d

def save_diagrams():
    # Figure: context diagram
    im,d=canvas("context","Context Diagram - Level 0","The web application accepts user-supplied audio and returns navigable analysis.")
    rounded_box(d,(85,335,390,530),"Podcast user","Uploads audio; reviews and exports results",fill="#FFF7E8",outline="#D79A32")
    rounded_box(d,(630,320,970,540),"Podly AI","Browser interface and FastAPI service",fill="#E6F2F1")
    rounded_box(d,(1220,220,1515,380),"Local storage","SQLite records, uploaded audio, exports")
    rounded_box(d,(1220,520,1515,680),"AI and media tools","Whisper, FFmpeg, Mutagen")
    arrow(d,(390,385),(630,385),"Audio and actions")
    arrow(d,(630,485),(390,485),"Brief, chapters, status")
    arrow(d,(970,370),(1220,300),"Jobs and results")
    arrow(d,(1220,575),(970,485),"Transcription and tags")
    im.save(ASSETS/"fig01_context.png")

    # Figure: architecture
    im,d=canvas("architecture","System Architecture","A single-process web application with a local background worker.")
    rounded_box(d,(75,285,355,500),"React client","Vite, TypeScript, Tailwind")
    rounded_box(d,(465,285,755,500),"FastAPI REST API","Validation, episode and job routes")
    rounded_box(d,(880,245,1175,390),"Processing worker","Thread pool, default 1 worker")
    rounded_box(d,(880,445,1175,590),"SQLite database","Podcasts, jobs, segments, chapters")
    rounded_box(d,(1290,245,1530,390),"AI pipeline","Whisper Tiny, fast grouping, summaries")
    rounded_box(d,(1290,445,1530,590),"File storage","Uploads, exports, model cache")
    arrow(d,(355,390),(465,390),"HTTP / JSON")
    arrow(d,(755,350),(880,320),"Submit job")
    arrow(d,(755,435),(880,505),"Read / write")
    arrow(d,(1175,320),(1290,320),"Transcribe")
    arrow(d,(1175,505),(1290,505),"Audio / outputs")
    arrow(d,(880,390),(755,390),"Progress")
    im.save(ASSETS/"fig02_architecture.png")

    # Figure: data flow
    im,d=canvas("dataflow","Data Flow Diagram - Level 1","Audio moves through validation, transcription, chapter generation and persistence.")
    boxes=[
      ((55,300,280,495),"1. Upload","Validate extension and size"),
      ((355,300,580,495),"2. Inspect","Read stream metadata"),
      ((655,300,890,495),"3. Transcribe","Whisper speech-to-text"),
      ((965,300,1205,495),"4. Structure","Group and summarize"),
      ((1280,300,1530,495),"5. Deliver","Store, play and export"),
    ]
    for b,t,s in boxes: rounded_box(d,b,t,s)
    for x1,x2,l in [(280,355,"Audio"),(580,655,"Valid file"),(890,965,"Timed text"),(1205,1280,"Chapters")]:
        arrow(d,(x1,400),(x2,400),l)
    rounded_box(d,(405,615,750,760),"D1 - SQLite","Episode, job, transcript, chapter",fill="#EEF2F8",outline="#6782A3")
    rounded_box(d,(860,615,1220,760),"D2 - File system","Original audio and generated exports",fill="#EEF2F8",outline="#6782A3")
    arrow(d,(1070,495),(660,615),"Persist structured results")
    arrow(d,(1390,495),(1110,615),"Save audio and files")
    arrow(d,(580,615),(500,495),"Job status")
    im.save(ASSETS/"fig03_dataflow.png")

    # Figure: use case
    im,d=canvas("usecase","Use Case Diagram","Primary actor: a listener or student working with an uploaded episode.")
    d.rounded_rectangle((400,185,1530,790),radius=26,outline="#9EB2B6",width=3,fill="#FFFFFF")
    d.text((435,205),"PODLY AI SYSTEM",font=fnt(24,True),fill="#17324D")
    # stick person
    d.ellipse((115,320,175,380),outline="#17324D",width=5)
    d.line((145,380,145,535),fill="#17324D",width=5)
    d.line((145,415,80,475),fill="#17324D",width=5)
    d.line((145,415,210,475),fill="#17324D",width=5)
    d.line((145,535,90,620),fill="#17324D",width=5)
    d.line((145,535,200,620),fill="#17324D",width=5)
    d.text((85,660),"Listener",font=fnt(25,True),fill="#17324D")
    usecases=[("Upload audio",280),("Monitor analysis",385),("Play and navigate chapters",490),("Search transcript",595),("Edit / copy chapter notes",700),("Download exports",805)]
    for label,y in usecases:
        d.ellipse((650,y-40,1120,y+35),fill="#EAF3F2",outline="#258C83",width=3)
        bb=d.textbbox((0,0),label,font=fnt(21,True)); d.text((885-(bb[2]-bb[0])/2,y-12),label,font=fnt(21,True),fill="#17324D")
        arrow(d,(210,465),(650,y-2),"")
    im.save(ASSETS/"fig04_usecase.png")

    # Figure: sequence
    im,d=canvas("sequence","Sequence Diagram - Episode Analysis","The browser polls the job endpoint until processing is complete.")
    lanes=[("Listener",95),("React UI",390),("FastAPI",690),("Worker / AI",1000),("SQLite / files",1330)]
    for name,x in lanes:
        d.rounded_rectangle((x-85,175,x+85,235),radius=12,fill="#EAF3F2",outline="#258C83",width=2)
        bb=d.textbbox((0,0),name,font=fnt(18,True)); d.text((x-(bb[2]-bb[0])/2,195),name,font=fnt(18,True),fill="#17324D")
        d.line((x,235,x,790),fill="#B9C9CC",width=2)
    seq=[(95,390,290,"Select and upload audio"),(390,690,365,"Validate; stream file"),(690,1330,440,"Create episode and job"),(690,1000,515,"Submit job"),(1000,1330,590,"Transcribe and analyze"),(1000,1330,665,"Save segments, chapters, exports"),(390,690,730,"Poll job status"),(690,390,785,"Return status and results")]
    for x1,x2,y,label in seq:
        arrow(d,(x1,y),(x2,y),label)
    im.save(ASSETS/"fig05_sequence.png")

    # Figure: ER diagram
    im,d=canvas("erd","Entity Relationship Diagram","Primary records use UUID strings; relationship foreign keys are indexed.")
    def entity(box,title,fields):
        x1,y1,x2,y2=box
        d.rounded_rectangle(box,radius=16,fill="#FFFFFF",outline="#258C83",width=3)
        d.rounded_rectangle((x1,y1,x2,y1+50),radius=16,fill="#17324D")
        d.rectangle((x1,y1+28,x2,y1+50),fill="#17324D")
        d.text((x1+18,y1+12),title,font=fnt(21,True),fill="#FFFFFF")
        y=y1+67
        for field in fields:
            d.text((x1+18,y),field,font=fnt(17),fill="#273946"); y+=27
    entity((50,190,450,495),"PODCAST",["PK id","UQ job_id","title, original_filename","file_path, file_size_bytes","duration, format, channels","word_count, topic_count","status, error_message","created_at, completed_at"])
    entity((585,190,980,390),"PROCESSING_JOB",["PK id","FK podcast_id","stage, progress","message, error","created_at, updated_at"])
    entity((1100,160,1545,420),"TRANSCRIPT_SEGMENT",["PK id","FK podcast_id","segment_index","start_time, end_time","text, topic_id, topic_label","confidence"])
    entity((1100,535,1545,790),"CHAPTER",["PK id","FK podcast_id","chapter_number, title","start_time, end_time","topic_id, topic_label","topic_keywords, summary","segment_ids, is_edited"])
    arrow(d,(450,285),(585,285),"1 : 1")
    arrow(d,(450,380),(1100,300),"1 : many")
    arrow(d,(450,415),(1100,650),"1 : many")
    im.save(ASSETS/"fig06_erd.png")

    # Figure: dashboard wireframe
    im,d=canvas("dashboard_wireframe","Dashboard Wireframe","Simplified layout of the current responsive library entry point.")
    d.rounded_rectangle((75,165,1525,815),radius=26,fill="#FFFFFF",outline="#AABCC0",width=3)
    d.rectangle((75,165,250,815),fill="#F0F5F4")
    d.text((105,195),"PODLY",font=fnt(25,True),fill="#17324D")
    for i,label in enumerate(["Home","Library","Settings"]):
        d.rounded_rectangle((95,270+i*65,230,315+i*65),radius=10,fill="#E3EFED")
        d.text((115,282+i*65),label,font=fnt(19),fill="#40515D")
    d.rounded_rectangle((280,190,1490,255),radius=12,fill="#F8FAFA",outline="#DCE5E8",width=2)
    d.text((315,211),"Search your library",font=fnt(20),fill="#7A8990")
    d.rounded_rectangle((280,285,1490,485),radius=18,fill="#EEF6F4",outline="#C9DDDA",width=2)
    d.text((320,320),"Your listening, made useful.",font=fnt(32,True),fill="#17324D")
    d.text((320,370),"Search episodes, review useful moments, and create a chapter guide.",font=fnt(20),fill="#52616C")
    d.rounded_rectangle((320,410,530,462),radius=12,fill="#258C83")
    d.text((350,426),"Analyze new podcast",font=fnt(18,True),fill="#FFFFFF")
    for i,(label,val) in enumerate([("Analyzed","3"),("Audio duration","2h 34m"),("Chapters","12"),("Words","16.6K")]):
        x=280+i*305
        d.rounded_rectangle((x,515,x+285,595),radius=14,fill="#FFFFFF",outline="#DCE5E8",width=2)
        d.text((x+18,530),label,font=fnt(17),fill="#6A7B83")
        d.text((x+18,555),val,font=fnt(24,True),fill="#17324D")
    d.text((290,640),"RECENT EPISODES",font=fnt(17,True),fill="#53636D")
    for i in range(2):
        y=675+i*58
        d.rounded_rectangle((280,y,1490,y+48),radius=10,fill="#FBFCFC",outline="#E0E7E8",width=1)
        d.text((305,y+14),["Podly Demo Episode","Recording 1476186"][i],font=fnt(18,True),fill="#17324D")
        d.text((1030,y+14),["Ready","Ready"][i],font=fnt(17),fill="#258C83")
    im.save(ASSETS/"fig07_dashboard_wireframe.png")

    # Figure: analysis wireframe
    im,d=canvas("analysis_wireframe","Episode Analysis Wireframe","The brief, chapter navigation, transcript and export views are separate tabs.")
    d.rounded_rectangle((75,165,1525,815),radius=26,fill="#FFFFFF",outline="#AABCC0",width=3)
    d.text((115,190),"Episode title",font=fnt(29,True),fill="#17324D")
    d.rounded_rectangle((110,245,1490,395),radius=18,fill="#F5F8F8",outline="#DCE5E8",width=2)
    d.text((145,270),"Now playing: chapter title",font=fnt(19,True),fill="#53636D")
    d.line((145,325,1450,325),fill="#258C83",width=7)
    d.ellipse((535,314,559,338),fill="#17324D")
    d.ellipse((1030,314,1054,338),fill="#258C83")
    d.text((145,350),"0:00",font=fnt(16),fill="#53636D"); d.text((1390,350),"Duration",font=fnt(16),fill="#53636D")
    navx=110
    labels=["Brief","Chapters","Transcript","Export"]
    for i,label in enumerate(labels):
        x=navx+i*345
        d.rounded_rectangle((x,420,x+320,470),radius=12,fill="#EAF3F2" if i==0 else "#FFFFFF",outline="#DCE5E8",width=2)
        d.text((x+105,435),label,font=fnt(19,True),fill="#17324D")
    d.rounded_rectangle((110,500,1490,775),radius=18,fill="#F8FAFA",outline="#DCE5E8",width=2)
    d.text((145,530),"YOUR EPISODE BRIEF",font=fnt(20,True),fill="#258C83")
    for i,text in enumerate(["Key idea from chapter one","Key idea from chapter two","Key idea from chapter three"]):
        d.ellipse((150,585+i*55,180,615+i*55),fill="#E3EFED")
        d.text((160,590+i*55),str(i+1),font=fnt(16,True),fill="#17324D")
        d.text((200,590+i*55),text,font=fnt(19),fill="#53636D")
    im.save(ASSETS/"fig08_analysis_wireframe.png")

    # Figure: deployment
    im,d=canvas("deployment","Deployment Diagram - Local Development","Current deployment runs the Vite client and FastAPI service on one development computer.")
    rounded_box(d,(75,280,405,510),"User device","Modern browser",fill="#FFF7E8",outline="#D79A32")
    rounded_box(d,(555,210,965,350),"Frontend dev server","Vite at localhost:5173")
    rounded_box(d,(555,435,965,575),"Backend API","Uvicorn / FastAPI at localhost:8000")
    rounded_box(d,(1100,210,1515,350),"SQLite database","Local persistent file")
    rounded_box(d,(1100,435,1515,575),"Local directories","Uploads, exports, model cache")
    arrow(d,(405,350),(555,280),"HTTP")
    arrow(d,(405,430),(555,500),"REST / JSON")
    arrow(d,(965,280),(965,435),"API proxy")
    arrow(d,(965,500),(1100,280),"SQLAlchemy")
    arrow(d,(965,520),(1100,500),"Audio / files")
    im.save(ASSETS/"fig09_deployment.png")


# ---------- Document helpers ----------
doc = Document()
sec = doc.sections[0]
sec.page_width = Inches(8.27)
sec.page_height = Inches(11.69)
sec.top_margin = Inches(0.72)
sec.bottom_margin = Inches(0.72)
sec.left_margin = Inches(0.82)
sec.right_margin = Inches(0.82)
sec.header_distance = Inches(0.32)
sec.footer_distance = Inches(0.35)
sec.different_first_page_header_footer = True

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "Arial"; normal.font.size = Pt(10)
normal.font.color.rgb = RGBColor.from_string(INK)
normal.paragraph_format.space_after = Pt(5)
normal.paragraph_format.line_spacing = 1.12
for style_name,size,color in [("Title",28,NAVY),("Subtitle",14,MUTED),("Heading 1",18,NAVY),("Heading 2",13,TEAL),("Heading 3",11,NAVY)]:
    s=styles[style_name]
    s.font.name="Arial"; s.font.size=Pt(size); s.font.bold=style_name!="Subtitle"
    s.font.color.rgb=RGBColor.from_string(color)
    s.paragraph_format.space_before=Pt(12 if style_name!="Title" else 0)
    s.paragraph_format.space_after=Pt(6)
    s.paragraph_format.keep_with_next=True
styles["Heading 1"].paragraph_format.page_break_before=False
styles["List Bullet"].font.name="Arial"; styles["List Bullet"].font.size=Pt(10)
styles["List Number"].font.name="Arial"; styles["List Number"].font.size=Pt(10)

# Header / footer
header = sec.header
hp = header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
run=hp.add_run("PODCAST SUMMARISATION AND CHAPTER GENERATOR")
run.font.name="Arial"; run.font.size=Pt(8); run.font.bold=True; run.font.color.rgb=RGBColor.from_string(MUTED)
hp.paragraph_format.space_after=Pt(2)
hp2=header.add_paragraph()
hp2.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=hp2.add_run("PROJECT GROUP 17  |  2025-26")
r.font.name="Arial"; r.font.size=Pt(8); r.font.color.rgb=RGBColor.from_string(MUTED)
footer=sec.footer
fp=footer.paragraphs[0]
fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=fp.add_run("Project Group 17  |  Page ")
r.font.name="Arial"; r.font.size=Pt(8); r.font.color.rgb=RGBColor.from_string(MUTED)
fld=OxmlElement("w:fldSimple"); fld.set(qn("w:instr"),"PAGE"); fp._p.append(fld)

def shade(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr()
    shd=OxmlElement("w:shd"); shd.set(qn("w:fill"),fill); tcPr.append(shd)

def set_cell_text(cell,text,bold=False,color=INK,size=9):
    cell.text=""
    p=cell.paragraphs[0]
    p.paragraph_format.space_after=Pt(2)
    p.paragraph_format.space_before=Pt(2)
    r=p.add_run(str(text))
    r.bold=bold; r.font.name="Arial"; r.font.size=Pt(size); r.font.color.rgb=RGBColor.from_string(color)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER

def set_repeat_table_header(row):
    trPr=row._tr.get_or_add_trPr()
    tblHeader=OxmlElement("w:tblHeader"); tblHeader.set(qn("w:val"),"true"); trPr.append(tblHeader)

def add_table(headers, rows, widths=None, font_size=8.8):
    table=doc.add_table(rows=1, cols=len(headers))
    table.alignment=WD_TABLE_ALIGNMENT.CENTER
    table.style="Table Grid"
    table.autofit=False
    for i,h in enumerate(headers):
        set_cell_text(table.rows[0].cells[i],h,True,WHITE,font_size)
        shade(table.rows[0].cells[i],NAVY)
    set_repeat_table_header(table.rows[0])
    for rowno,row in enumerate(rows):
        cells=table.add_row().cells
        for i,value in enumerate(row):
            set_cell_text(cells[i],value,False,INK,font_size)
            if rowno%2==1: shade(cells[i],"F1F6F6")
        trPr=table.rows[-1]._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
    if widths:
        for row in table.rows:
            for i,w in enumerate(widths):
                row.cells[i].width=Inches(w)
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
    return table

def para(text, style=None, boldlead=None, align=None):
    p=doc.add_paragraph(style=style)
    if align is not None: p.alignment=align
    if boldlead and text.startswith(boldlead):
        r=p.add_run(boldlead); r.bold=True
        p.add_run(text[len(boldlead):])
    else: p.add_run(text)
    return p

def bullet(text, level=0):
    style="List Bullet" if level==0 else "List Bullet 2"
    p=doc.add_paragraph(style=style); p.paragraph_format.space_after=Pt(2); p.add_run(text); return p

def numbered(text):
    p=doc.add_paragraph(style="List Number"); p.paragraph_format.space_after=Pt(3); p.add_run(text); return p

def caption(text):
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(9)
    r=p.add_run(text); r.italic=True; r.font.size=Pt(8.5); r.font.color.rgb=RGBColor.from_string(MUTED)

def figure(path, caption_text, width=6.55):
    doc.add_picture(str(path),width=Inches(width))
    doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER
    caption(caption_text)

def codeblock(text):
    p=doc.add_paragraph()
    p.paragraph_format.left_indent=Inches(0.18); p.paragraph_format.right_indent=Inches(0.12)
    p.paragraph_format.space_before=Pt(3); p.paragraph_format.space_after=Pt(7)
    p.paragraph_format.keep_together=True
    pPr=p._p.get_or_add_pPr()
    shd=OxmlElement("w:shd"); shd.set(qn("w:fill"),"F2F5F6"); pPr.append(shd)
    for i,line in enumerate(text.strip("\n").splitlines()):
        if i: p.add_run().add_break()
        r=p.add_run(line); r.font.name="Consolas"; r.font.size=Pt(8.5); r.font.color.rgb=RGBColor.from_string("273A46")
    return p

def chapter(title, sections, page_break=True):
    if page_break: doc.add_page_break()
    doc.add_heading(title,level=1)
    for item in sections:
        kind=item[0]
        if kind=="p": para(item[1])
        elif kind=="h": doc.add_heading(item[1],level=2)
        elif kind=="h3": doc.add_heading(item[1],level=3)
        elif kind=="b":
            for value in item[1]: bullet(value)
        elif kind=="n":
            for value in item[1]: numbered(value)
        elif kind=="table": add_table(item[1],item[2],item[3] if len(item)>3 else None,item[4] if len(item)>4 else 8.8)
        elif kind=="fig": figure(item[1],item[2],item[3] if len(item)>3 else 6.55)
        elif kind=="code": codeblock(item[1])
        elif kind=="note":
            p=doc.add_paragraph()
            p.paragraph_format.left_indent=Inches(.12)
            p.paragraph_format.space_before=Pt(4); p.paragraph_format.space_after=Pt(8)
            r=p.add_run(item[1]); r.italic=True; r.font.color.rgb=RGBColor.from_string(TEAL)
        elif kind=="page": doc.add_page_break()

def add_cover():
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(22); p.paragraph_format.space_after=Pt(4)
    r=p.add_run("MAHARAJ SHIKSHAN SANSTHA'S"); r.bold=True; r.font.name="Arial"; r.font.size=Pt(14); r.font.color.rgb=RGBColor.from_string(NAVY)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4)
    r=p.add_run("CHH. SHAHU COLLEGE OF ENGINEERING"); r.bold=True; r.font.name="Arial"; r.font.size=Pt(18); r.font.color.rgb=RGBColor.from_string(NAVY)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4)
    r=p.add_run("Approved by AICTE, New Delhi; DTE, Government of Maharashtra; affiliated to Dr. Babasaheb Ambedkar Technological University, Lonere"); r.font.name="Arial"; r.font.size=Pt(9); r.font.color.rgb=RGBColor.from_string(MUTED)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(18)
    r=p.add_run("Kanchanwadi, Paithan Road, Aurangabad 431 002, Maharashtra"); r.font.name="Arial"; r.font.size=Pt(9); r.font.color.rgb=RGBColor.from_string(MUTED)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(30); p.paragraph_format.space_after=Pt(4)
    r=p.add_run("PROJECT REPORT"); r.bold=True; r.font.size=Pt(13); r.font.color.rgb=RGBColor.from_string(TEAL)
    p=doc.add_paragraph(style="Title"); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(4); p.paragraph_format.space_after=Pt(12)
    p.add_run("Podcast Summarisation\nand Chapter Generator")
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(22)
    r=p.add_run("Web-Based Application"); r.font.size=Pt(13); r.font.color.rgb=RGBColor.from_string(MUTED)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(15)
    r=p.add_run("PROJECT GROUP 17"); r.bold=True; r.font.size=Pt(13); r.font.color.rgb=RGBColor.from_string(NAVY)
    add_table(["Project member","Responsibility","Roll number"],[
        ["Anjali Rajkiran Kamble","Team Leader","CS4133"],
        ["Shiwani Deepak Nand","Member 1","CS4110"],
        ["Rajshree Munjaba Bhalshankar","Member 2","CS4146"],
        ["Chaturthi Nanasaheb Gavande","Member 3","CS4114"],
    ],[3.55,1.65,1.0],9)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(7); p.paragraph_format.space_after=Pt(3)
    r=p.add_run("Project Guide: Prof. G. S. Vyas"); r.bold=True; r.font.size=Pt(11); r.font.color.rgb=RGBColor.from_string(NAVY)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(2)
    r=p.add_run("Panel Members: Prof. M. K. Jadhav  |  Prof. P. D. Sathya"); r.font.size=Pt(10); r.font.color.rgb=RGBColor.from_string(MUTED)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(8)
    r=p.add_run("Academic Year 2025-26"); r.bold=True; r.font.size=Pt(10); r.font.color.rgb=RGBColor.from_string(TEAL)

save_diagrams()
add_cover()

# Abstract
doc.add_page_break()
doc.add_heading("Abstract",level=1)
abstract=("Podcasts and long-form spoken recordings contain useful knowledge, but reviewing a full episode to locate a particular idea can take substantial time. This project develops a web-based Podcast Summarisation and Chapter Generator that converts an uploaded audio file into a transcript with timestamps, a concise episode brief, navigable chapter sections, and downloadable outputs. The application combines a React and TypeScript interface with a FastAPI service, a SQLite data store, and a background processing pipeline. Audio metadata is inspected before OpenAI Whisper performs speech recognition. In the default fast mode, transcript segments are grouped into lightweight sections and extractive chapter highlights are generated without downloading a separate summarisation model. Users can play the original audio, jump to chapter timestamps, search the transcript on demand, edit or copy chapter notes, and export a Markdown brief, tagged MP3, transcript, or JSON analysis. A generated demonstration episode of 161 seconds produced 388 words, 35 timestamped transcript segments, and four chapters in the local development environment. This result demonstrates end-to-end functionality, not a formal accuracy benchmark. The project is intended as a local academic prototype; speaker diarisation, automatic noise reduction, authentication, durable distributed jobs, and production hosting remain future work.")
para(abstract)
abstract_words=len(abstract.split())
p=doc.add_paragraph(); r=p.add_run(f"Abstract length: {abstract_words} words."); r.italic=True; r.font.size=Pt(9); r.font.color.rgb=RGBColor.from_string(MUTED)
doc.add_heading("Keywords",level=2)
para("Podcast analysis; speech recognition; automatic transcription; chapter segmentation; audio processing; web application; Whisper; FastAPI.")
doc.add_heading("Project particulars",level=2)
add_table(["Item","Details"],[
["Project title","Podcast Summarisation and Chapter Generator"],
["Project group","17"],
["Project guide","Prof. G. S. Vyas"],
["Panel members","Prof. M. K. Jadhav; Prof. P. D. Sathya"],
["Institution","Maharaj Shikshan Sanstha's Chh. Shahu College of Engineering, Aurangabad"],
["Academic year","2025-26"],
],[1.7,4.5],9)
doc.add_page_break()
doc.add_heading("Acknowledgement",level=1)
para("The project group expresses its gratitude to Prof. G. S. Vyas for guidance throughout the planning, implementation, and review of the Podcast Summarisation and Chapter Generator. The group also thanks panel members Prof. M. K. Jadhav and Prof. P. D. Sathya for their review and feedback. The team acknowledges Maharaj Shikshan Sanstha's Chh. Shahu College of Engineering for providing the academic setting in which the project was developed. Finally, the team recognizes the maintainers of the open-source frameworks and libraries used in the application, including React, FastAPI, SQLAlchemy, OpenAI Whisper, FFmpeg, and Mutagen.")
para("The report describes the implemented local prototype and distinguishes current capabilities from proposed production improvements.")
doc.add_page_break()
doc.add_heading("Table of Contents",level=1)
TOC_ITEMS=[
("Abstract","TOC_ABSTRACT"),("Acknowledgement","TOC_ACK"),
("1. Introduction","TOC_01"),("2. Background and System Analysis","TOC_02"),
("3. Feasibility and Requirements","TOC_03"),("4. System Architecture and Design","TOC_04"),
("5. Process Models and Use Cases","TOC_05"),("6. Database Design","TOC_06"),
("7. User Interface Design","TOC_07"),("8. Implementation Details","TOC_08"),
("9. Testing and Verification","TOC_09"),("10. Deployment and Operations","TOC_10"),
("11. Results and Discussion","TOC_11"),("12. Conclusion and Future Scope","TOC_12"),
("References","TOC_REF"),("Appendix A. User Guide","TOC_A"),("Appendix B. API Reference","TOC_B"),
("Appendix C. Data Dictionary","TOC_C"),("Appendix D. Test Evidence and Glossary","TOC_D")
]
for label,mark in TOC_ITEMS:
    p=doc.add_paragraph()
    p.paragraph_format.space_after=Pt(5)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.2))
    r=p.add_run(label); r.font.size=Pt(10); r.font.color.rgb=RGBColor.from_string(NAVY if label[:1].isdigit() else INK)
doc.add_page_break()
doc.add_heading("List of Figures and Tables",level=1)
doc.add_heading("Figures",level=2)
for x in [
"Figure 4.1 System context diagram (Level 0)",
"Figure 4.2 High-level system architecture",
"Figure 5.1 Data Flow Diagram (Level 1)",
"Figure 5.2 Listener use-case diagram",
"Figure 5.3 Episode analysis sequence diagram",
"Figure 6.1 Entity Relationship Diagram",
"Figure 7.1 Dashboard interface wireframe",
"Figure 7.2 Episode analysis interface wireframe",
"Figure 10.1 Local deployment diagram",
]: bullet(x)
doc.add_heading("Tables",level=2)
for x in [
"Table 2.1 Existing approach and proposed application",
"Table 3.1 Functional requirements",
"Table 3.2 Non-functional requirements",
"Table 3.3 Hardware and software requirements",
"Table 3.4 Feasibility summary",
"Table 4.1 Application modules",
"Table 6.1 Database entities and relationships",
"Table 8.1 Technology stack",
"Table 8.2 API endpoint summary",
"Table 9.1 Test plan",
"Table 9.2 Sample test cases",
"Table 11.1 Demonstration run results",
"Table C.1 Database data dictionary",
]: bullet(x)
doc.add_page_break()
doc.add_heading("Abbreviations",level=1)
add_table(["Term","Meaning"],[
["AI","Artificial Intelligence"],
["API","Application Programming Interface"],
["ASR","Automatic Speech Recognition"],
["CRUD","Create, Read, Update, Delete"],
["DFD","Data Flow Diagram"],
["ERD","Entity Relationship Diagram"],
["HTTP","Hypertext Transfer Protocol"],
["ID3","Metadata format commonly used in MP3 audio files"],
["JSON","JavaScript Object Notation"],
["ORM","Object Relational Mapper"],
["REST","Representational State Transfer"],
["UI / UX","User Interface / User Experience"],
["UUID","Universally Unique Identifier"],
["VAD","Voice Activity Detection"],
], [1.2,5.0],9)

# ---------- Chapters ----------
chapter("1. Introduction",[
("h","1.1 Background"),
("p","Podcasts, interviews, lectures, and recorded discussions are efficient ways to distribute information. Their length can make targeted review difficult: a listener may remember a topic but not its time, or may need to revisit a whole episode to confirm a statement. Reading an unstructured transcript is also a poor substitute for navigable playback when a listener wants to move directly to a relevant passage."),
("p","The project addresses this review problem with an application that connects a transcript to the original recording. Audio is uploaded through a browser. A backend service validates the file, runs speech recognition, groups the resulting timed segments into sections, creates short chapter highlights, and stores the outputs. A listener can then scan the episode brief, open chapter moments, search the transcript when exact wording matters, and save a chosen representation."),
("h","1.2 Problem statement"),
("p","Listeners lack a simple workflow for transforming a long spoken recording into an organized, timestamped review guide. Manual note taking is slow and inconsistent. A raw transcript is searchable but often long and hard to navigate. A summary without timestamps is difficult to verify against the source audio. The project therefore aims to combine concise notes with direct navigation to the corresponding point in the recording."),
("h","1.3 Project objectives"),
("b",[
"Accept common audio formats through a browser-based upload flow and reject unsupported or empty files with clear errors.",
"Transcribe speech into ordered text segments with start and end times.",
"Group transcript segments into chapter-like sections and generate brief highlights.",
"Provide in-browser playback, chapter seeking, and transcript search linked to playback.",
"Allow a user to edit and copy chapter notes and download selected output formats.",
"Keep processing asynchronous so the web API can report job status while audio analysis runs.",
"Document the implementation, tests, operating assumptions, and limitations accurately."
]),
("h","1.4 Scope"),
("p","The implemented prototype supports MP3, WAV, M4A, OGG, and FLAC uploads up to a configured limit of 500 MB. It uses local storage, a local SQLite database, a React web interface, and an asynchronous in-process worker. Its outputs include a full timestamped transcript, chapter summaries, structured analysis data, and a tagged MP3 with ID3 chapter metadata. The default fast configuration uses Whisper Tiny on CPU, lightweight time-based grouping, and extractive highlights."),
("p","The current scope does not include user accounts, multi-tenant access control, a cloud-hosted production deployment, real-time streaming transcription, automatic speaker diarisation, guaranteed noise suppression, translation workflows, or model training. The system does not claim that automatically generated summaries are error-free or that its fast section labels represent validated semantic topics."),
("h","1.5 Importance and use cases"),
("b",[
"Students can locate lecture topics and revisit the audio instead of replaying the entire recording.",
"Researchers can search a discussion and use timestamps to return to a passage for verification.",
"Podcast listeners can preview chapter highlights and navigate to topics of interest.",
"Creators can produce a chapter guide and share an outline or chapter-tagged audio file.",
"Teams can review recorded discussions and preserve key moments in a portable summary."
]),
("h","1.6 Report organization"),
("p","Chapter 2 analyses the problem domain and proposed system. Chapter 3 records feasibility and requirements. Chapters 4 to 7 document architecture, process models, database design, and interface design. Chapter 8 describes the implementation. Chapters 9 to 11 report verification, operation, and observed results. Chapter 12 concludes with limitations and future scope. Appendices provide a user guide, API reference, data dictionary, test notes, and glossary.")
])

chapter("2. Background and System Analysis",[
("h","2.1 Current ways of reviewing long audio"),
("p","A listener can replay the audio manually, create notes while listening, or use a transcript generated by a separate tool. Manual review preserves context but requires repeated listening. Notes can be concise but may omit timestamps or exact wording. A transcript enables text search but may contain recognition errors and can still be difficult to scan when presented as one long document. A summary without chapter timestamps offers an overview but does not support precise verification."),
("p","These approaches identify a useful product requirement: the review interface should connect the text, section summaries, and original audio. Search and summaries should reduce navigation effort, while playback and timestamps should let the user verify important statements."),
("h","2.2 Existing approach and proposed application"),
("table",["Dimension","Common manual or transcript-only workflow","Podly project approach"],[
["Finding a topic","Replay or scan a long recording","Open a chapter and jump to its start time"],
["Recall","Keep separate notes, if created","Read a concise episode brief and chapter highlights"],
["Exact wording","Locate it manually in the audio","Search timestamped transcript segments"],
["Verification","Replay from an estimated point","Seek from a chapter or transcript timestamp"],
["Portability","Share separate audio and notes","Export a Markdown brief, transcript, JSON, or tagged MP3"],
["Limitations","Time-consuming; notes can omit timing","ASR and fast section labels can be imperfect and need review"],
],[1.15,2.55,2.55],8.2),
("h","2.3 Proposed system overview"),
("p","The proposed system consists of a browser client and a FastAPI backend. The client sends an audio file to the upload endpoint and receives episode and job identifiers. The backend stores the file under a generated identifier, creates database records, and submits analysis to a background thread pool. The browser periodically reads the job status. When processing finishes, the client requests episode metadata and chapters; it fetches the transcript only when the transcript view is selected."),
("p","The analysis pipeline inspects audio metadata, transcribes the original audio with Whisper, groups timed segments, creates chapter titles and highlights, persists records, and generates export files. The audio player streams the original upload, so the transcript and chapters remain connected to the source recording."),
("h","2.4 Design rationale"),
("b",[
"Use a pretrained speech-recognition model rather than train a new model: a labelled audio corpus and training compute are outside the scope of this academic application.",
"Use asynchronous processing: speech recognition can take longer than a normal web request, so a job status record lets the client remain responsive.",
"Use timestamps as first-class data: summaries are more trustworthy and useful when they can be checked against the original audio.",
"Keep the transcript available as a reference, but make the brief and chapter navigation the main review path.",
"Use a fast local default: Tiny model weights and extractive summaries reduce setup requirements on a CPU-only machine."
]),
("h","2.5 Strengths and limitations of the proposed system"),
("p","The implemented system provides an end-to-end workflow from upload to chapter playback and export. It is modular enough to replace local storage, SQLite, or the in-process queue in a later deployment. Its main limitations are inherited from the selected model and fast pipeline: recognition quality depends on the recording; time-based sections are not equivalent to topic clustering; extractive highlights do not guarantee a complete summary; and the worker queue is not durable across a backend restart.")
])

chapter("3. Feasibility and Requirements",[
("h","3.1 Technical feasibility"),
("p","The project uses established Python and JavaScript libraries available in the supplied development environment. React and TypeScript support interactive client pages; Vite bundles the frontend; FastAPI supplies typed HTTP endpoints; SQLAlchemy maps application records to SQLite; Whisper performs speech recognition; bundled FFmpeg decodes audio; and Mutagen writes MP3 chapter metadata. The selected stack can run locally without a cloud account. Initial setup requires Python and Node.js dependencies and model weights."),
("h","3.2 Operational feasibility"),
("p","A user interacts through a browser: upload one file, wait for the job status, review the brief, jump into chapters, optionally search the transcript, and export. No specialist audio-editing software is required. The primary operational cost is waiting for transcription, which depends on audio duration, processor, and model. A local operator must keep the backend and frontend services running and retain sufficient disk space for uploads, outputs, and cached model weights."),
("h","3.3 Financial feasibility"),
("p","The prototype is built from open-source tools and local compute, so it does not require per-minute hosted transcription fees or a paid cloud service during local development. This does not mean the application has zero operating cost: a production service would incur storage, compute, backup, monitoring, network, and maintenance costs. Larger Whisper models or concurrent processing require more memory and compute."),
("h","3.4 Functional requirements"),
("table",["ID","Requirement","Priority","Verification"],[
["FR-01","Accept MP3, WAV, M4A, OGG, and FLAC files; reject unsupported extensions.","Must","Upload validation"],
["FR-02","Enforce the configured maximum upload size and stream accepted data to disk.","Must","Upload boundary cases"],
["FR-03","Create an episode record and an asynchronous processing job.","Must","Upload response and job query"],
["FR-04","Inspect the audio stream and reject missing, empty, corrupt, or too-short audio.","Must","Audio validation"],
["FR-05","Transcribe supported speech to timed segments.","Must","Transcript endpoint and playback"],
["FR-06","Group segments into chapter candidates and generate brief summaries.","Must","Chapters endpoint"],
["FR-07","Display an episode brief, chapter list, audio player, transcript, and export options.","Must","Browser review"],
["FR-08","Seek to chapter starts and transcript segment timestamps.","Must","Playback interaction"],
["FR-09","Search transcript text and render matching lines in manageable batches.","Should","Transcript interaction"],
["FR-10","Edit chapter title/summary and copy chapter notes.","Should","PATCH endpoint and UI"],
["FR-11","Export Markdown, timestamped TXT, JSON, and tagged MP3 when generated.","Should","Download endpoints"],
["FR-12","Retry a failed episode when the original audio exists and there are no partial results.","Should","Retry endpoint"],
["FR-13","Show a health response and job status for operational checks.","Should","Health and job endpoints"],
],[.65,3.15,.75,1.7],8),
("h","3.5 Non-functional requirements"),
("table",["ID","Quality attribute","Requirement / measurable target"],[
["NFR-01","Usability","Core result navigation must expose brief, chapters, transcript, and export as direct tabs."],
["NFR-02","Responsiveness","The API should acknowledge an upload without waiting for full transcription."],
["NFR-03","Memory","The upload endpoint streams files in bounded chunks instead of reading a 500 MB file into one process buffer."],
["NFR-04","Reliability","A failed job exposes a readable error and may be retried if partial rows are absent."],
["NFR-05","Maintainability","Frontend pages, API routes, processing services, and exports are separate modules."],
["NFR-06","Portability","Configuration supports local paths and a configurable database URL; SQLite remains the default."],
["NFR-07","Security","Use generated storage names, extension allowlisting, size checks, and safe display filenames; no authentication is currently implemented."],
["NFR-08","Scalability","Library responses are paginated, episode detail omits the transcript payload, and transcript rows are loaded on demand."],
["NFR-09","Transparency","Fast keyword/time grouping and summaries are described as approximate; no transcript accuracy score is claimed."],
],[.75,1.25,4.25],8.6),
("h","3.6 Hardware and software requirements"),
("table",["Category","Minimum for local demonstration","Recommended for longer audio"],[
["Processor","Modern multi-core CPU","Recent multi-core CPU; GPU optional"],
["Memory","4 GB RAM may run the small model but leaves little headroom","8 GB or more for smoother analysis and multiple services"],
["Storage","Several GB free for Python packages, model weights, uploads, and outputs","SSD and additional capacity for long recordings"],
["Operating system","Windows, macOS, or Linux with compatible Python and Node.js","64-bit operating system"],
["Runtime","Python 3.11+; Node.js 18+ per project README","Use project-pinned dependencies"],
["Browser","Current Chromium, Firefox, Safari, or Edge","Current browser with audio playback support"],
["Network","Needed for initial package/model setup if dependencies are not cached","Local processing can run offline after dependencies and model weights are cached"],
],[1.0,2.6,2.65],8.3),
("h","3.7 Feasibility summary"),
("table",["Feasibility area","Assessment","Reason"],[
["Technical","Feasible for a prototype","Implemented with local libraries and pretrained models."],
["Operational","Feasible for individual or classroom use","Browser flow is straightforward; local services must remain running."],
["Financial","Low-cost for a local demonstration","No mandatory hosted inference API; compute and storage remain costs."],
["Production","Requires additional engineering","Durable jobs, authentication, backups, shared storage, monitoring, and load testing are not included."],
],[1.1,1.55,3.6],8.5),
])

chapter("4. System Architecture and Design",[
("h","4.1 Architecture style"),
("p","The system uses a client-server architecture with a modular backend. The React client makes HTTP requests to FastAPI routes. The route layer handles upload, listing, detail, transcript, chapter editing, audio streaming, exports, and job status. A processing worker performs CPU-intensive analysis outside the request handler. SQLAlchemy provides a persistence boundary for SQLite. Audio and generated artifacts are stored on the local file system."),
("fig",ASSETS/"fig01_context.png","Figure 4.1. Context diagram showing the listener, Podly application, storage, and media/AI tools.",6.45),
("fig",ASSETS/"fig02_architecture.png","Figure 4.2. High-level architecture of the current local application.",6.45),
("h","4.2 Component responsibilities"),
("table",["Component","Responsibility","Primary implementation"],[
["Browser application","Upload flow, progress polling, library, playback, chapter and transcript views, downloads","React + TypeScript pages and components"],
["API service","Validate requests, persist episode/job records, serve results and files","FastAPI routers under /api"],
["Processing worker","Run audio inspection, transcription, grouping, summary, persistence, and export steps","ThreadPoolExecutor and processing pipeline"],
["Speech recognition","Return language, transcript text, and timestamped segments","OpenAI Whisper Tiny by default"],
["Audio tools","Read metadata, decode source formats, produce tagged MP3","Mutagen and bundled imageio-ffmpeg binary"],
["Database","Store metadata, jobs, segments, and chapters","SQLAlchemy with SQLite default"],
["File system","Store original uploads, exports, and model cache","backend/uploads, backend/outputs, backend/models"],
],[1.2,3.1,1.95],8.3),
("h","4.3 Request and response pattern"),
("p","Upload uses multipart form data. The API returns job_id and podcast_id; the client uses the job identifier to request progress. The job response includes stage, progress, message, and error. Once complete, episode details and chapters are loaded, while the transcript is fetched only if the user selects the Transcript tab. The audio endpoint returns the original file with a media type derived from its filename. Export endpoints return downloadable files."),
("h","4.4 Processing state model"),
("p","A job progresses through queued, preprocessing, transcribing, detecting_topics, generating_summaries, writing_metadata, and completed states. An exception records failed state with a readable message. Progress values are approximate stage indicators rather than a guaranteed linear measure of remaining time. In-process execution means queued jobs can be lost when the backend process exits; production deployment requires a durable queue."),
("h","4.5 Error handling"),
("b",[
"Unsupported extension and empty content are rejected at upload time.",
"Audio metadata validation catches files without readable audio streams and recordings shorter than one second.",
"Whisper and FFmpeg errors are converted into processing failures visible through the job and episode.",
"Missing episode, transcript, chapter, or export resources return not-found responses.",
"Failed jobs are retryable when their audio file exists and the first run produced no transcript or chapter rows.",
"Tagged MP3 generation is treated as non-critical; a failure there does not invalidate the core analysis."
]),
])

chapter("5. Process Models and Use Cases",[
("h","5.1 Level 1 Data Flow Diagram"),
("p","The process begins when a user selects an audio file. The upload handler checks the extension, streams the body to a generated path, and stores episode and job records. The worker reads metadata, transcribes the audio, groups segments, generates chapter highlights, persists the analysis, and builds exports. The browser reads status and presents the results."),
("fig",ASSETS/"fig03_dataflow.png","Figure 5.1. Level 1 DFD. D1 is the relational database; D2 is local file storage.",6.45),
("h","5.2 Listener use cases"),
("fig",ASSETS/"fig04_usecase.png","Figure 5.2. Use-case diagram for the implemented listener workflow.",6.45),
("table",["Use case","Precondition","Main outcome"],[
["Upload and analyze","Browser can reach API; file has an allowed extension and is within limit.","Episode and job are created; the job runs asynchronously."],
["Monitor processing","Upload response contains a job identifier.","The UI shows the latest processing stage and handles polling errors."],
["Review chapter","Episode analysis completed and chapters exist.","Player seeks to the chapter start; summary is visible."],
["Search transcript","Transcript exists and user opens Transcript.","Timed lines load, search filters text, and visible results can be expanded in batches."],
["Edit a chapter","Chapter belongs to the episode.","Updated title or summary is persisted through PATCH."],
["Export content","Episode processing is complete and requested export exists.","A file download is returned."],
],[1.4,2.2,2.65],8.5),
("h","5.3 Episode analysis sequence"),
("fig",ASSETS/"fig05_sequence.png","Figure 5.3. Sequence of upload, asynchronous processing, polling, and result retrieval.",6.45),
("h","5.4 Processing algorithm"),
("n",[
"Receive the file and verify its extension and size.",
"Stream the file to a UUID-based local path and create an episode record and queued job.",
"Inspect audio metadata and reject missing, unreadable, or too-short audio.",
"Load the configured Whisper model and transcribe the original audio into timed segments.",
"Assign lightweight section labels in fast mode, or use the optional BERTopic path when deep processing is configured.",
"Group consecutive segments into chapter candidates and merge short sections.",
"Generate a title and extractive highlight for each chapter in fast mode.",
"Persist transcript segments and chapters; generate TXT, Markdown, JSON, and optional tagged MP3 files.",
"Mark the job and episode complete; return status and allow the client to fetch the result views."
]),
("h","5.5 Failure and retry flow"),
("p","Validation failures stop before model inference. Runtime failures set the job to failed and the episode error message is displayed. The worker clears partial segment and chapter rows when a processing attempt fails, allowing a new retry to begin from the original audio. The retry API checks that the source file still exists. A job queue that survives process restarts is not implemented in this local version."),
])

chapter("6. Database Design",[
("h","6.1 Entity relationship overview"),
("fig",ASSETS/"fig06_erd.png","Figure 6.1. ERD for episodes, jobs, transcript segments, and chapters.",6.45),
("h","6.2 Relationships"),
("table",["Relationship","Cardinality","Description"],[
["Podcast to ProcessingJob","One-to-one in application","Podcast.job_id is unique; ProcessingJob.podcast_id refers to the owning episode."],
["Podcast to TranscriptSegment","One-to-many","An episode may contain many ordered timestamped segments."],
["Podcast to Chapter","One-to-many","An episode may contain several chapter records with titles and summaries."],
["Chapter to transcript references","Many segment IDs stored as JSON text","segment_ids records the source segment identifiers for a chapter."],
["File artifacts to Podcast","One-to-many by directory convention","Original audio and generated exports are stored under UUID-based paths; artifact files are not binary database columns."],
],[1.8,1.45,3.0],8.5),
("h","6.3 Data integrity and indexing"),
("p","UUID strings identify episodes, jobs, transcript rows, and chapters. Timestamps use floating-point seconds from the start of the recording. Foreign keys connect jobs, segments, and chapters to their episode. SQLite connections enable foreign-key checks and use a busy timeout for the threaded worker workload. Composite indexes support episode-plus-segment ordering and episode-plus-chapter ordering. Episode status/creation time and job stage/update time also have composite indexes."),
("p","The current database is SQLite to keep setup local and simple. SQLite is suitable for the academic single-host prototype. Multi-instance production operation should use a server database such as PostgreSQL and explicit schema migrations rather than relying on create_all."),
("h","6.4 Entity summary"),
("table",["Entity","Important attributes","Purpose"],[
["Podcast","id, job_id, title, original_filename, file_path, file_size_bytes, duration_seconds, format, sample rate, channels, word_count, topic_count, status, created_at, completed_at","Episode-level metadata, source location, state, and summary counts."],
["ProcessingJob","id, podcast_id, stage, progress, message, error, created_at, updated_at","Tracks processing progress and failure details."],
["TranscriptSegment","id, podcast_id, segment_index, start_time, end_time, text, topic_id, topic_label, confidence","Stores ordered and searchable ASR output."],
["Chapter","id, podcast_id, chapter_number, title, start_time, end_time, topic_id, topic_label, topic_keywords, summary, segment_ids, is_edited","Stores navigation points and editable chapter notes."],
],[1.25,3.2,1.8],8.1),
("h","6.5 Persistence decisions"),
("p","The application stores uploaded audio and exports on disk while keeping searchable metadata and transcript text in SQLite. This simplifies MP3 tagging and media streaming. It also means file backups must be coordinated with database backups. If a database record survives but its file is removed, audio streaming reports a missing-file response. A production design should use managed object storage, a relational database, retention rules, and integrity checks.")
])

chapter("7. User Interface Design",[
("h","7.1 Interaction principles"),
("p","The current interface puts the episode brief and chapter navigation ahead of long-form text. The same four top-level tabs are always available: Brief, Chapters, Transcript, and Export. The transcript is loaded on demand and rendered in batches, so opening an episode does not require loading all transcript lines. A persistent player exposes play/pause, seeking, chapter markers, volume, and playback speed."),
("p","The dashboard and library provide a starting point for new uploads, recent episodes, status labels, and search. The upload page explains the expected processing stages. The processing view polls job status and retries polling with backoff when the connection is interrupted. The episode view uses chapter buttons to move to relevant moments in the original audio."),
("fig",ASSETS/"fig07_dashboard_wireframe.png","Figure 7.1. Dashboard wireframe based on the current application layout; the diagram is illustrative.",6.45),
("fig",ASSETS/"fig08_analysis_wireframe.png","Figure 7.2. Episode analysis wireframe showing the brief, player, and four direct tabs; illustrative layout.",6.45),
("h","7.2 Main screens"),
("table",["Screen","Primary content","User action"],[
["Dashboard","Welcome panel, analysis statistics, recent episodes","Start an upload or open the library."],
["Upload","Audio drop zone, accepted formats, processing explanation","Select a file and follow transfer progress."],
["Library","Searchable episode list, status filters, paginated results","Open an episode and inspect its state."],
["Episode brief","Key chapter highlights, duration, chapter count, player","Scan key ideas and choose Explore chapters."],
["Chapters","Chapter titles, timestamps, summaries, edit and copy controls","Play a chapter, update its notes, or copy the summary."],
["Transcript","Search field and timestamped transcript segments","Search exact wording and seek to a matching segment."],
["Export","Brief and chapter-tagged audio as primary downloads; TXT and JSON under more formats","Download a selected artifact."],
],[1.25,3.0,2.0],8.2),
("h","7.3 Accessibility and responsive behavior"),
("p","Controls use semantic buttons and visible text labels. The library and analysis panels use responsive grids and flexible widths. Transcript rows expose timestamp buttons for keyboard-accessible seeking. Low-coverage transcripts display an explanatory warning based on words per minute; it is a heuristic and may reflect silence, music, quiet speech, or noise. The interface does not measure signal-to-noise ratio and does not perform automatic denoising."),
("h","7.4 Interface evaluation"),
("p","A generated demonstration episode was opened in the browser to check that the brief, player, four chapter buttons, tabs, and export view are rendered. During the project, the navigation was simplified from a clipped dropdown to a balanced single row of four direct tabs. These checks are functional inspection of the local prototype, not a formal usability study with recruited participants.")
])

chapter("8. Implementation Details",[
("h","8.1 Technology stack"),
("table",["Layer","Technology","Use in this project"],[
["Frontend","React 19, TypeScript","Reusable pages, stateful player, upload flow, tabs, search, and routing."],
["Frontend build and styles","Vite 8, Tailwind CSS 4","Development server, production bundling, utility styling."],
["Frontend networking","Axios","JSON requests, multipart upload progress, file downloads."],
["Backend","Python 3.11+, FastAPI 0.115","REST endpoints, schema validation, OpenAPI docs, application lifespan."],
["Validation","Pydantic 2","Request/response schema and typed settings."],
["Persistence","SQLAlchemy 2, SQLite","ORM models, sessions, indexes, local database."],
["Speech recognition","OpenAI Whisper, default model Tiny","Transcription and timestamped segment output."],
["Audio handling","Mutagen, imageio-ffmpeg / FFmpeg","Metadata inspection, decode support, MP3 conversion and ID3 chapters."],
["Analysis","scikit-learn stop words and local grouping; optional BERTopic / DistilBART","Fast section labels and highlights; deeper optional path."],
],[1.45,2.0,2.8],8.0),
("h","8.2 Audio upload and validation"),
("p","The upload endpoint allowlists .mp3, .wav, .m4a, .ogg, and .flac. It streams the multipart upload to a UUID-named file in 1 MiB chunks, counts bytes as the file is written, and removes the partial file if the configured maximum is exceeded. The display filename is reduced to a basename and stripped of control characters. The system does not use a client-supplied name to construct the storage path."),
("p","Mutagen reads available stream metadata. The validation layer rejects empty files, missing audio streams, unreadable media, and audio shorter than one second. Whisper decodes the original audio through its bundled FFmpeg path. This avoids creating a full-size temporary WAV before transcription."),
("h","8.3 Transcription"),
("p","The default configuration selects the Tiny Whisper model on CPU. The model is loaded once and cached in memory; a lock prevents two jobs from loading the same model simultaneously. Decoding uses fp16 disabled for CPU compatibility, no word-level timestamps, beam size one, best-of one, and previous-text conditioning disabled to reduce processing work. Whisper returns segment start/end values, text, and detected language. This design provides segment timestamps, not word-level alignment."),
("h","8.4 Topic grouping and chapter generation"),
("p","Fast mode divides segments into a small number of time-based groups and extracts salient non-stopword terms to make provisional labels. Consecutive segments are merged into chapter candidates; sections shorter than the configured minimum may merge with a preceding section. Fast grouping is lightweight and deterministic, but it does not prove that a semantic topic change occurred at every boundary. When fast mode is disabled, the code attempts BERTopic clustering and falls back to time groups if the deeper model fails."),
("h","8.5 Summary generation"),
("p","Fast mode chooses a small number of relatively informative sentences from each chapter or falls back to an excerpt. It avoids a separate summarizer model download. With fast processing disabled, the code can use DistilBART and chunk longer text before summarization. The extractive default is quick, but it may select a sentence that lacks context and it is not a claim that every key point has been captured."),
("h","8.6 MP3 chapter metadata"),
("p","The export pipeline copies MP3 input or converts other accepted formats to MP3, then writes standard ID3 tags and CHAP/CTOC chapter frames. Chapter start and end times are converted to milliseconds. Each chapter frame includes a title and a short summary subframe. Mutagen reads and writes the chapter metadata."),
("h","8.7 Job execution"),
("p","A configurable ThreadPoolExecutor runs processing work in the API process. PROCESSING_WORKERS defaults to 1 and accepts values from 1 to 8, but increasing it should be based on available memory and compute. The job state is persisted in SQLite and exposed through polling. The executor's waiting queue is in process and is not durable after a restart."),
("h","8.8 Core pipeline pseudocode"),
("code","upload(file):\n  validate extension\n  stream chunks to generated local path; enforce byte limit\n  create podcast record and queued processing job\n  submit job to local worker pool\n\nprocess(job):\n  inspect audio metadata\n  transcribe source audio with Whisper\n  group transcript segments into chapters\n  create chapter highlights\n  persist segments and chapters\n  write transcript, Markdown, JSON, and optional tagged MP3\n  mark job and episode complete"),
("h","8.9 API endpoints"),
("table",["Method and path","Purpose","Result"],[
["POST /api/podcasts/upload","Upload audio and submit analysis job","job_id, podcast_id, message"],
["GET /api/podcasts?limit=50&offset=0","List newest episodes as a bounded page","Podcast list item array"],
["GET /api/podcasts/stats","Return aggregate dashboard statistics","Counts, duration, chapters, words"],
["GET /api/podcasts/{id}","Read episode metadata without nested transcript","Podcast detail"],
["GET /api/jobs/{job_id}","Read job stage, progress, and message","Job status"],
["POST /api/podcasts/{id}/retry","Retry eligible failed analysis","Updated job status"],
["GET /api/podcasts/{id}/chapters","Read chapters in order","Chapter array"],
["PATCH /api/podcasts/{id}/chapters/{chapter_id}","Edit title or summary","Updated chapter"],
["GET /api/podcasts/{id}/transcript","Load timestamped transcript","Transcript segment array"],
["GET /api/podcasts/{id}/audio","Stream source audio","Audio response"],
["GET /api/podcasts/{id}/download/{format}","Download txt, md, json, or mp3","File response"],
["GET /api/health","Service health check","Service status"],
],[2.8,2.0,1.45],7.5),
])

chapter("9. Testing and Verification",[
("h","9.1 Testing approach"),
("p","Testing combines automated service-level tests, static frontend checks, and direct functional inspection. Audio processing includes native model and media dependencies, so a clean validation should separate deterministic service tests from long-running model inference. Tests in this report were run against temporary databases and directories rather than the project's saved episode data."),
("table",["Test level","Focus","Evidence collected"],[
["Frontend build","TypeScript compilation and production bundling","npm run build completed successfully."],
["Frontend lint","Static checks for frontend source","npm run lint completed without warnings."],
["Backend service tests","Module imports, time formatting, and text chunking helpers","8 selected tests passed."],
["Backend compilation","Python syntax and import compilation","python -m compileall -q app completed."],
["Direct route logic smoke check","Health response, paged list, stats aggregation, detail payload, and DB index","All checked conditions passed."],
["Browser functional inspection","Sample brief, player, chapters, four tabs, and export panel","Sample episode was inspected in the local browser."],
["Full FastAPI TestClient suite","HTTP integration tests","Could not complete in the restricted execution sandbox; TestClient blocked while creating its local socket pair."],
],[1.35,2.75,2.15],8.1),
("h","9.2 Sample test cases"),
("table",["ID","Input / action","Expected result","Observed result"],[
["TC-01","Upload a non-audio extension such as PDF.","HTTP 400; file is rejected before processing.","Automated test covers this case."],
["TC-02","Upload a zero-byte MP3.","HTTP 400; empty file is rejected.","Automated test covers this case."],
["TC-03","Upload supported audio below configured size.","Audio is saved under generated identifier; job is returned.","Sample upload and processing completed in the local demo."],
["TC-04","Request a non-existent job ID.","HTTP 404 with job-not-found detail.","Route logic returns not found; full HTTP harness was restricted."],
["TC-05","Request dashboard statistics for a populated test DB.","Aggregated counts and totals are returned.","Direct smoke check returned expected count and word total."],
["TC-06","Request episode details with transcript available.","Detail includes metadata; transcript remains on its own endpoint.","Schema smoke check confirmed chapters and segments are omitted."],
["TC-07","Inspect the segment index after schema setup.","Composite podcast/segment index exists.","SQLite index smoke check passed."],
["TC-08","Use the sample 161-second spoken episode.","Produce transcript segments, chapters, and exports.","Observed 388 words, 35 segments, and 4 chapters."],
["TC-09","Open the browser results page.","Brief, chapter controls, player, and four direct tabs render.","Observed in local browser for the demo episode."],
["TC-10","Use speech with background noise.","Warn or improve transcript quality appropriately.","Not validated; automatic denoising and acoustic quality analysis are not implemented."],
],[.55,1.85,2.15,1.75],7.25),
("h","9.3 Test boundaries and interpretation"),
("p","The 161-second generated demo establishes that the local pipeline can complete a short, clear-speech example. It is not a representative benchmark for accents, multiple speakers, music, noise, long recordings, or different languages. No Word Error Rate, chapter-boundary F1, summary faithfulness score, or user-satisfaction study has been measured. Such metrics require a labelled evaluation set and a defined annotation protocol."),
("p","Eight deterministic backend tests were selected and passed. The full API TestClient suite could not be completed in the current sandbox because the test harness stalled while creating a local Windows socket pair. Direct route-function checks and browser inspection were used as alternate evidence; these are not equivalent to a full HTTP integration run."),
("h","9.4 Acceptance criteria"),
("b",[
"An accepted audio file creates an episode and a processing job.",
"Job progress can be read without waiting for transcription to finish.",
"A completed episode has a brief, chapters, timed transcript, and playback source.",
"Chapter and transcript timestamps can seek the audio player.",
"Export files are available only after processing has completed.",
"Failures are readable and retryable when the original file exists and no partial results remain."
])
])

chapter("10. Deployment and Operations",[
("h","10.1 Current local deployment"),
("p","The project is configured for local development. The Vite development server serves the frontend at http://localhost:5173. Uvicorn serves the FastAPI backend at http://127.0.0.1:8000, with interactive API documentation at /api/docs. The frontend sends requests to /api and uses the Vite proxy configuration. SQLite, uploads, generated outputs, and model weights are stored under the backend project directory by default."),
("fig",ASSETS/"fig09_deployment.png","Figure 10.1. Local development deployment of the web client, API, database, worker, and storage.",6.45),
("h","10.2 Setup and launch"),
("n",[
"Install Python 3.11 or newer and Node.js 18 or newer.",
"Install backend dependencies from backend/requirements.txt in a Python virtual environment.",
"Install frontend packages from frontend/package.json using npm install.",
"Set environment options in backend/.env if needed. The root .env.example documents Whisper model, processing mode, upload limit, and worker count.",
"Start the backend with the supplied start_backend.ps1 script or the Uvicorn command in README.md.",
"Start the frontend with start_frontend.ps1 or npm run dev from frontend.",
"Open http://localhost:5173, upload supported audio, and wait for the processing job.",
"Use /api/health and /api/docs when checking the backend service."
]),
("h","10.3 Configuration"),
("table",["Setting","Default","Operational meaning"],[
["WHISPER_MODEL","tiny","Selects the speech-recognition model size."],
["WHISPER_DEVICE","cpu","Runs inference on CPU; CUDA can be configured where installed."],
["FAST_PROCESSING","true","Uses lightweight grouping and extractive highlights."],
["PROCESSING_WORKERS","1","Limits simultaneous local jobs; raise cautiously based on hardware."],
["MAX_UPLOAD_SIZE_MB","500","Maximum upload file size enforced by the API."],
["MIN_CHAPTER_DURATION_SECONDS","30","Merge threshold for short chapter candidates."],
["DATABASE_URL","SQLite file in backend","Database connection string."],
["UPLOAD_DIR / OUTPUT_DIR / MODEL_CACHE_DIR","backend local folders","Storage locations for inputs, exports, and model weights."],
],[1.8,1.65,2.75],8.2),
("h","10.4 Security and privacy considerations"),
("b",[
"Audio may contain personal, educational, or confidential information. The local prototype stores uploads and transcript data on disk without account isolation.",
"Do not expose the development server to a public network without authentication, authorization, rate limiting, HTTPS, and a clear data-retention policy.",
"The upload endpoint uses an allowlist, a size cap, UUID-based storage names, and chunked writes. These controls reduce accidental misuse but do not replace malware scanning or a hardened media sandbox.",
"Use generated filenames for storage and safe display names for labels. Avoid returning internal file paths in public API responses.",
"Backups should include both SQLite and media directories and should be protected because transcript text and audio may be sensitive.",
"Configure CORS to trusted origins and replace development defaults before production.",
"Run FFmpeg and transcription workers with least privilege and resource limits in hosted environments."
]),
("h","10.5 Production deployment path"),
("p","A production implementation should split the API and worker roles. The API can remain stateless behind a reverse proxy while a durable queue dispatches jobs to workers. PostgreSQL can replace SQLite; object storage can hold original audio and exports; a migration tool can version schema changes; and a monitoring system can track job age, failure rates, queue depth, storage, model memory, and request latency. Authentication, data retention, backups, and secure deletion need explicit product decisions."),
("p","The current ThreadPoolExecutor is an in-process local queue and is not durable. Deploying multiple API instances with independent thread pools can duplicate work or lose queued tasks on restart. The documented production direction is therefore architectural guidance, not a feature implemented in this project.")
])

chapter("11. Results and Discussion",[
("h","11.1 Demonstration run"),
("p","A generated 161-second speech episode was processed in the local development environment. The pipeline produced 388 recognized words, 35 timestamped transcript segments, and four chapters. The browser results page exposed an episode brief, four chapter jump controls, a working player display, transcript and export tabs, and available downloads. This is evidence of an end-to-end functional demonstration."),
("table",["Measurement","Observed value","Interpretation"],[
["Input duration","161.07 seconds","Approximately 2 minutes 41 seconds."],
["Recognized word count","388 words","Word count from the generated demonstration speech."],
["Transcript segmentation","35 segments","Each segment includes start/end timing and text."],
["Chapter count","4 chapters","Chapter grouping output for this sample."],
["Warm local processing time","Approximately 18 seconds after model setup","One machine-specific observation; not a performance guarantee or benchmark."],
["Available outputs","TXT, Markdown, JSON, tagged MP3","MP3 tagging is optional if metadata conversion succeeds."],
],[1.65,1.7,2.85],8.6),
("h","11.2 Discussion"),
("p","The demonstration supports the project objective of making a short spoken recording easier to navigate and review. Chapter timestamps connect the text overview back to audio. Lazy transcript loading and batched rendering reduce work on the initial episode page and improve handling of longer transcripts. Paginated library results and bounded upload chunks reduce avoidable memory and response costs."),
("p","The principal quality trade-off is speed versus semantic depth. The default fast mode avoids model downloads and additional CPU-heavy clustering, but its section labels are keyword hints over time groups. Extractive highlights may omit relationships across sections. Whisper Tiny may misrecognize names, technical terms, accents, overlapping voices, or speech obscured by background sound. A user should confirm important statements against the original audio."),
("h","11.3 Comparison to project objectives"),
("table",["Objective","Status","Evidence / limitation"],[
["Browser upload and asynchronous job","Implemented","Sample analysis generated and job flow inspected."],
["Timestamped speech transcription","Implemented","Demonstration returned 35 timed segments."],
["Chapter grouping and highlights","Implemented","Four chapters produced for demonstration audio."],
["Playback-linked navigation","Implemented","Chapter buttons and player controls present in inspected UI."],
["Transcript search and export","Implemented","Transcript view, search, and download options available; no formal usability study."],
["Quality analysis for noisy recordings","Partial / future","Only a low transcript-density hint exists; no SNR estimator or denoiser."],
["Production-scale processing","Future","Local thread pool and SQLite are single-host prototype choices."],
],[2.0,1.2,3.0],8.4),
("h","11.4 Threats to validity"),
("b",[
"One short, generated speech sample cannot represent varied podcast audio.",
"No labelled corpus was used to measure transcription error or chapter quality.",
"The reported processing time depends on the local machine, cached model state, and current system load.",
"The UI was inspected by the project team; formal user acceptance testing with participants was not performed.",
"Fast mode labels sections with a lightweight method, so the term topic should not be interpreted as expert-validated semantic classification."
])
])

chapter("12. Conclusion and Future Scope",[
("h","12.1 Conclusion"),
("p","The Podcast Summarisation and Chapter Generator provides a complete local web workflow for converting an audio recording into a timestamped transcript, concise chapter highlights, and downloadable assets. The application combines a responsive browser interface with FastAPI endpoints and an asynchronous processing pipeline. Its most useful contribution is the connection between short notes and the original audio: a listener can scan the episode, open a chapter, and return to the corresponding time without reading the full transcript first."),
("p","A short generated demonstration completed with four chapters and 35 timestamped segments. Frontend production build and lint checks passed, eight selected backend service tests passed, and direct route logic checks passed. The project is therefore a functional academic prototype. It is not yet a production service or a benchmarked transcription system."),
("h","12.2 Current limitations"),
("b",[
"Speech recognition and summaries can be inaccurate, especially with difficult audio, proper nouns, or multiple speakers.",
"Fast topic grouping is time-based and keyword-labelled rather than a validated semantic model.",
"There is no automatic denoising, calibrated confidence score, or speaker diarisation.",
"Processing runs inside one API process; queued work is not durable through a restart.",
"SQLite and local disk are not designed for horizontally scaled multi-instance hosting.",
"There is no authentication, user separation, role management, public share-link security, or retention controls.",
"No formal accuracy benchmark or user study has been completed."
]),
("h","12.3 Future work"),
("n",[
"Add an audio-quality preflight using measurable signals such as clipping, loudness, silence proportion, and voice activity. Present the result as a warning, not an accuracy guarantee.",
"Offer optional denoising on a temporary derivative while preserving the uploaded original; compare transcript quality before making enhancement the default.",
"Evaluate Whisper model choices on a consented, labelled audio set and report Word Error Rate by language and recording condition.",
"Replace time-only grouping with speech-aware segmentation and evaluate chapter boundaries using human annotations.",
"Add speaker diarisation and per-speaker transcript labels where the additional model and runtime cost are justified.",
"Improve summary quality with grounded extractive evidence and sentence-level timestamp references; measure factual consistency with human review.",
"Introduce search across transcripts and episodes after access control and indexing requirements are defined.",
"Move processing to a durable task queue and deploy workers separately from the API.",
"Adopt PostgreSQL, object storage, database migrations, monitoring, backups, and retention controls for production.",
"Conduct usability testing with students or podcast listeners and refine navigation, export choices, and progress communication."
]),
])

# References
doc.add_page_break()
doc.add_heading("References",level=1)
para("The following primary documentation and project references informed the implementation description. Framework versions in the project are recorded in the local package manifests; URLs below point to official documentation or the official project repository.")
refs=[
"[1] Project Group 17, Podcast Summarisation and Chapter Generator source tree, local project documentation and configuration, accessed 28 October 2026.",
"[2] React Team, React documentation: Quick Start. https://react.dev/learn (accessed 28 October 2026).",
"[3] FastAPI, Tutorial - User Guide. https://fastapi.tiangolo.com/tutorial/ (accessed 28 October 2026).",
"[4] OpenAI, Whisper speech recognition repository and README. https://github.com/openai/whisper (accessed 28 October 2026).",
"[5] SQLAlchemy, SQLAlchemy 2.0 ORM documentation. https://docs.sqlalchemy.org/en/20/orm/ (accessed 28 October 2026).",
"[6] Vite, Getting Started Guide. https://vite.dev/guide/ (accessed 28 October 2026).",
"[7] Pydantic, Validation documentation. https://pydantic.dev/docs/validation/latest/get-started/ (accessed 28 October 2026).",
"[8] FFmpeg Project, FFmpeg Documentation. https://www.ffmpeg.org/documentation.html (accessed 28 October 2026).",
"[9] Mutagen Documentation, ID3 frame API and chapter frame support. https://mutagen.readthedocs.io/en/latest/api/id3_frames.html (accessed 28 October 2026).",
"[10] Project Documentation Guidelines 2025-26, Web Based Application, supplied by the project group."
]
for x in refs: numbered(x)

chapter("Appendix A. User Guide",[
("h","A.1 Start the application"),
("n",[
"Open a terminal in the project folder and start the backend using start_backend.ps1. The first startup may import libraries and create local database tables.",
"Open a second terminal and start the frontend using start_frontend.ps1.",
"Open http://localhost:5173 in a current browser. Confirm the dashboard appears.",
"Use the upload action to choose an MP3, WAV, M4A, OGG, or FLAC file. The current configured size limit is 500 MB."
]),
("h","A.2 Review an episode"),
("n",[
"Wait while the job status progresses through audio inspection, transcription, grouping, summary generation, and export writing.",
"Open the completed episode. Read the short brief first to understand the main sections.",
"Select Chapters to see timestamps and short highlights. Use Play to seek to a chapter.",
"Select Transcript only when exact wording is needed. The application loads transcript segments on demand. Search for a phrase and use its timestamp button to seek.",
"Edit a chapter title or note if the automatic result needs correction. Save the edit; use Copy to copy a note.",
"Select Export to download the Markdown brief or chapter-tagged MP3. Open More formats inside the export panel for a timestamped transcript or JSON data."
]),
("h","A.3 If processing fails"),
("p","Read the displayed error. Check that the file has an allowed extension, contains a valid audio track, is at least one second long, and is below the upload limit. Confirm the backend remains running. Use Retry analysis when the uploaded file remains available. If the file itself is incomplete or corrupt, upload a different audio file."),
("h","A.4 Local data locations"),
("table",["Path","Contents"],[
["backend/uploads","Original audio files, stored using generated identifiers."],
["backend/outputs/<podcast_id>","Transcript, Markdown chapters, JSON, and tagged MP3 exports."],
["backend/models","Cached Whisper model weights."],
["backend/podly.db","SQLite database containing episode metadata and analysis records."],
],[2.5,3.7],8.5),
("note","Do not delete a source audio file while an episode still needs playback or reprocessing. Back up the database together with its uploads and outputs.")
])

chapter("Appendix B. API Reference",[
("p","The API is designed for the React client and local testing. The backend exposes OpenAPI documentation at /api/docs when the service is running."),
("table",["Endpoint","Request / parameters","Response / behavior"],[
["POST /api/podcasts/upload","multipart form field file","Creates episode/job; returns IDs."],
["GET /api/podcasts","limit (default 50, maximum 100), offset (default 0)","Newest episode page."],
["GET /api/podcasts/stats","None","Aggregate counts and totals."],
["GET /api/podcasts/{id}","Episode UUID","Episode metadata; transcript is separate."],
["GET /api/podcasts/{id}/transcript","Episode UUID","Ordered transcript segment list."],
["GET /api/podcasts/{id}/chapters","Episode UUID","Ordered chapter list."],
["PATCH /api/podcasts/{id}/chapters/{chapter_id}","Optional title and/or summary fields","Updated chapter record."],
["GET /api/podcasts/{id}/audio","Episode UUID","Original audio stream."],
["GET /api/podcasts/{id}/download/{format}","format in txt, md, json, mp3","Download generated export; completed job required."],
["POST /api/podcasts/{id}/retry","Episode UUID","Requeues eligible failed episode."],
["GET /api/jobs/{job_id}","Job UUID","Stage, progress, message, error, timestamps."],
["GET /api/health","None","Service health payload."],
],[2.6,1.85,1.75],7.8),
("h","B.1 Job status fields"),
("b",[
"id: unique processing job identifier.",
"podcast_id: associated episode identifier.",
"stage: current pipeline stage such as queued, transcribing, or completed.",
"progress: approximate fractional progress from 0 to 1.",
"message: human-readable current operation.",
"error: failure detail when processing fails.",
"created_at and updated_at: job timestamps."
]),
("h","B.2 Error behavior"),
("p","Validation errors return an HTTP client-error response with a detail message. Unknown episodes, jobs, chapters, or files return not found. Download requests are rejected until an episode is completed. Retrying an episode is rejected when it is not failed, its source file is missing, or partial database results remain.")
])

chapter("Appendix C. Data Dictionary",[
("h","C.1 Podcast"),
("table",["Field","Type","Meaning"],[
["id","String / UUID","Primary key."],["job_id","String / UUID","Unique processing job identifier."],
["title","String","Display title derived from the uploaded filename."],["filename","String","Generated stored filename."],
["original_filename","String","Sanitized display filename."],["file_path","String","Local path to the audio source."],
["file_size_bytes","Integer","Uploaded file size."],["duration_seconds","Float","Audio duration when readable."],
["audio_format","String","Extension-derived format label."],["sample_rate","Integer","Source audio sample rate when available."],
["channels","Integer","Number of audio channels when available."],["word_count","Integer","Count of words in returned transcript."],
["topic_count","Integer","Count of assigned non-noise groups in the processing result."],["status","String","pending, processing, completed, or failed."],
["error_message","Text","Processing error suitable for display."],["created_at / completed_at","DateTime","Episode lifecycle timestamps."],
],[1.5,1.3,3.4],8.0),
("h","C.2 ProcessingJob and TranscriptSegment"),
("table",["Entity / field","Type","Meaning"],[
["ProcessingJob.id","String","Primary key."],["ProcessingJob.podcast_id","String / FK","Owning episode."],
["ProcessingJob.stage","String","Current processing stage."],["ProcessingJob.progress","Float","Approximate progress."],
["ProcessingJob.message / error","Text","Status explanation or failure detail."],
["TranscriptSegment.id","String","Primary key."],["TranscriptSegment.podcast_id","String / FK","Owning episode."],
["TranscriptSegment.segment_index","Integer","Stable order within the transcript."],
["TranscriptSegment.start_time / end_time","Float","Segment timestamps in seconds."],
["TranscriptSegment.text","Text","Recognized speech."],
["TranscriptSegment.topic_id / topic_label","Integer / String","Assigned lightweight group and label."],
["TranscriptSegment.confidence","Float, nullable","Reserved field; current pipeline does not persist calibrated confidence."],
],[2.2,1.4,2.6],7.8),
("h","C.3 Chapter"),
("table",["Field","Type","Meaning"],[
["id","String / UUID","Primary key."],["podcast_id","String / FK","Owning episode."],
["chapter_number","Integer","Display order."],["title","String","Generated or user-edited chapter title."],
["start_time / end_time","Float","Chapter interval in seconds."],["topic_id / topic_label","Integer / String","Group assignment and label."],
["topic_keywords","Text","Keyword summary stored as text."],["summary","Text","Short chapter highlight."],
["segment_ids","Text","JSON-encoded list of source segment identifiers."],
["is_edited","Boolean","Indicates a chapter was edited by a user."],
],[1.75,1.35,3.1],8.1)
])

chapter("Appendix D. Test Evidence and Glossary",[
("h","D.1 Evidence notes"),
("p","Frontend validation was performed with the production build and Oxlint. Both commands completed successfully on 28 October 2026. The build runs TypeScript compilation followed by Vite bundling. The backend service test selection covered eight helper/import cases and passed. Python compileall completed. Direct route-function checks against an isolated SQLite test database confirmed the health payload, paged list, aggregate totals, compact episode detail schema, and creation of the segment index."),
("p","The full FastAPI TestClient request suite could not be completed in the restricted environment. The test harness stalled while constructing a local Windows socket pair before it reached the health endpoint. This is recorded as an environment limitation, not as a successful HTTP integration test. The demo episode was separately inspected in the browser."),
("h","D.2 Glossary"),
("table",["Term","Definition in this project"],[
["Automatic Speech Recognition","Conversion of audio speech into text; Whisper performs this role."],
["Chapter","A time-bounded group of transcript segments with a title and a short highlight."],
["Extractive highlight","A summary-like output assembled from selected source sentences rather than newly generated prose."],
["Fast mode","Default pipeline using Tiny Whisper, local section grouping, and extractive highlights."],
["ID3 CHAP frame","MP3 metadata frame describing a chapter and its start/end time."],
["Job polling","Repeated requests by the browser to read processing progress."],
["Transcript segment","Recognized text associated with a start and end time."],
["Voice Activity Detection","Detection of speech-containing regions; Whisper includes related capability, but this app does not expose a dedicated user-facing VAD quality report."],
],[1.7,4.5],8.5),
("h","D.3 Project files of interest"),
("table",["File or folder","Role"],[
["frontend/src/pages/PodcastAnalysis.tsx","Episode brief, chapters, transcript, export tabs."],
["frontend/src/components/Transcript/TranscriptExplorer.tsx","Transcript search and batched rendering."],
["frontend/src/components/Export/ExportPanel.tsx","Primary and advanced download options."],
["backend/app/api/podcasts.py","Upload, listing, details, chapters, streaming, and exports API."],
["backend/app/workers/processing.py","Asynchronous processing pipeline and export generation."],
["backend/app/services/transcription.py","Whisper model cache, FFmpeg compatibility, and transcription settings."],
["backend/app/services/topic_detection.py","Fast section grouping and optional BERTopic path."],
["backend/app/services/summarization.py","Extractive fast highlights and optional model summary path."],
["backend/app/database.py","SQLite engine, schema, relationships, and indexes."],
["backend/app/config.py","Runtime settings and local storage paths."],
],[3.2,3.0],8.2)
])

# Make headings keep together and improve table row rendering.
for p in doc.paragraphs:
    if p.style.name.startswith("Heading"):
        p.paragraph_format.keep_with_next=True
# Core properties
doc.core_properties.title="Podcast Summarisation and Chapter Generator Project Report"
doc.core_properties.subject="Web-Based Application Project Documentation"
doc.core_properties.author="Project Group 17"
doc.core_properties.keywords="Podcast, Summarisation, Chapter Generator, Whisper, FastAPI"

doc.save(DOCX_PATH)
print(f"Created {DOCX_PATH}")
print(f"Abstract words: {abstract_words}")
print(f"Diagram files: {len(list(ASSETS.glob('*.png')))}")


