from django.db import models

from veryusefulproject.core.models import BaseModel


class ArticleAuthor(BaseModel):
    name = models.TextField()
    desc = models.TextField()


class ArticleCategory(BaseModel):
    name = models.CharField(max_length=256)
    desc = models.TextField()


class Article(BaseModel):
    category = models.ForeignKey(ArticleCategory, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(ArticleAuthor, on_delete=models.SET_NULL, null=True)
    title = models.TextField()


class ArticleParagraph(BaseModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)


class ArticleParagraphPicture(BaseModel):
    paragraphs = models.ManyToManyField(ArticleParagraph)
    order = models.PositiveIntegerField()
    picture = models.ImageField(upload_to="articles/pictures/%Y/%m/%d")
