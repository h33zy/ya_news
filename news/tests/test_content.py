from datetime import datetime, timedelta
from django.utils import timezone

from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import TestCase

from news.models import News, Comment

from yanews.settings import NEWS_COUNT_ON_HOME_PAGE


User = get_user_model()


class TestHomePage(TestCase):
    HOME_URL = reverse('news:home')
    
    @classmethod
    def setUpTestData(cls):
        News.objects.bulk_create(
            News(title=f'Новость {index}', text='Просто текст.', date=datetime.today() - timedelta(days=index))
            for index in range(NEWS_COUNT_ON_HOME_PAGE + 1)
        ) 
    
        
    def test_news_count(self):
        response = self.client.get(self.HOME_URL)
        object_list = response.context['object_list']
        news_count = len(object_list)
        self.assertEqual(news_count, NEWS_COUNT_ON_HOME_PAGE)
        
    def test_news_order(self):
        response = self.client.get(self.HOME_URL)
        object_list = response.context['object_list']
        first_news_date = object_list[0].date
        all_dates = [news.date for news in object_list]
        self.assertEqual(first_news_date, max(all_dates))

 
class TestDetailPage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(title='Новость', text='text')
        cls.detail_url = reverse('news:detail', args=(cls.news.id,))
        cls.author = User.objects.create(username='Petr')
        for index in range(2):
            comment = Comment.objects.create(news=cls.news, author=cls.author, text=f'Текст {index}')
            comment.created = timezone.now() + timedelta(days=index)
            comment.save()
    
    def test_comments_order(self):
        response = self.client.get(self.detail_url)
        # Проверяем, что объект новости находится в словаре контекста
        # под ожидаемым именем - названием модели.
        self.assertIn('news', response.context)
        # Получаем объект новости.
        news = response.context['news']
        # Получаем все комментарии к новости.
        all_comments = news.comment_set.all()
        # Проверяем, что время создания первого комментария в списке
        # меньше, чем время создания второго.
        self.assertLess(all_comments[0].created, all_comments[1].created)
        
    def test_anonymous_client_has_form(self):
        response = self.client.get(self.detail_url)
        self.assertNotIn('form', response.context)
        
    
    def test_authorized_client_has_form(self):
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn('form', response.context)