import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from .models import QuizProfile, Question, AttemptedQuestion, Course, Tag
from .forms import UserLoginForm, RegistrationForm


def home(request):
    context = {
        'courses': Course.objects.all(),
        'tags': Tag.objects.all(),
    }
    return render(request, 'quiz/home.html', context=context)


@login_required()
def user_home(request):
    context = {
        'courses': Course.objects.all(),
        'tags': Tag.objects.all(),
    }
    return render(request, 'quiz/user_home.html', context=context)


def leaderboard(request):

    top_quiz_profiles = QuizProfile.objects.order_by('-total_score')[:500]
    total_count = top_quiz_profiles.count()
    context = {
        'top_quiz_profiles': top_quiz_profiles,
        'total_count': total_count,
    }
    return render(request, 'quiz/leaderboard.html', context=context)


@login_required()
def play(request):

    quiz_profile, created = QuizProfile.objects.get_or_create(user=request.user)
    course = request.GET.get('course')
    tags = request.GET.getlist('tags')
    paranms = {}
    if course == "0":
        quiz_profile.course = None
        quiz_profile.save()
        if tags:
            if "0" in tags:
                quiz_profile.tags.clear()
            else:
                quiz_profile.tags.clear()
                quiz_profile.tags.set([Tag.objects.get(pk=tag_id) for tag_id in tags])
    elif course:
        quiz_profile.course = Course.objects.get(pk=course)
        quiz_profile.save()
    elif not quiz_profile.course and tags:
        if "0" in tags:
            quiz_profile.tags.clear()
        else:
            quiz_profile.tags.clear()
            quiz_profile.tags.set([Tag.objects.get(pk=tag_id) for tag_id in tags])

    if request.method == 'POST':
        question_pk = request.POST.get('question_pk')

        attempted_question = quiz_profile.attempts.select_related('question').get(question__pk=question_pk)

        choice_pks = request.POST.getlist('choice_pk')

        try:
            selected_choices = attempted_question.question.choices.filter(pk__in=choice_pks)
        except ObjectDoesNotExist:
            raise Http404

        quiz_profile.evaluate_attempt(attempted_question, selected_choices)

        return redirect(attempted_question)

    else:
        question = quiz_profile.get_new_question()
        choices = []
        if question is not None:
            choices = quiz_profile.create_attempt(question)

        context = {
            'question': question,
            'choices': choices, #TODO: Take all correct answers + incorrects
        }

        return render(request, 'quiz/play.html', context=context)

@login_required()
def reset(request):
    quiz_profile, created = QuizProfile.objects.get_or_create(user=request.user)
    quiz_profile.attempts.all().delete()
    quiz_profile.total_score = 0
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
        'offered_pks': offered_pks
    }

    return render(request, 'quiz/submission_result.html', context=context)


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
