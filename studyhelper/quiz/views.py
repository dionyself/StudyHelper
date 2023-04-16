import json
from datetime import datetime, timezone
from datetime import timedelta
from io import BytesIO
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from .models import QuizProfile, Question, AttemptedQuestion, Course, Tag, Choice, CourseSession, SessionScore
from .forms import UserLoginForm, RegistrationForm
from django.forms.models import model_to_dict
from django.http import FileResponse
from django.contrib.auth.models import User


def home(request):
    context = {
        'questions': Question.objects.all(),
        'users': User.objects.all(),
        'courses': Course.objects.all(),
        'tags': Tag.objects.all(),
    }
    return render(request, 'quiz/home.html', context=context)


@login_required()
def user_home(request):
    context = {
        'questions': Question.objects.all(),
        'users': User.objects.all(),
        'courses': Course.objects.all(),
        'tags': Tag.objects.all(),
    }
    return render(request, 'quiz/user_home.html', context=context)


def leaderboard(request):

    top_quiz_profiles = QuizProfile.objects.order_by('-total_score')[:500]
    total_count = top_quiz_profiles.count()
    session_scores = SessionScore.objects.filter(
            is_enabled=False, course_session__is_published=True).order_by('-total_score')[:500]
    session_total_count = session_scores.count()
    context = {
        'session_scores': session_scores,
        'session_total_count': session_total_count,
        'top_quiz_profiles': top_quiz_profiles,
        'total_count': total_count,
    }
    return render(request, 'quiz/leaderboard.html', context=context)


def course_dict_to_db(course_data):
    course_tags_data = []
    questions_data = []
    questions = []
    course_tags = []
    question_tags = []
    course_tags_data.extend(course_data.pop("tags", []))
    questions_data.extend(course_data.pop("questions", []))
    print(course_data)
    course, created = Course.objects.get_or_create(**course_data)
    print(course.__dict__)
    
    for tag in course_tags_data:
        course_tag, created = Tag.objects.get_or_create(**tag)
        course_tags.append(course_tag)

    course.tags.add(*course_tags)

    for q in questions_data:
        question_tags = []
        for tag in q.pop("tags", []):
            question_tag, created = Tag.objects.get_or_create(**tag)
            question_tags.append(question_tag)
        
        question_choices = []
        tmp_question_choices = q.pop("choices", [])
        question, create = Question.objects.get_or_create(**q)
        for c in tmp_question_choices:
            c["question_id"] = question.id
            question_choice, created = Choice.objects.get_or_create(**c)
            question_choices.append(question_choice)
        question.tags.add(*question_tags)
        question.choices.add(*question_choices)
        questions.append(question)

    course.question_set.add(*questions)
    return course


def import_json_course(course_json_files):
    courses = []
    for raw_course in course_json_files:
        course_data = json.loads(raw_course.read())
        if type(course_data) is list:
            for c in course_data:
                courses.append(course_dict_to_db(c))
        else:
            raise Exception("ERROR: Invalid Data")
    return courses


def course_db_to_dict(course_instance):
    course_data = model_to_dict(course_instance, fields=["name", "tags", "provider", "image", "expertise_level", "enforce_expertise_level"])
    course_data["questions"] = course_instance.question_set.all()
    question_dicts = []
    for question in course_data["questions"]:
        choices = question.choices.all()
        question_dict = model_to_dict(question, fields=["html", "is_published", "image", "maximum_marks", "tags", "expertise_level"])
        question_dict["choices"] = choices
        question_dict["maximum_marks"] = float(question_dict["maximum_marks"])
        question_dicts.append(question_dict)
    course_data["tags"] = [model_to_dict(tag, fields=["name",]) for tag in course_data["tags"]]
    for question in question_dicts:
        question["choices"] = [model_to_dict(choice, fields=["html", "is_correct", "image", "reason"]) for choice in question["choices"]]
        question["tags"] = [model_to_dict(tag, fields=["name",]) for tag in question["tags"]]
    course_data["questions"] = question_dicts
    print(course_data)
    return course_data


def export_json_course(course_id):
    courses = []
    if type(course_id) is list:
        for c in course_id:
            courses.append(course_db_to_dict(Course.objects.get(pk=c)))
    else:
        raise Exception("ERROR: Invalid Data")
    return json.dumps(courses)

@login_required()
def import_export(request):
    
    if request.user.is_superuser:
        if request.method == "GET":
            course_id = request.GET.getlist("course_id")
            if course_id:
                return FileResponse(
                    BytesIO(bytes(export_json_course(course_id), encoding='utf-8')), \
                            as_attachment=True, filename=f"courses.json")
            else:
                context = {
                    'courses': Course.objects.all(),
                    'tags': Tag.objects.all(),
                    'imported_courses': [],
                }
                return render(request, 'quiz/import_export.html', context=context)
        if request.method == "POST":
            course_json_files = request.FILES.getlist("course_file")
            context = {
                'courses': Course.objects.all(),
                'tags': Tag.objects.all(),
                'imported_courses': import_json_course(course_json_files)
            }
            return render(request, 'quiz/import_export.html', context=context)
    else:
        return leaderboard(request)


@login_required()
def play(request):
    quiz_profile, created = QuizProfile.objects.get_or_create(user=request.user)
    active_session = None
    next_session = None
    session_score = None
    try:

        session_score = SessionScore.objects.filter(
            is_enabled=True, course_session__is_published=True,
            course_session__opens_at__lt=datetime.now(timezone.utc), 
            course_session__closes_at__gt=datetime.now(timezone.utc),
            user=request.user).first()
        
        active_session = session_score.course_session
        if request.GET.get("abandone_session") == "1":
            SessionScore.objects.filter(
                is_enabled=True, course_session__is_published=True,
                course_session__opens_at__lt=datetime.now(timezone.utc), 
                course_session__closes_at__gt=datetime.now(timezone.utc),
                user=request.user).update(is_enabled=False)
            active_session = None

    except:
        pass

    if active_session:
        next_session_score = SessionScore.objects.filter(
            is_enabled=True, course_session__is_published=True,
            course_session__opens_at__gt=active_session.closes_at, 
            user=request.user).first()
        if next_session_score:
            next_session = next_session_score.course_session
    else:
        next_session_score = SessionScore.objects.filter(
            is_enabled=True, course_session__is_published=True,
            course_session__opens_at__gt=datetime.now(timezone.utc), 
            user=request.user).first()
        if next_session_score:
            next_session = next_session_score.course_session



    if request.method == 'POST' and request.POST.get('question_pk'):
        question_pk = request.POST.get('question_pk')

        if active_session:
            attempted_question = quiz_profile.attempts.select_related('question').get(session=active_session, question__pk=question_pk)
        else:
            attempted_question = quiz_profile.attempts.select_related('question').get(session__isnull=True, question__pk=question_pk)

        choice_pks = request.POST.getlist('choice_pk')

        try:
            selected_choices = attempted_question.question.choices.filter(pk__in=choice_pks)
        except ObjectDoesNotExist:
            raise Http404
        if active_session:
            active_session.evaluate_attempt(attempted_question, selected_choices, quiz_profile)
        else:
            quiz_profile.evaluate_attempt(attempted_question, selected_choices)

        return redirect(attempted_question)
    else:
        
        course = request.GET.get('course')
        session_course = request.GET.get('session_course')
        tags = request.GET.getlist('tags')

        if course == "0":
            quiz_profile.course = None
            quiz_profile = _reset_profile(quiz_profile)
            quiz_profile.save()
            if tags:
                if "0" in tags:
                    quiz_profile.tags.clear()
                else:
                    quiz_profile.tags.clear()
                    quiz_profile.tags.set([Tag.objects.get(pk=tag_id) for tag_id in tags])
        elif course:
            quiz_profile.course = Course.objects.get(pk=course)
            quiz_profile = _reset_profile(quiz_profile)
            quiz_profile.save()
        elif not quiz_profile.course and tags:
            if "0" in tags:
                quiz_profile.tags.clear()
            else:
                quiz_profile.tags.clear()
                quiz_profile.tags.set([Tag.objects.get(pk=tag_id) for tag_id in tags])
            quiz_profile = _reset_profile(quiz_profile)  

        session_course = request.GET.get('session_course')
        session_course = int(session_course) if session_course else None
        session_expertise_level = request.GET.get('session_expertise_level')
        session_questions = request.GET.getlist('session_questions')
        if (not active_session) and (session_course or session_expertise_level or session_questions):
            session_publish = int(request.GET.get('session_is_published', "0"))
            session_users = request.GET.getlist('session_user')
            session_tags = request.GET.getlist('session_tags')
            if request.GET.get('session_include_me'):
                session_users.append(str(request.user.id))
                session_users = list(set(session_users))
            else:
                session_users.remove(str(request.user.id))
            session_opens_at = datetime.strptime(request.GET.get('session_opens_at'), '%Y-%m-%dT%H:%M')if request.GET.get('session_opens_at') else datetime.now(timezone.utc)
            session_closes_at = datetime.strptime(request.GET.get('session_closes_at'), '%Y-%m-%dT%H:%M') if request.GET.get('session_closes_at') else datetime.now(timezone.utc) + timedelta(minutes=30)
            session_max_n_questions = int(request.GET.get('session_max_n_questions', "0"))
            session_enforce_expertise_level = int(request.GET.get('session_enforce_expertise_level', "0"))
            course_session = CourseSession.objects.create(
                is_published=session_publish, opens_at=session_opens_at, closes_at=session_closes_at,
                course_id=session_course, max_n_questions=session_max_n_questions, expertise_level=session_expertise_level,
                enforce_expertise_level=session_enforce_expertise_level
            )
            course_session.users.add(*[User.objects.get(id=int(u)) for u in session_users])
            course_session.tags.add(*[Tag.objects.get(id=int(t)) for t in session_tags])
            course_session.questions.add(*[Question.objects.get(id=int(cs)) for cs in session_questions])
            course_session.session_questions_order = " ".join([question for question in session_questions])
            course_session.enforce_questions_order = int(request.GET.get('enforce_questions_order', "0"))
            SessionScore.objects.create(course_session=course_session, is_enabled=True, user=quiz_profile.user)
        
        try:
            session_score = SessionScore.objects.filter(
                is_enabled=True, course_session__is_published=True,
                course_session__opens_at__lt=datetime.now(timezone.utc), 
                course_session__closes_at__gt=datetime.now(timezone.utc),
                user=request.user).first()
            active_session = session_score.course_session
        except:
            pass
        
        choices = []
        course_name = "N/A"
        if active_session:
            question = active_session.get_new_question(quiz_profile)
            if question is not None:
                choices = active_session.create_attempt(question, quiz_profile)
            course_name = "N/A" if not active_session.course else active_session.course.name
        else:
            question = quiz_profile.get_new_question()
            if question is not None:
                choices = quiz_profile.create_attempt(question)
            course_name = "N/A" if not quiz_profile.course else quiz_profile.course.name

        context = {
            'course_name': course_name,
            'tag_names': [c_tag.name for c_tag in question.tags.all()] if question else [],
            'question': question,
            'choices': choices,
            'session_score_id': session_score.id if (session_score and not question) else 0,
            'session_duration': (active_session.closes_at - active_session.opens_at) / timedelta(minutes=1) if active_session else "",
            'session_time_left': (active_session.closes_at - datetime.now(timezone.utc)) / timedelta(minutes=1) if active_session else "",
            'session_next': next_session.opens_at if next_session else "",
        }

        return render(request, 'quiz/play.html', context=context)


def _reset_profile(quiz_profile):
    quiz_profile.attempts.filter(session__isnull=True).all().delete()
    quiz_profile.total_score = 0
    return quiz_profile

@login_required()
def reset(request):
    quiz_profile, created = QuizProfile.objects.get_or_create(user=request.user)
    quiz_profile = _reset_profile(quiz_profile)
    quiz_profile.save()
    return redirect('/')


@login_required()
def submission_result(request, attempted_question_pk):
    attempted_question = get_object_or_404(AttemptedQuestion, pk=attempted_question_pk)
    selected_pks = [ selected.id for selected in attempted_question.selected_choices.all() ]
    offered_pks = [int(id) for id in attempted_question.offered_choices_order.split()]
    context = {
        'attempted_question': attempted_question,
        'selected_pks': selected_pks,
        'non_selected_pks': [ non_sec for non_sec in offered_pks if (non_sec not in selected_pks) ],
        'tag_names': [c_tag.name for c_tag in attempted_question.question.tags.all()],
        'course_name': "N/A" if not attempted_question.quiz_profile.course else attempted_question.quiz_profile.course.name,
        'offered_pks': offered_pks
    }

    return render(request, 'quiz/submission_result.html', context=context)

@login_required()
def session_result(request, session_score_id):
    attempted_questions = []
    attempted_questions_rendering = []
    session_score = SessionScore.objects.filter(id=session_score_id, is_enabled=False, course_session__is_published=True).first()
    if session_score:
        attempted_questions = AttemptedQuestion.objects.filter(session=session_score.course_session, quiz_profile__user=session_score.user)
    for attempted_question in attempted_questions:
        selected_pks = [ selected.id for selected in attempted_question.selected_choices.all() ]
        offered_pks = [int(id) for id in attempted_question.offered_choices_order.split()]
        attempted_questions_rendering.append(
            {
                'attempted_question': attempted_question,
                'selected_pks': selected_pks,
                'non_selected_pks': [ non_sec for non_sec in offered_pks if (non_sec not in selected_pks) ],
                'tag_names': [c_tag.name for c_tag in attempted_question.question.tags.all()],
                #'course_name': "N/A" if not attempted_question.quiz_profile.course else attempted_question.quiz_profile.course.name,
                'offered_pks': offered_pks
            }
        )

    context = {
        'attempted_questions': attempted_questions_rendering,
        'session_username': session_score.user.username,
        'session_score': session_score.total_score,
        'session_started_at': session_score.course_session.opens_at,
        'session_closed_at': session_score.course_session.closes_at,
        'course_name': session_score.course_session.course.name if session_score.course_session.course else 'N/A',
        'tag_names': [c_tag.name for c_tag in session_score.course_session.tags.all()],
    }

    return render(request, 'quiz/session_result.html', context=context)

@login_required()
def user_results(request, user_id):
    free_attempts = AttemptedQuestion.objects.filter(session__isnull=True, quiz_profile__user__id=user_id).order_by('-id')[:500]
    user = User.objects.get(pk=user_id)
    return render(
        request,
        'quiz/list_profile_results.html',
        context={
            'free_attempts': free_attempts,
            'total_count': len(free_attempts),
            'username': user.username})

def login_view(request):
    title = "Login"
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('/user-home')
    return render(request, 'quiz/login.html', {"form": form, "title": title})


def register(request):
    title = "Create account"
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/login')
    else:
        form = RegistrationForm()

    context = {'form': form, 'title': title}
    return render(request, 'quiz/registration.html', context=context)


def logout_view(request):
    logout(request)
    return redirect('/')


def error_404(request, exception):
    data = {}
    return render(request, 'quiz/error_404.html', data)


def error_500(request):
    data = {}
    return render(request, 'quiz/error_500.html', data)
