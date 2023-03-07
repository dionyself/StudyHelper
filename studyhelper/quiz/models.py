import random
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from model_utils.models import TimeStampedModel




class Tag(TimeStampedModel):
    name = models.TextField(_('Tag Name'), unique=True)
    def __str__(self):
        return self.name

class Course(TimeStampedModel):
    name = models.TextField(_('Course Name'), unique=True)
    tags = models.ManyToManyField(Tag, blank=True)
    provider = models.TextField(_('Provider Name'), unique=True)

    def __str__(self):
        return self.name

class Question(TimeStampedModel):
    ALLOWED_NUMBER_OF_CORRECT_CHOICES = 5
    MAX_CHOICES_TO_OFFER = ALLOWED_NUMBER_OF_CORRECT_CHOICES * 3

    html = models.TextField(_('Question Text'))
    is_published = models.BooleanField(_('Has been published?'), default=False, null=False)
    maximum_marks = models.DecimalField(_('Maximum Marks'), default=4, decimal_places=2, max_digits=6)
    courses = models.ManyToManyField(Course, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.html


class Choice(TimeStampedModel):
    MIN_CHOICES_COUNT = Question.ALLOWED_NUMBER_OF_CORRECT_CHOICES * 3
    MAX_CHOICES_COUNT = MIN_CHOICES_COUNT * 5

    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    is_correct = models.BooleanField(_('Is this answer correct?'), default=False, null=False)
    html = models.TextField(_('Choice Text'))
    reason = models.TextField(_('Choice Reason Text'))

    def __str__(self):
        return self.html


class QuizProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_score = models.DecimalField(_('Total Score'), default=0, decimal_places=2, max_digits=10)
    course = models.ForeignKey(Course, null=True, blank=True, related_name='profiles', on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return f'<QuizProfile: user={self.user}>'

    def get_new_question(self):
        used_questions_pk = AttemptedQuestion.objects.filter(quiz_profile=self).values_list('question__pk', flat=True)
        
        if self.course:
            remaining_questions = self.course.question_set.exclude(pk__in=used_questions_pk)
        elif self.tags.all():
            remaining_questions = Question.objects.filter(tags__in=self.tags.all()).exclude(pk__in=used_questions_pk).distinct()
        else:
            remaining_questions = Question.objects.exclude(pk__in=used_questions_pk)

        if not remaining_questions.exists():
            return
        return random.choice(remaining_questions)

    def create_attempt(self, question):
        attempted_question = AttemptedQuestion(question=question, quiz_profile=self)
        all_choices = list(question.choices.all())
        correct_choices = [cc for cc in all_choices if cc.is_correct]
        incorrect_choices = [ic for ic in all_choices if not ic.is_correct]
        random.shuffle(incorrect_choices)
        randomized_choices = correct_choices
        INCORRECT_CHOICES_TO_OFFER_COUNT = random.choice(list(range(2 if len(correct_choices) < 4 else 0, len(correct_choices)*3 )))
        for _ in range(INCORRECT_CHOICES_TO_OFFER_COUNT):
            incorrect_choice_to_offer = incorrect_choices.pop()
            if incorrect_choice_to_offer:
                randomized_choices.append(incorrect_choice_to_offer)
        shuffed_choices = list(randomized_choices)
        random.shuffle(shuffed_choices)
        attempted_question.offered_choices_order = " ".join([str(choice.pk) for choice in shuffed_choices])
        attempted_question.save()
        attempted_question.offered_choices.set(randomized_choices)
        return shuffed_choices

    def evaluate_attempt(self, attempted_question, selected_choices):
        for selected_choice in selected_choices:
            if attempted_question.question_id != selected_choice.question_id:
                return

        attempted_question.selected_choices.set(list(selected_choices))
        selected_choice_pks = [selected_choice.pk for selected_choice in selected_choices]
        correct_choice_pks = [offered_choice.pk for offered_choice in attempted_question.offered_choices.all() if offered_choice.is_correct]
        incorrect_choice_pks = [offered_choice.pk for offered_choice in attempted_question.offered_choices.all() if not offered_choice.is_correct]
        is_correct = False
        for selected_choice_pk in selected_choice_pks:
            if (selected_choice_pk not in incorrect_choice_pks) and (selected_choice_pk in correct_choice_pks):
                is_correct = True
            else:
                is_correct = False
                break
        if is_correct:
            for should_selected in correct_choice_pks:
                if should_selected not in selected_choice_pks:
                    is_correct = False
                    break

        print(is_correct, selected_choice_pks, incorrect_choice_pks, correct_choice_pks)
        attempted_question.is_correct = is_correct
        if is_correct is True:
            attempted_question.marks_obtained = attempted_question.question.maximum_marks

        attempted_question.save()
        self.update_score()

    def update_score(self):
        marks_sum = self.attempts.filter(is_correct=True).aggregate(
            models.Sum('marks_obtained'))['marks_obtained__sum']
        self.total_score = marks_sum or 0
        self.save()


class AttemptedQuestion(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    quiz_profile = models.ForeignKey(QuizProfile, on_delete=models.CASCADE, related_name='attempts')
    selected_choices = models.ManyToManyField(Choice, blank=True)
    offered_choices = models.ManyToManyField(Choice, related_name="offered_in_attempts", blank=True)
    offered_choices_order = models.TextField(_('Question Text'))
    is_correct = models.BooleanField(_('Was this attempt correct?'), default=False, null=False)
    marks_obtained = models.DecimalField(_('Marks Obtained'), default=0, decimal_places=2, max_digits=6)

    def get_absolute_url(self):
        return f'/submission-result/{self.pk}/'
