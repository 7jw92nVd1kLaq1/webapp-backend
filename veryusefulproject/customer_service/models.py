from django.db import models
from django.contrib.auth import get_user_model
from veryusefulproject.core.models import BaseModel


User = get_user_model()


# Survey-related models


class CustomerSatisfactionSurveyStatus(BaseModel):
    name = models.CharField(max_length=128)
    desc = models.TextField()


class CustomerSatisfactionSurvey(BaseModel):
    status = models.ForeignKey(CustomerSatisfactionSurveyStatus, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=128)
    desc = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    min_needed_responses = models.PositiveIntegerField()
    max_needed_responses = models.PositiveIntegerField()


class CustomerSatisfactionSurveyResponse(BaseModel):
    survey = models.ForeignKey(CustomerSatisfactionSurvey, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()


class CustomerSatisfactionSurveyQuestionType(BaseModel):
    question_type = models.CharField(max_length=128)
    desc = models.TextField()


class CustomerSatisfactionSurveyQuestion(BaseModel):
    question = models.TextField()
    question_type = models.ForeignKey(CustomerSatisfactionSurveyQuestionType, on_delete=models.SET_NULL, null=True)
    order = models.PositiveIntegerField()


class CustomerSatisfactionSurveyAnswer(BaseModel):
    response = models.ForeignKey(CustomerSatisfactionSurveyResponse, on_delete=models.SET_NULL, null=True)
    question = models.ForeignKey(CustomerSatisfactionSurveyQuestion, on_delete=models.CASCADE)
    answer = models.TextField(default="")


class CustomerSatisfactionSurveyQuestionOption(BaseModel):
    question = models.ForeignKey(CustomerSatisfactionSurveyQuestion, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    value = models.TextField()


class CustomerSatisfactionSurveyAnswerOption(BaseModel):
    answer = models.ForeignKey(CustomerSatisfactionSurveyAnswer, on_delete=models.CASCADE)
    question_option = models.ForeignKey(CustomerSatisfactionSurveyQuestionOption, on_delete=models.CASCADE)

# Inquiry models


class Inquiry(BaseModel):
    email = models.EmailField()
    message = models.TextField()


class InquiryReply(BaseModel):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    inquiry = models.OneToOneField(Inquiry, on_delete=models.CASCADE)
    message = models.TextField()

# Q/A-related models


class QuestionAnswerCategory(BaseModel):
    name = models.CharField(max_length=256)
    desc = models.TextField()


class QuestionAnswer(BaseModel):
    category = models.ForeignKey(QuestionAnswerCategory, on_delete=models.SET_NULL, null=True)
    desc = models.TextField()


class QuestionAnswerQuestion(BaseModel):
    question_answer = models.ForeignKey(QuestionAnswer, on_delete=models.CASCADE)
    question = models.TextField()
    upvote = models.PositiveIntegerField()
    downvote = models.PositiveIntegerField()


class QuestionAnswerAnswer(BaseModel):
    question = models.ForeignKey(QuestionAnswerQuestion, on_delete=models.CASCADE)
    answer = models.TextField()


class QuestionAnswerComment(BaseModel):
    question_answer = models.ForeignKey(QuestionAnswer, on_delete=models.CASCADE)
    comment = models.TextField()
