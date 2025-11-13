from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),

    path('features/', views.features_page, name='features'),
    path('pricing/', views.pricing, name='pricing'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('security/', views.security, name='security'),
    path('pricing/', views.pricing, name='pricing'),

    path('auth/', views.auth_page, name='auth_page'),
    path('login/', views.login_user, name='login'),
    path('signup/', views.signup_user, name='signup'),

    
    path('dashboard/', views.dashboard_page, name='dashboard'),
    path('upload/', views.upload_page, name='upload'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('document/<int:doc_id>/view/', views.view_document, name='view_document'),
    path('document/<int:doc_id>/download/', views.download_document, name='download_document'),
]
