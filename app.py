import streamlit as st
import openai  # Make sure you have installed openai library
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io
import re

# Load OpenAI API key from Streamlit secrets
client = openai.OpenAI(api_key="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")

def generate_refined_resume(chatgpt_prompt, job_profile):   
    # System content dynamically incorporating job profile
    system_prompt = f"""
    You are a highly skilled resume assistant. Your task is to help users create resumes tailored 
    to specific job descriptions. The job profile provided is: {job_profile}
    Consider the role, responsibilities, and key skills described in the job profile 
    when refining the resume.
    """
    # Call GPT to refine the resume
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chatgpt_prompt},
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        # Extract the generated content
        refined_resume = response.choices[0].message.content
        return refined_resume

    except Exception as e:
        raise RuntimeError(f"Error generating resume: {e}")


def render_markdown_text(text):
    """
    Convert Markdown-like text (**bold**, \n for newlines) to proper HTML-safe text for PDF rendering.
    """
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)  # Convert **bold** to <b>bold</b>
    text = text.replace("\n", "<br/>")  # Replace newline characters with <br/>
    return text

def add_section(title, content_list, content, style, spacer_height=10, title_color=colors.darkblue):
    """
    Add a section to the PDF with a title and content, only if the content_list is not empty.
    """
    if content_list:  # Only add the section if there is content
        content.append(Paragraph(f"<font color='{title_color}'>{title}</font>", style))
        for item in content_list:
            content.append(Paragraph(item, style))
            content.append(Spacer(1, spacer_height))

def generate_resume_with_reportlab(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="Title",
        fontSize=18,
        spaceAfter=10,
        textColor=colors.darkblue,
        alignment=1,  # Center-aligned
    )
    heading_style = ParagraphStyle(
        name="Heading",
        fontSize=14,
        spaceAfter=8,
        textColor=colors.darkblue,
        leading=16,
        alignment=0,  # Left-aligned
    )
    normal_style = ParagraphStyle(
        name="Normal",
        fontSize=11,
        leading=14,
        alignment=0,  # Left-aligned
    )

    content = []

    # Add Title Section
    content.append(Paragraph(f"<b>{data['name']}</b>", title_style))
    content.append(Paragraph(f"<b>{data['job_title']}</b>", title_style))
    content.append(Spacer(1, 12))

    # Add Contact Information in a single line
    if data.get("email") or data.get("phone"):
        contact_info_data = [
            [
                f"E-mail : {data.get('email', '')}",
                f"Phone : {data.get('phone', '')}",
            ]
        ]
        contact_info_table = Table(contact_info_data, colWidths=[200, 160])  # Adjust column widths
        contact_info_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (0, -1), "LEFT"),   # Left-align email
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),  # Right-align phone
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.blue),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        content.append(contact_info_table)
        content.append(Spacer(1, 12))

    # Add Professional Summary
    if data.get("summary"):
        content.append(Paragraph(f"<font color='darkblue'>{render_markdown_text(data['summary'])}</font>", normal_style))
        content.append(Spacer(1, 20))

    # Add Skills
    if data.get("skills"):
        # Add the section title (left-aligned)
        content.append(Paragraph("<font color='darkblue'><b>Skills</b></font>", heading_style))  # Left-aligned title
        content.append(Spacer(1, 10))

        # Prepare data for the table with bold skill names
        skills_data = [[Paragraph(f"<b>{skill}</b>", normal_style), f"{'★' * level}"] for skill, level in data["skills"].items()]

        # Create a table for skills
        skills_table = Table(skills_data, colWidths=[200, 150])  # Adjust column widths
        skills_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),  # Left-align all cells
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),  # Vertically align to middle
            ])
        )

        # Add the table to the content
        content.append(skills_table)
        content.append(Spacer(1, 20))


    # Add Education
    if data.get("education"):
        education = [
            f"{edu['degree']} - <font color='darkblue'>{edu['institution']}</font> ({edu['year']})"
            for edu in data["education"]
        ]
        add_section("Education", education, content, normal_style, title_color=colors.darkblue)

     # Add Hobbies
    if data.get("hobbies"):
        hobbies = [
            f"{hob['hobby']} - <font color='darkblue'>{hob['institution']}</font> ({hob['year']})"
            for hob in data["hobbies"]
        ]
        add_section("Hobby", hobbies, content, normal_style, title_color=colors.darkblue)    

    # Add Work Experience
    if data.get("work_experience"):
        work_exp = []
        for work in data["work_experience"]:
            if work.get("job_title") and work.get("company"):
                # Add job title, company, and duration
                work_exp.append(
                    f"<b>{work['job_title']}</b> at <font color='darkblue'>{work['company']}</font> ({work['duration']})"
                )
            # Add refined job description
            if work.get("description"):
                work_exp.append(render_markdown_text(work["description"]))
        add_section("Work Experience", work_exp, content, normal_style, title_color=colors.darkblue)

    # Add Projects
    if data.get("projects"):
        for project in data["projects"]:
            project_content = []

            # Add refined project description
            if project.get("description"):
                project_content.append(render_markdown_text(project["description"]))

            # Add the project section to content
            add_section(project.get("name", "Project"), project_content, content, normal_style, spacer_height=12)


    # Build the document
    doc.build(content)
    buffer.seek(0)
    return buffer.getvalue()


# Initialize session state for dynamic sections
if "work_experiences" not in st.session_state:
    st.session_state.work_experiences = [{}]
if "educations" not in st.session_state:
    st.session_state.educations = [{}]
if "projects" not in st.session_state:
    st.session_state.projects = [{}]
if "skills" not in st.session_state:
    st.session_state.skills = []
if "hobbies" not in st.session_state:
    st.session_state.hobbies = []
# Function to add a new skill
def add_skill():
    st.session_state.skills.append({"name": "", "score": 5})

# Function to remove a skill
def remove_skill(index):
    st.session_state.skills.pop(index)

# Title of the application
st.title("📄 ResumeAI - Build Your Resume")

# Section: Personal Information
st.header("👤 Personal Information")
name = st.text_input("Full Name", placeholder="Enter your name")
job_title = st.text_input("Target Job Title", placeholder="Enter the job title you're applying for")
email = st.text_input("Email", placeholder="Enter your email")
phone = st.text_input("Phone", placeholder="Enter your phone number")
summary = st.text_area("Professional Summary", placeholder="Write a brief summary about yourself")

# Section: Skills
st.header("💡 Skills")
# Display existing skills dynamically
for i, skill in enumerate(st.session_state.skills):
    cols = st.columns([3, 1, 1])
    with cols[0]:
        st.session_state.skills[i]["name"] = st.text_input(
            f"Skill {i+1} Name", 
            value=skill["name"], 
            key=f"skill_name_{i}"
        )
    with cols[1]:
        st.session_state.skills[i]["score"] = st.slider(
            f"Skill {i+1} Score", 
            min_value=1, 
            max_value=10, 
            value=skill["score"], 
            key=f"skill_score_{i}"
        )
    with cols[2]:
        if st.button("Remove", key=f"remove_skill_{i}"):
            remove_skill(i)
            st.rerun()

# Add Skill Button
if st.button("➕ Add Skill"):
    add_skill()
    st.rerun()

# Section: Job Profile or Job Description
st.header("💼 Job Profile/Description")
job_profile = st.text_area(
    "Job Description or Role",
    placeholder="Enter the details of the job or role you are applying for. You can include responsibilities or expectations mentioned in the JD.",
)

# Section: Education
st.header("🎓 Education")
for i, education in enumerate(st.session_state.educations):
    with st.expander(f"Education {i + 1}", expanded=True):
        degree = st.text_input(
            f"Degree {i + 1}", placeholder="Enter your degree", key=f"edu_degree_{i}"
        )
        institution = st.text_input(
            f"Institution {i + 1}", placeholder="Enter institution name", key=f"edu_institution_{i}"
        )
        year = st.text_input(
            f"Year of Graduation {i + 1}", placeholder="Enter graduation year", key=f"edu_year_{i}"
        )
        st.session_state.educations[i] = {
            "degree": degree,
            "institution": institution,
            "year": year,
        }
    if st.button(f"Remove Education {i + 1}", key=f"remove_edu_{i}"):
        st.session_state.educations.pop(i)
        st.rerun()
if st.button("➕ Add Education"):
    st.session_state.educations.append({})
    st.rerun()



# Section: Hobby
st.header("Hobby")
for i, hobbies in enumerate(st.session_state.hobbies):
    with st.expander(f"Hobby {i + 1}", expanded=True):
        hobby = st.text_input(
            f"Hobby {i + 1}", placeholder="Enter your hobby", key=f"hby_degree_{i}"
        )
       
        st.session_state.hobbies[i] = {
            "Hobby": hobby,
        }
    if st.button(f"Remove Hobby {i + 1}", key=f"remove_hby_{i}"):
        st.session_state.hobbies.pop(i)
        st.rerun()
if st.button("➕ Add Hobby"):
    st.session_state.hobbies.append({})
    st.rerun()



# User Type Selection
user_type = st.radio("Are you a fresher or experienced?", ["Fresher", "Experienced"], horizontal=True)

# Section: Work Experience (only for Experienced users)
if user_type == "Experienced":
    st.header("💼 Work Experience")
    for i, experience in enumerate(st.session_state.work_experiences):
        with st.expander(f"Work Experience {i + 1}", expanded=True):
            job_title = st.text_input(
                f"Job Title {i + 1}", placeholder="Enter job title", key=f"work_job_title_{i}"
            )
            company = st.text_input(
                f"Company {i + 1}", placeholder="Enter company name", key=f"work_company_{i}"
            )
            duration = st.text_input(
                f"Duration {i + 1}", placeholder="e.g., Jan 2020 - Dec 2022", key=f"work_duration_{i}"
            )
            description = st.text_area(
                f"Job Description {i + 1}",
                placeholder="Describe your role and responsibilities",
                key=f"work_description_{i}",
            )
            st.session_state.work_experiences[i] = {
                "job_title": job_title,
                "company": company,
                "duration": duration,
                "description": description,
            }
        if st.button(f"Remove Work Experience {i + 1}", key=f"remove_work_{i}"):
            st.session_state.work_experiences.pop(i)
            st.rerun()
    if st.button("➕ Add Work Experience"):
        st.session_state.work_experiences.append({})
        st.rerun()

# Section: Projects (for all users)
st.header("📂 Projects")
for i, project in enumerate(st.session_state.projects):
    with st.expander(f"Project {i + 1}", expanded=True):
        project_name = st.text_input(
            f"Project Name {i + 1}", placeholder="Enter project name", key=f"proj_name_{i}"
        )
        project_desc = st.text_area(
            f"Project Description {i + 1}",
            placeholder="Describe the project",
            key=f"proj_desc_{i}",
        )
        technologies = st.text_input(
            f"Technologies Used {i + 1}",
            placeholder="List technologies used",
            key=f"proj_tech_{i}",
        )
        link = st.text_input(f"Project Link {i + 1}", placeholder="Enter project link", key=f"proj_link_{i}")
        st.session_state.projects[i] = {
            "name": project_name,
            "description": project_desc,
            "technologies": technologies,
            "link": link,
        }
    if st.button(f"Remove Project {i + 1}", key=f"remove_proj_{i}"):
        st.session_state.projects.pop(i)
        st.rerun()
if st.button("➕ Add Project"):
    st.session_state.projects.append({})
    st.rerun()

if st.button("Generate Resume"):
    resume_data = {
        "name": name,
        "job_title": job_title,
        "email": email,
        "phone": phone,
        "summary": generate_refined_resume(
            "Create the Overall Summary of the resume and make it short, precise and to the point", job_profile
        ),
        "skills": {skill["name"]: skill["score"] for skill in st.session_state.skills if skill["name"]},
        "education": st.session_state.educations,
        "work_experience": [
            {
                "job_title": work.get("job_title", ""),
                "company": work.get("company", ""),
                "duration": work.get("duration", ""),
                "description": generate_refined_resume(
                    f"Refine the job description for the role '{work.get('job_title', '')}' at '{work.get('company', '')}'. "
                    f"Details: {work.get('description', '')} then return overview, Key Responsibilities, Impact and technologies used in points and make it shorter and precise", 
                    job_profile
                ) if work.get("job_title") and work.get("company") else work.get("description", "")
            }
            for work in st.session_state.work_experiences
        ],
        "projects": [
            {
                "name": project.get("name", ""),
                "description": generate_refined_resume(
                    f"Refine the project description for the project '{project.get('name', '')}'. "
                    f"Details: {project.get('description', '')} then return overview, My Contribution, Impact and Tools Used in points and make it shorter and precise", 
                    job_profile
                ) if project.get("name") else project.get("description", ""),
                "technologies": project.get("technologies", ""),
                "link": project.get("link", "")
            }
            for project in st.session_state.projects
        ],
    }
    print(resume_data)
    pdf_content = generate_resume_with_reportlab(resume_data)
    st.download_button(
        "Download Resume",
        data=pdf_content,
        file_name="resume.pdf",
        mime="application/pdf"
    )
