from ai_tools.main import AI

def update_course(course):
    ai = AI()
    summery = ai.run(course.file, "summerize")
    if summery:
        course.note_content = summery
        course.save()
        print("saved")
