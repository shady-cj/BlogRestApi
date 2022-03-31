from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
import json
from django.db import transaction,IntegrityError


from django.contrib.auth.models import User 
from .models import BlogPost, Comment,Topic, Bookmark
from blogUsers.models import Profile


class TestBlogModel(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='ceejay', email='ceejay@yahoo.com', password='test123')
        self.blog1 = BlogPost.objects.create(
            author = self.user,
            title= 'testing 123',
            content = 'content 1234'

        )
        self.blog2= BlogPost.objects.create(
            author = self.user,
            title= 'testing 1234',
            content = 'content 1234'
        )
    
    def test_blogpost_creation(self):
        qs = BlogPost.objects.all()
        
        self.assertEqual(qs.count(), 2)
    
    def test_comment_feature(self):
        comm = Comment.objects.create(
            author =self.user,
            content = 'testing 123'
        )

        qs = BlogPost.objects.all().first()
        qs.comments_by.add(comm)
        self.assertTrue(qs.comments_by.all().exists())
        self.assertEqual(Comment.objects.all().count(), 1)
        self.assertEqual(BlogPost.objects.first().comments, 1)
    
    def test_like_feature(self):
        qs = BlogPost.objects.all().first()
        qs.liked_by.add(self.user)
        self.assertTrue(qs.liked_by.all().exists)
        self.assertEqual(BlogPost.objects.first().likes,1)

    def test_comment_increment_forward(self):
        qs = BlogPost.objects.all().first()
        comm1 = Comment.objects.create(author= self.user,content = 'comment 1')
        comm2 = Comment.objects.create(author = self.user,content = 'comment 2')
        qs.comments_by.add(comm1,comm2)

        self.assertTrue(qs.comments_by.all().exists())
        self.assertEqual(BlogPost.objects.get(id = qs.id).comments, 2)
    def test_comment_incremet_backward(self):
        qs = BlogPost.objects.all().first()
        qs2 = BlogPost.objects.all().last()
        com = Comment.objects.create(author = self.user, content= 'comment')
        com.blog_comments.add(qs,qs2)
        self.assertEqual(com.blog_comments.all().count(), 2)
        self.assertEqual(BlogPost.objects.get(id = qs.id).comments, 1)
        self.assertEqual(BlogPost.objects.get(id = qs2.id).comments, 1)

    def test_like_increment_forward(self):
        qs = BlogPost.objects.all().first()
        u = User.objects.create(username='henry', email= 'henry@gmail.com', password = 'henry')
        qs.liked_by.add(u, self.user)
        self.assertTrue(qs.liked_by.all().exists())
        self.assertEqual(qs.liked_by.all().count(), BlogPost.objects.get(id = qs.id).likes)

    def test_like_increment_backward(self):
        qs = BlogPost.objects.all().first()
        qs2 = BlogPost.objects.all().last()
        self.user.post_likedBy.add(qs, qs2)

        self.assertTrue(self.user.post_likedBy.all().exists())
        self.assertEqual(self.user.post_likedBy.all().count(), 2)
        self.assertEqual(BlogPost.objects.first().likes, 1)
        self.assertEqual(BlogPost.objects.last().likes, 1)
    
    def test_adding_approved_topic_to_blogposts(self):
        topic = Topic.objects.create(name="Technology", approved=True)
        b= BlogPost.objects.all().first()
        b.blog_topic = topic
        b.save()
        self.assertEqual(Topic.objects.get(name="Technology").topic.all().count(),1)
        self.assertEqual(Topic.objects.get(name="Technology").topic.all().first().id,1)
    def test_increment_view_post(self):
        qs = BlogPost.objects.all().first()
        qs.viewed_by.add(self.user)
        self.assertTrue(qs.viewed_by.all().exists())
        self.assertTrue(BlogPost.objects.get(id = qs.id).views, 1)


class TestBlogRoutes(APITestCase):
    def setUp(self):
        self.client.post(reverse('register'), json.dumps({'first_name':'shady', 'last_name':'Erinfolami',  'password':'shady123', 're_password':'shady123'}), content_type='application/json',HTTP_ACCEPT='application/json')

        self.user = User.objects.get(username = 'shady')
        self.blog1 = BlogPost.objects.create(
            author = self.user,
            title= 'testing 1',
            content = 'content 1',
            published=True

        )
        self.blog2 = BlogPost.objects.create(
            author = self.user,
            title= 'testing 2',
            trashed=True,
            content = 'content 2'

        )
        self.blog3 = BlogPost.objects.create(
            author = self.user,
            title= 'testing 3',
            content = 'content 3',
            published=True
        )
    def authenticate(self):
        respToken = self.client.post('/api/token/', json.dumps({'username':'shady','password':'shady123'}),content_type='application/json')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + respToken.data.get('access'),HTTP_ACCEPT='application/json')
    
    def test_blogposts_list_view_default_no_auth(self):
        
        res = self.client.get('/blogs/feed/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blogposts_list_view_default_with_auth_but_with_unapproved_topics(self):
        # Testing for all posts but all return posts must be a published post and post must not be a trashed post(i.e removed by the author)
        self.authenticate()
        res = self.client.get('/blogs/feed/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Since none of the posts doesn't have approved topics then they shouldn't be returned   
        self.assertEqual(len(res.data.get('results')), 0)
        self.assertNotEqual(len(res.data.get('results')), BlogPost.objects.filter(published=True, trashed=False).count())
    
    def test_blogposts_list_view_default_with_auth_but_with_approved_topics(self):
        # Testing for all posts but all return posts must be a published post and post must not be a trashed post(i.e removed by the author)
        self.authenticate()

        # Creating a topic and adding it to the blog post
        topic = Topic.objects.create(name="Technology", approved=True)
        self.blog1.blog_topic = topic
        self.blog1.save()
        self.blog2.blog_topic = topic
        self.blog2.save()
        self.blog3.blog_topic = topic
        self.blog3.save()
        res = self.client.get('/blogs/feed/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data.get('results'),list)
        # Returns 2 posts since one of the post has been trashed
        self.assertEqual(len(res.data.get('results')), 2)
        self.assertEqual(len(res.data.get('results')), BlogPost.objects.filter(published=True, trashed=False).count())



    def test_blogposts_list_recommended_posts_view_with_auth_and_approved_topic(self):
        # testing for recommended posts but which means the posts must contain a topic the user is interested in or following. 
        self.authenticate()
        topic = Topic.objects.create(name="Technology",approved=True)
        topic2 = Topic.objects.create(name="Political",approved=True)
        self.user.following_topics.add(topic,topic2)
        self.blog1.blog_topic =topic
        self.blog2.blog_topic =topic2
        self.blog3.blog_topic = topic
        self.blog1.save()
        self.blog2.save()
        self.blog3.save()
        res = self.client.get('/blogs/feed/?filter=recommended')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # print(res.data,'filter recommended')
        self.assertIsInstance(res.data.get('results'),list)
        self.assertEqual(len(res.data.get('results')),2)
        self.assertEqual(res.data.get('results')[0].get('title'),'testing 1')
        self.assertEqual(res.data.get('results')[1].get('title'),'testing 3')
    
    def test_blogposts_list_recommended_posts_view_with_auth_and_unapproved_topic(self):
        # testing for recommended posts but which means the posts must contain a topic the user is interested in or following. 
        self.authenticate()
        topic = Topic.objects.create(name="Technology")
        topic2 = Topic.objects.create(name="Political")
        self.user.following_topics.add(topic,topic2)
        self.blog1.blog_topic =topic
        self.blog2.blog_topic =topic2
        self.blog1.save()
        self.blog2.save()
        res = self.client.get('/blogs/feed/?filter=recommended')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotEqual(len(res.data.get('results')),2)
        self.assertEqual(len(res.data.get('results')),0)

    def test_blogposts_list_following_posts_view_with_auth(self):
        # Test for articles created by authors authenticated user is following 
        u = User.objects.create(username='ceejay', email='ceejay@yahoo.com', password='test123')
        # Follow the newly created follower
        u1 = User.objects.get(username='shady')
        Profile.objects.get(user= u1).following.add(u)
        topic2 = Topic.objects.create(name="Political",approved=True)
        post_1 = BlogPost.objects.create(
            author = u,
            title= 'following user article 1',
            content = 'content 1',
            blog_topic = topic2,
            published=True,
            trashed = True

        )
        post_2 = BlogPost.objects.create(
            author = u,
            title= 'following user article 2',
            content = 'content 2',
            blog_topic=topic2,
            published=True

        )
        post_3 = BlogPost.objects.create(
            author = u,
            title= 'following user article 3',
            content = 'content 3',
            published=True
           

        )

        self.authenticate()

        res = self.client.get('/blogs/feed/?filter=following')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data.get('results'),list)
        self.assertEqual(len(res.data.get('results')),1)
        self.assertEqual(res.data.get('results')[0].get('title'),'following user article 2')

    def test_bookmark_lists_with_unapproved_topics(self):
      
        # Since Bookmarks are created immediately a user is created
        b = Bookmark.objects.get(user = self.user)
        # Create an approved topic and assign to blogs instance

    
        # topic = Topic.objects.create(name="Technology", approved=True)
        # self.blog1.blog_topic = topic
        # self.blog1.save()
        # self.blog2.blog_topic = topic
        # self.blog2.save()
        # self.blog3.blog_topic = topic
        # self.blog3.save()
        b.blogPost.add(self.blog1,self.blog2,self.blog3)
        self.assertEqual(self.user.bookmark_user.blogPost.all().count(),3)
        
        self.authenticate()

        res = self.client.get('/blogs/bookmarks/')
         
        # also testing the endpoint when a filter query is given
        res2 = self.client.get('/blogs/bookmarks/?filter=saved')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
       
        self.assertEqual(len(res.data.get('results')[0].get('blogPost')), 3)
        self.assertEqual(len(res2.data.get('results')[0].get('blogPost')), 3)
        


    def test_create_blog_view_with_unapproved_topic(self):
        # this goes ahead to create the topic and add to suggested topic since it hasn't been approved
        post_data = {
            "topic_name":"Sports",
            "title":"TDD",
            "caption":"Test Driven Development",
            "content":"The art of Test Driven Development"
        }

        self.authenticate()
        res = self.client.post(reverse('create-article'), json.dumps(post_data),content_type= 'application/json')
        
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data.get('blog_topic'),None)
        self.assertIsInstance(res.data.get('suggested_topic'),dict)
    
        b = BlogPost.objects.get(title= post_data['title'])
    
        self.assertEqual(b.author.username,'shady')
        self.assertFalse(b.published)
        self.assertEqual(b.blog_topic, None)
        self.assertIsInstance(b.suggested_topic, Topic)

        topic = Topic.objects.get(name= "Sports")
        self.assertFalse(topic.approved)


    def test_create_blog_view_with_approved_topic(self):
        # this goes ahead to create the topic and add to blog topic since it has been approved
        topic = Topic.objects.create(name = "Sports",approved =True)
        post_data = {
            "topic_name":"Sports",
            "title":"TDD",
            "caption":"Test Driven Development",
            "content":"The art of Test Driven Development"
        }

        self.authenticate()
        res = self.client.post(reverse('create-article'), json.dumps(post_data),content_type= 'application/json')
       
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsInstance(res.data.get('blog_topic'),dict)
        self.assertEqual(res.data.get('suggested_topic'),None)

        b = BlogPost.objects.get(title = post_data['title'])
        self.assertEqual(b.author.username,'shady')
        self.assertFalse(b.published)
        self.assertEqual(b.suggested_topic, None)
        self.assertIsInstance(b.blog_topic, Topic)

        topic = Topic.objects.get(name= "Sports")
        self.assertTrue(topic.approved)


    def test_create_blog_view_with_approved_topic_and_published(self):
        # this goes ahead to create the topic and add to blog topic since it has been approved and also publish the post
        topic = Topic.objects.create(name = "Sports",approved =True)
        post_data = {
            "topic_name":"Sports",
            "title":"TDD",
            "caption":"Test Driven Development",
            "content":"The art of Test Driven Development",
            "published":True
        }

        self.authenticate()
        res = self.client.post(reverse('create-article'), json.dumps(post_data),content_type= 'application/json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsInstance(res.data.get('blog_topic'),dict)
        self.assertEqual(res.data.get('suggested_topic'),None)
        b = BlogPost.objects.get(title = post_data['title'])
        self.assertEqual(b.author.username,'shady')
        self.assertEqual(b.published,True)
        self.assertEqual(b.suggested_topic, None)
        self.assertIsInstance(b.blog_topic, Topic)
        
        topic = Topic.objects.get(name= "Sports")
        self.assertTrue(topic.approved)

    
    
    def test_retrieve_blogs_view_for_published_tag_with_authenticated_user_as_the_author(self):
        self.authenticate()
       
        res=self.client.get(reverse('retrieve-update', args= (self.blog1.id,)))
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('title'), self.blog1.title)
        self.assertTrue(res.data.get('published'))
    
    def test_retrieve_blogs_view_for_not_published_post_with_authenticated_user_as_the_author(self):
        blog = BlogPost.objects.create(
            author = self.user,
            title= 'testing 3',
            content = 'content 3',
        )
        self.authenticate()
        res=self.client.get(reverse('retrieve-update', args= (blog.id,)))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('title'), blog.title)
        self.assertFalse(res.data.get('published'))

    def test_retrieve_blogs_view_for_not_published_post_with_authenticated_user_not_the_author(self):
        user = User.objects.create_user(username='ceejay',password='ceejay123')
        blog = BlogPost.objects.create(
            author = user,
            title= 'testing 3',
            content = 'content 3',
        )
        self.authenticate()
        res=self.client.get(reverse('retrieve-update', args= (blog.id,)))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(res.data.get('title'))
        self.assertEqual(res.data.get('error'),"This post is not available" )
    
    def test_retrieve_blogs_view_for_trashed_post_with_authenticated_user_not_the_author(self):
        user = User.objects.create_user(username='ceejay',password='ceejay123')
        blog = BlogPost.objects.create(
            author = user,
            title= 'testing 3',
            content = 'content 3',
            trashed = True
        )
        self.authenticate()
        res=self.client.get(reverse('retrieve-update', args= (blog.id,)))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(res.data.get('title'))
        self.assertEqual(res.data.get('error'),"This post is not available" )
    
    def test_retrieve_blogs_view_for_trashed_post_with_authenticated_user_as_the_author(self):
        blog = BlogPost.objects.create(
            author = self.user,
            title= 'testing 3',
            content = 'content 3',
            trashed = True
        )
        self.authenticate()
        res=self.client.get(reverse('retrieve-update', args= (blog.id,)))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('title'),blog.title)
        self.assertIsNone(res.data.get('error'))
        self.assertEqual(res.data.get('author').get('username'), self.user.username)

    def test_update_blog_view_with_authenticated_user_as_the_author(self):
        self.authenticate()
        update_data = {
            'title':'updated title',
            'content':'updated content'
        }
        res = self.client.put(reverse('retrieve-update', args= (self.blog1.id,)), json.dumps(update_data),content_type='application/json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('title'), update_data['title'])
        self.assertEqual(res.data.get('content'), update_data['content'])
        b = BlogPost.objects.get(id = self.blog1.id)
        self.assertEqual(b.title, update_data['title'])
        self.assertEqual(b.content, update_data['content'])

    def test_update_blog_view_with_authenticated_user_not_the_author(self):
        user = User.objects.create_user(username='ceejay',password='ceejay123')
        blog = BlogPost.objects.create(
            author = user,
            title= 'testing 3',
            content = 'content 3',
            trashed = True
        )
        self.authenticate()
        update_data = {
            'title':'updated title',
            'content':'updated content'
        }
        res = self.client.put(reverse('retrieve-update', args= (blog.id,)), json.dumps(update_data),content_type='application/json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(res.data.get('title'), update_data['title'])
        self.assertIsNone(res.data.get('content'), update_data['content'])
        b = BlogPost.objects.get(id = blog.id)

        self.assertNotEqual(b.title, update_data['title'])
        self.assertNotEqual(b.content, update_data['content'])


    def test_retrieve_blogs_view_for_trashed_post_with_authenticated_user_as_the_author(self):
        blog = BlogPost.objects.create(
            author = self.user,
            title= 'testing 3',
            content = 'content 3',
            trashed = True
        )
        self.authenticate()
        res=self.client.get(reverse('retrieve-update', args= (blog.id,)))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('title'),blog.title)
        self.assertIsNone(res.data.get('error'))
        self.assertEqual(res.data.get('author').get('username'), self.user.username)

    
    def test_update_trashed_blog_view_with_authenticated_user_as_the_author(self):
        self.authenticate()
        update_data = {
            'title':'updated title',
            'content':'updated content'
        }
        res = self.client.put(reverse('retrieve-update', args= (self.blog2.id,)), json.dumps(update_data),content_type='application/json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIsNone(res.data.get('title'))
        self.assertIsNone(res.data.get('content'))
        b = BlogPost.objects.get(id = self.blog2.id)
        self.assertNotEqual(b.title, update_data['title'])
        self.assertNotEqual(b.content, update_data['content'])

    def test_user_Published_story_view(self):
        self.authenticate()
        res = self.client.get(reverse('story', args=('published',)))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data.get('results')), BlogPost.objects.filter(trashed=False,published=True,author = self.user).count())

    def test_user_Drafted_story_view(self):
        self.authenticate()
        res = self.client.get(reverse('story', args=('drafts',)))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data.get('results')), BlogPost.objects.filter(trashed=False,published=False,author = self.user).count())

    def test_user_Trashed_story_view(self):
        self.authenticate()
        res = self.client.get(reverse('story', args=('trash',)))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data.get('results')), BlogPost.objects.filter(trashed=True,author = self.user).count())


    # Testing Actions Liking Posts, Bookmarking ,Commenting, Following, Unfollowing....
    
    def test_post_like_action(self):
        self.authenticate()
        payload = {
            "post_id":self.blog1.id,
            "action":"like"
        }
        res = self.client.post(reverse('activities', args=('like',)), json.dumps(payload), content_type= "application/json")
        self.assertEqual(res.status_code,status.HTTP_200_OK )
        self.assertEqual(res.data.get('message'), 'like successful')
        self.assertEqual(res.data.get('data'), BlogPost.objects.get(id=self.blog1.id).likes)
        self.assertIn(self.user,BlogPost.objects.get(id=self.blog1.id).liked_by.all())

    def test_post_unlike_action(self):
        self.authenticate()
        self.blog1.liked_by.add(self.user)
        payload = {
            "post_id":self.blog1.id,
            "action":"unlike"
        }
        res = self.client.post(reverse('activities', args=('like',)), json.dumps(payload), content_type= "application/json")
        self.assertEqual(res.status_code,status.HTTP_200_OK )
        self.assertEqual(res.data.get('message'), 'unlike successful')
        self.assertEqual(res.data.get('data'), BlogPost.objects.get(id=self.blog1.id).likes)
        self.assertNotIn(self.user,BlogPost.objects.get(id=self.blog1.id).liked_by.all())


    def test_add_post_to_bookmark_action(self):
        self.authenticate()
        data = {
            "post_id":self.blog1.id,
            "action":"add"
        }
        res = self.client.post(reverse('activities', args=('bookmark',)), json.dumps(data), content_type="application/json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('message'), "Article Added To Your Bookmark")
        b = Bookmark.objects.get(user = self.user)
        self.assertIn(self.blog1, b.blogPost.all())
    
    
    def test_remove_post_from_bookmark_action(self):
        self.authenticate()
        b = Bookmark.objects.get(user = self.user)
        b.blogPost.add(self.blog1)
        data = {
            "post_id":self.blog1.id,
            "action":"remove"
        }
        res = self.client.post(reverse('activities', args=('bookmark',)), json.dumps(data), content_type="application/json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('message'), "Article Removed From Your Bookmark")
        b_updated = Bookmark.objects.get(user= self.user)

        self.assertNotIn(self.blog1, b_updated.blogPost.all())
    
    def test_comment_on_post(self):
        self.authenticate()
        initial_comments = self.blog1.comments
        data = {
            "post_id":self.blog1.id,
            "comment":{
                "content":"Nice Article"
            }
        }
        res = self.client.post(reverse('activities', args =('comments',)),json.dumps(data),content_type= "application/json")

        b = BlogPost.objects.get(id = self.blog1.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(b.comments,initial_comments +1)

    def test_following_a_user(self):
        self.authenticate()
        u = User.objects.create(username= "ceejay", password= "ceejay123")
        data = {
            "user_id":u.id,
            "action":"follow"
        }
        res = self.client.post(reverse('activities', args =('follow',)),json.dumps(data),content_type= "application/json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('message'), "Follow Successful")
        
        self.assertIn(Profile.objects.get(user=self.user), u.followers.all())

    def test_unfollowing_a_user(self):
        self.authenticate()
        u = User.objects.create(username= "ceejay", password= "ceejay123")
        p = Profile.objects.get(user= self.user)
        # Following the newly created user
        p.following.add(u)
        data = {
            "user_id":u.id,
            "action":"unfollow"
        }
        res = self.client.post(reverse('activities', args =('follow',)),json.dumps(data),content_type= "application/json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data.get('message'), "Unfollow Successful")

        self.assertNotIn(Profile.objects.get(user=self.user), u.followers.all())
        
