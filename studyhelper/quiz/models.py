import random
from datetime import datetime, timezone
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from model_utils.models import TimeStampedModel



EXPERTISE_LEVEL_CHOICES = [
    ('NO', 'Novice'),
    ('AD', 'Advanced Beginner'),
    ('CO', 'Competent'),
    ('PR', 'Proficient'),
    ('EX', 'Expert'),
]


class Tag(TimeStampedModel):
    name = models.TextField(_('Tag Name'), unique=True)
    def __str__(self):
        return self.name


class Course(TimeStampedModel):
    name = models.TextField(_('Course Name'), unique=True)
    tags = models.ManyToManyField(Tag, blank=True)
    provider = models.TextField(_('Provider Name'))
    image = models.TextField(_('SVG QR Image'), default='', null=True, blank=True)
    expertise_level = models.CharField(
        max_length=2,
        choices=EXPERTISE_LEVEL_CHOICES,
        default="CO"
    )
    enforce_expertise_level = models.BooleanField(default=False, null=False, blank=True)

    def __str__(self):
        return self.name


class Question(TimeStampedModel):
    MIN_NUMBER_OF_CORRECT_CHOICES = 1
    MAX_NUMBER_OF_CORRECT_CHOICES = 5
    MAX_CHOICES_TO_OFFER = MAX_NUMBER_OF_CORRECT_CHOICES * 3

    html = models.TextField(_('Question Text'), unique=True)
    is_published = models.BooleanField(_('Has been published?'), default=False, null=False)
    maximum_marks = models.DecimalField(_('Maximum Marks'), default=4, decimal_places=2, max_digits=6)
    courses = models.ManyToManyField(Course, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    image = models.TextField(_('SVG Image'), default='', null=True, blank=True)
    expertise_level = models.CharField(
        max_length=2,
        choices=EXPERTISE_LEVEL_CHOICES,
        default="CO"
    )

    def __str__(self):
        return self.html


class Choice(TimeStampedModel):
    MIN_CHOICES_COUNT = Question.MIN_NUMBER_OF_CORRECT_CHOICES * 3
    MAX_CHOICES_COUNT = Question.MAX_CHOICES_TO_OFFER * 5

    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    is_correct = models.BooleanField(_('Is this answer correct?'), default=False, null=False)
    html = models.TextField(_('Choice Text'))
    image = models.TextField(_('SVG Image'), default='', null=True, blank=True)
    reason = models.TextField(_('Choice Reason Text'), blank=True, default="", null=False)

    def __str__(self):
        return self.html
    
    class Meta:
        unique_together = ('html', 'question',)


class QuizProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_score = models.DecimalField(_('Total Score'), default=0, decimal_places=2, max_digits=10)
    course = models.ForeignKey(Course, null=True, blank=True, related_name='profiles', on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)
    image = models.TextField(_('SVG QR Image'), default='', null=True, blank=True)
    expertise_level = models.CharField(
        max_length=2,
        choices=EXPERTISE_LEVEL_CHOICES,
        default="CO"
    )
    enforce_expertise_level = models.BooleanField(default=False, null=False, blank=True)

    def __str__(self):
        return f'<QuizProfile: user={self.user}>'

    def get_new_question(self):
        used_questions_pk = AttemptedQuestion.objects.filter(quiz_profile=self, session__isnull=True).values_list('question__pk', flat=True)
        
        expertise_filter = {"expertise_level": self.expertise_level}
        expertise_filter_choices = ['NO', 'AD', 'CO', 'PR', 'EX']
        if not self.enforce_expertise_level:
            expertise_filter = {"expertise_level__in": expertise_filter_choices[:expertise_filter_choices.index(self.expertise_level)+1]}
        print(expertise_filter)
        
        if self.course:
            remaining_questions = self.course.question_set.exclude(pk__in=used_questions_pk)
        elif self.tags.all():
            remaining_questions = Question.objects.filter(**expertise_filter).filter(tags__in=self.tags.all()).exclude(pk__in=used_questions_pk).distinct()
        else:
            remaining_questions = Question.objects.filter(**expertise_filter).exclude(pk__in=used_questions_pk)

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
            try:
                incorrect_choice_to_offer = incorrect_choices.pop()
            except:
                break
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

        attempted_question.is_correct = is_correct
        if is_correct is True:
            attempted_question.marks_obtained = attempted_question.question.maximum_marks

        attempted_question.save()
        self.update_score()

    def update_score(self):
        marks_sum = self.attempts.filter(is_correct=True, session__isnull=True).aggregate(
            models.Sum('marks_obtained'))['marks_obtained__sum']
        self.total_score = marks_sum or 0
        self.save()


class CourseSession(TimeStampedModel):
    is_published = models.BooleanField(_('Is this session open?'), default=True, null=False)
    users = models.ManyToManyField(User, blank=True)
    opens_at = models.DateTimeField()
    closes_at = models.DateTimeField()
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)
    max_n_questions = models.IntegerField(blank=True, default=0)
    questions = models.ManyToManyField(Question, blank=True)
    image = models.TextField(_('SVG QR Image'), default='', null=True, blank=True)
    expertise_level = models.CharField(
        max_length=2,
        choices=EXPERTISE_LEVEL_CHOICES,
        default="CO"
    )
    enforce_expertise_level = models.BooleanField(default=False, null=False, blank=True)

    def get_new_question(self, quiz_profile):
        used_questions_pk = AttemptedQuestion.objects.filter(quiz_profile=quiz_profile, session=self).values_list('question__pk', flat=True)
        if self.max_n_questions and self.max_n_questions <= len(used_questions_pk):
            session_score, _ = SessionScore.objects.get_or_create(course_session=self, user=quiz_profile.user)
            session_score.is_enabled = False
            session_score.save()
            return None
        
        expertise_filter = {"expertise_level": self.expertise_level}
        expertise_filter_choices = ['NO', 'AD', 'CO', 'PR', 'EX']
        if not self.enforce_expertise_level:
            expertise_filter = {"expertise_level__in": expertise_filter_choices[:expertise_filter_choices.index(self.expertise_level)+1]}

        if self.course:
            remaining_questions = self.course.question_set.exclude(pk__in=used_questions_pk)
        elif self.tags.all():
            remaining_questions = Question.objects.filter(**expertise_filter).filter(tags__in=self.tags.all()).exclude(pk__in=used_questions_pk).distinct()
        elif self.questions.all():
            remaining_questions = self.questions.exclude(pk__in=used_questions_pk)
        else:
            remaining_questions = Question.objects.filter(**expertise_filter).exclude(pk__in=used_questions_pk)

        if not remaining_questions.exists():
            session_score, _ = SessionScore.objects.get_or_create(course_session=self, user=quiz_profile.user)
            session_score.is_enabled = False
            session_score.save()
            return

        if not self.enforce_expertise_level:
            expertise_gear=[]
            for exp_filter in expertise_filter["expertise_level__in"]:
                expertise_gear.append(remaining_questions.filter(expertise_level=exp_filter))

            if self.max_n_questions:
                position_val = self.max_n_questions // len(expertise_filter["expertise_level__in"])
                position_index = len(used_questions_pk) // position_val
                if expertise_gear[position_index].exists():
                    return random.choice(expertise_gear[position_index])
            else:
                position_val = (self.closes_at - self.opens_at) // len(expertise_filter["expertise_level__in"])
                position_index = (datetime.now(timezone.utc) - self.opens_at) // position_val
                if expertise_gear[position_index].exists():
                    return random.choice(expertise_gear[position_index])

        return random.choice(remaining_questions)
    
    def evaluate_attempt(self, attempted_question, selected_choices, quiz_profile):
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

        attempted_question.is_correct = is_correct
        if is_correct is True:
            attempted_question.marks_obtained = attempted_question.question.maximum_marks

        attempted_question.save()
        self.update_score(quiz_profile)
    
    def update_score(self, quiz_profile):
        marks_sum = quiz_profile.attempts.filter(session=self, is_correct=True).aggregate(
            models.Sum('marks_obtained'))['marks_obtained__sum']
        session_score = SessionScore.objects.get(user=quiz_profile.user, course_session=self)
        session_score.total_score = marks_sum or 0
        session_score.save()

    def create_attempt(self, question, quiz_profile):
        attempted_question = AttemptedQuestion(question=question, quiz_profile=quiz_profile, session=self)
        all_choices = list(question.choices.all())
        correct_choices = [cc for cc in all_choices if cc.is_correct]
        incorrect_choices = [ic for ic in all_choices if not ic.is_correct]
        random.shuffle(incorrect_choices)
        randomized_choices = correct_choices
        INCORRECT_CHOICES_TO_OFFER_COUNT = random.choice(list(range(2 if len(correct_choices) < 4 else 0, len(correct_choices)*3 )))
        for _ in range(INCORRECT_CHOICES_TO_OFFER_COUNT):
            try:
                incorrect_choice_to_offer = incorrect_choices.pop()
            except:
                break
            if incorrect_choice_to_offer:
                randomized_choices.append(incorrect_choice_to_offer)
        shuffed_choices = list(randomized_choices)
        random.shuffle(shuffed_choices)
        attempted_question.offered_choices_order = " ".join([str(choice.pk) for choice in shuffed_choices])
        attempted_question.save()
        attempted_question.offered_choices.set(randomized_choices)
        return shuffed_choices


class AttemptedQuestion(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    quiz_profile = models.ForeignKey(QuizProfile, on_delete=models.CASCADE, related_name='attempts')
    selected_choices = models.ManyToManyField(Choice, blank=True)
    offered_choices = models.ManyToManyField(Choice, related_name="offered_in_attempts", blank=True)
    offered_choices_order = models.TextField(_('Question Text'))
    is_correct = models.BooleanField(_('Was this attempt correct?'), default=False, null=False)
    marks_obtained = models.DecimalField(_('Marks Obtained'), default=0, decimal_places=2, max_digits=6)
    session = models.ForeignKey(CourseSession, default=None, null=True, blank=True, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return f'/submission-result/{self.pk}/'


class SessionScore(TimeStampedModel):
    course_session = models.ForeignKey(CourseSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_score = models.DecimalField(_('Total Score'), default=0, decimal_places=2, max_digits=10)
    is_enabled = models.BooleanField(_('Is this session avalible for the user?'), default=True, null=False)