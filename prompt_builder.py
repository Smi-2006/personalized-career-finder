def build_prompt(student, courses):
    return f"""
A student has the following profile:
Name: {student['name']}
Interests: {student['interests']}
Strengths: {student['strengths']}
Family income: {student['income']}
Location: {student['user_location']}

Available courses:
{', '.join(courses)}

Task:
Recommend 3 suitable courses for this student.

For each course:
- Explain WHY it suits the student's interests and strengths.
- Keep explanation to ONE concise line.
- Format strictly as:
Course Name – Personalized one line explanation.
"""
