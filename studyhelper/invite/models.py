import random
from datetime import datetime, timezone
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from model_utils.models import TimeStampedModel
from quiz import models as quiz_models




class AnonymousCourseSession(TimeStampedModel):
    name = models.TextField(_('Anonymous Session name'), default='', null=True, blank=True)
    is_published = models.BooleanField(_('Is this session open?'), default=True, null=False)
    invitations = models.ManyToManyField(AnonymousInvitation, blank=True)
    opens_at = models.DateTimeField()
    closes_at = models.DateTimeField()
    exam_topics = models.ManyToManyField(quiz_models.ExamTopic, blank=True)
    enforce_exam_topics = models.BooleanField(default=False, null=False, blank=True)
    course = models.ForeignKey(quiz_models.Course, null=True, blank=True, on_delete=models.CASCADE)
    tags = models.ManyToManyField(quiz_models.Tag, blank=True)
    max_n_questions = models.IntegerField(blank=True, default=0)
    questions = models.ManyToManyField(quiz_models.Question, blank=True)
    image = models.TextField(_('SVG QR Image'), default='', null=True, blank=True)
    expertise_level = models.CharField(
        max_length=2,
        choices=quiz_models.EXPERTISE_LEVEL_CHOICES,
        default="CO"
    )
    enforce_expertise_level = models.BooleanField(default=False, null=False, blank=True)
    enforce_questions_order = models.BooleanField(default=True, null=False, blank=True)
    session_questions_order = models.TextField(_('Question Text'), default='', null=False, blank=True)

    def get_new_question(self, anonymous_user):
        used_questions_pk = quiz_models.AttemptedQuestion.objects.filter(user=anonymous_user, session=self).values_list('question__pk', flat=True)
        if self.max_n_questions and self.max_n_questions <= len(used_questions_pk):
            session_score, _ = AnonymousSessionScore.objects.get_or_create(course_session=self, user=anonymous_user)
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
            remaining_questions = quiz_models.Question.objects.filter(**expertise_filter).filter(tags__in=self.tags.all()).exclude(pk__in=used_questions_pk).distinct()
        elif self.questions.all():
            remaining_questions = self.questions.exclude(pk__in=used_questions_pk)
            if self.enforce_questions_order and self.session_questions_order:
                for ordered_question in self.session_questions_order.split(","):
                    for unordered in remaining_questions.all():
                        if int(ordered_question) == unordered.id:
                            return unordered
        else:
            remaining_questions = quiz_models.Question.objects.filter(**expertise_filter).exclude(pk__in=used_questions_pk)

        if not remaining_questions.exists():
            session_score, _ = AnonymousSessionScore.objects.get_or_create(course_session=self, user=anonymous_user)
            session_score.is_enabled = False
            session_score.save()
            return

        if not self.enforce_expertise_level:
            expertise_gear=[]
            for exp_filter in expertise_filter["expertise_level__in"]:
                expertise_gear.append(remaining_questions.filter(expertise_level=exp_filter))

            if self.max_n_questions:
                if self.exam_topics.all() and self.enforce_exam_topics:
                    topic_pos_val = self.max_n_questions // len(self.exam_topics.all())
                    topic_index = len(used_questions_pk) // topic_pos_val
                    topic_expertice_pos_val = len(used_questions_pk) % topic_pos_val
                    topic_expertice_pos_index = topic_pos_val // topic_expertice_pos_val
                    if expertise_gear[topic_expertice_pos_index].filter(
                            tags_contains=self.exam_topics.all()[topic_index].tags).exists():
                        return random.choice(expertise_gear[topic_expertice_pos_index].filter(
                            tags_contains=self.exam_topics.all()[topic_index].tags))         
                else:
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
    
    def update_score(self, anonymous_user):
        marks_sum = anonymous_user.attempts.filter(session=self, is_correct=True).aggregate(
            models.Sum('marks_obtained'))['marks_obtained__sum']
        session_score = AnonymousSessionScore.objects.get(user=anonymous_user, course_session=self)
        session_score.total_score = marks_sum or 0
        session_score.save()

    def create_attempt(self, question, anonymous_user):
        attempted_question = AnonymousAttemptedQuestion(question=question, user=anonymous_user, session=self)
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


class AnonymousAttemptedQuestion(TimeStampedModel):
    question = models.ForeignKey(quiz_models.Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    selected_choices = models.ManyToManyField(quiz_models.Choice, blank=True)
    offered_choices = models.ManyToManyField(quiz_models.Choice, related_name="offered_in_anonymous_attempts", blank=True)
    offered_choices_order = models.TextField(_('Question Text'))
    is_correct = models.BooleanField(_('Was this attempt correct?'), default=False, null=False)
    marks_obtained = models.DecimalField(_('Marks Obtained'), default=0, decimal_places=2, max_digits=6)
    session = models.ForeignKey(quiz_models.CourseSession, default=None, null=True, blank=True, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return f'/submission-result/{self.pk}/'


class AnonymousSessionScore(TimeStampedModel):
    course_session = models.ForeignKey(quiz_models.CourseSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_score = models.DecimalField(_('Total Score'), default=0, decimal_places=2, max_digits=10)
    is_enabled = models.BooleanField(_('Is this session avalible for the user?'), default=True, null=False)